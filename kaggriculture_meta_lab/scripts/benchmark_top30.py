#!/usr/bin/env python3
"""Bounded evaluation against an audited TOP30 or per-team TOP15 corpus.

Each selected team's recorded policy tape is replayed under its original seed,
with the candidate tested in both physical seats. This is an open-loop replay
stress test, not a closed-loop reconstruction of the leaderboard.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kaggriculture_lab import rust_backend  # noqa: E402
from kaggriculture_lab.stats import aggregate  # noqa: E402


def _load(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def _manifest_sha(path: Path) -> str:
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    if (path / "manifest.json").is_file():
        return hashlib.sha256((path / "manifest.json").read_bytes()).hexdigest()
    manifests = sorted(path.glob("*/manifest.json"))
    digest = hashlib.sha256()
    for manifest in manifests:
        digest.update(manifest.relative_to(path).as_posix().encode())
        digest.update(manifest.read_bytes())
    return digest.hexdigest()


def load_corpus_manifest(corpus: Path) -> dict[str, Any]:
    """Load legacy aggregate TOP30 or the current per-team TOP15 layout."""
    aggregate = corpus / "manifest.json"
    if aggregate.is_file():
        manifest = _load(aggregate)
    else:
        teams = [_load(path) for path in sorted(corpus.glob("*/manifest.json"))]
        if not teams:
            raise ValueError("corpus has neither aggregate nor per-team manifests")
        teams.sort(key=lambda team: int(team["rank"]))
        manifest = {"competition": "kaggriculture", "teams": teams}
    teams = manifest.get("teams")
    if manifest.get("competition") != "kaggriculture" or not isinstance(teams, list):
        raise ValueError("not a Kaggriculture replay corpus manifest")
    ranks = [int(team["rank"]) for team in teams]
    if len(ranks) != len(set(ranks)):
        raise ValueError("duplicate team rank in corpus manifests")
    return manifest


def build_top30_jobs(corpus: Path, candidate: Path, max_rank: int = 30) -> tuple[list[tuple], list[dict]]:
    manifest = load_corpus_manifest(corpus)
    teams = manifest["teams"]
    jobs: list[tuple] = []
    metadata: list[dict] = []
    for team in teams:
        rank = int(team["rank"])
        if rank > max_rank:
            continue
        submissions = {int(x["submission_id"]): float(x["public_score"])
                       for x in team["active_submissions"]}
        best_score = max(submissions.values())
        for slot, entry in enumerate(team["selected_episodes"], 1):
            replay_path = corpus / team["folder"] / entry["file"]
            replay = _load(replay_path)
            if replay.get("info", {}).get("EpisodeId") != entry["episode_id"]:
                raise ValueError(f"episode mismatch: {replay_path}")
            names = replay.get("info", {}).get("TeamNames")
            seats = [i for i, name in enumerate(names or []) if name == team["team_name"]]
            if len(seats) == 1:
                recorded_seat = seats[0]
            elif seats == [0, 1]:
                # In a genuine leaderboard self-play both recorded tapes belong
                # to this team. Select seat zero deterministically.
                recorded_seat = 0
            else:
                raise ValueError(f"cannot identify team seat in {replay_path}: {names}")
            seed = replay.get("info", {}).get("seed")
            if not isinstance(seed, int) or isinstance(seed, bool):
                raise ValueError(f"missing integer replay seed: {replay_path}")
            submission_id = int(entry["submission_id"])
            source_score = submissions.get(submission_id)
            if source_score is None:
                raise ValueError(f"selected submission absent from active list: {replay_path}")
            opponent = f"tape:{replay_path.resolve()}#{recorded_seat}"
            common = {
                "rank": rank,
                "team": team["team_name"],
                "slot": slot,
                "episode_id": int(entry["episode_id"]),
                "submission_id": submission_id,
                "submission_public_score": source_score,
                "best_listed_public_score": best_score,
                "best_listed_submission": source_score == best_score,
                "recorded_team_seat": recorded_seat,
                "recorded_self_play": seats == [0, 1],
                "replay_file": replay_path.relative_to(corpus).as_posix(),
            }
            for candidate_seat in (0, 1):
                jobs.append((seed, str(candidate.resolve()), opponent, candidate_seat, 720,
                             f"rank{rank:02d}"))
                metadata.append({**common, "candidate_seat": candidate_seat})
    return jobs, metadata


def _summary(rows: list[dict]) -> dict[str, Any]:
    agg = aggregate(rows)
    by_seat = {}
    for seat in (0, 1):
        selected = [row for row in rows if row["candidate_seat"] == seat]
        seat_agg = aggregate(selected)
        by_seat[str(seat)] = {
            "games": seat_agg.games,
            "wins": seat_agg.wins,
            "losses": seat_agg.losses,
            "ties": seat_agg.ties,
            "score_rate": seat_agg.score_rate,
            "mean_margin": seat_agg.mean_margin,
        }
    return {
        "games": agg.games,
        "wins": agg.wins,
        "losses": agg.losses,
        "ties": agg.ties,
        "errors": agg.errors,
        "score_rate": agg.score_rate,
        "wilson_95": [agg.ci_low, agg.ci_high],
        "mean_margin": agg.mean_margin,
        "mean_candidate_reward": statistics.mean(row["self_reward"] for row in rows),
        "mean_tape_reward": statistics.mean(row["opp_reward"] for row in rows),
        "by_candidate_seat": by_seat,
    }


def summarize(rows: list[dict]) -> dict[str, Any]:
    if any(row.get("error") or row.get("outcome") == "error" for row in rows):
        failures = [row for row in rows if row.get("error") or row.get("outcome") == "error"]
        raise RuntimeError(f"refusing to summarize {len(failures)} failed games")
    out: dict[str, Any] = {}
    maximum = max(row["rank"] for row in rows)
    limits = [limit for limit in (10, 20, 30) if limit <= maximum]
    if maximum not in limits:
        limits.append(maximum)
    for limit in sorted(set(limits)):
        recent = [row for row in rows if row["rank"] <= limit]
        best = [row for row in recent if row["best_listed_submission"]]
        out[f"top{limit}"] = {
            "all_recent_selected": _summary(recent),
            "best_listed_submission_only": _summary(best),
            "best_subset_teams_covered": len({row["team"] for row in best}),
            "all_teams_covered": len({row["team"] for row in recent}),
        }
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True,
                        help="extracted aggregate TOP30 or per-team TOP15 directory")
    parser.add_argument("--candidate", type=Path,
                        default=ROOT / "agents/current/agent_v9_b21_s16.py")
    parser.add_argument("--candidate-overlay", type=Path,
                        help="Rust overlay JSON applied to the candidate tape")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--max-rank", type=int, choices=range(1, 31), default=30)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    jobs, metadata = build_top30_jobs(args.corpus.resolve(), args.candidate.resolve(), args.max_rank)
    print(f"planned {len(jobs)} games from {len(jobs) // 2} team-policy records, both seats")
    if args.dry_run:
        print(f"best-listed-submission games: {sum(2 for m in metadata[::2] if m['best_listed_submission'])}")
        return 0
    rows = rust_backend.run_rust(jobs, args.workers,
                                 candidate_overlay=args.candidate_overlay)
    enriched = [{**row, "opponent": meta["replay_file"], **meta}
                for row, meta in zip(rows, metadata)]
    try:
        candidate_label = args.candidate.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        candidate_label = str(args.candidate.resolve())
    summary_error = None
    try:
        summary = summarize(enriched)
    except RuntimeError as error:
        # Preserve every raw row for diagnosis while still returning failure.
        # A failed game is never converted into a normal score or ranking.
        summary, summary_error = {}, str(error)
    result = {
        "format": "kaggriculture-replay-corpus-benchmark-v2",
        "mode": "open-loop recorded team policy; original seed; candidate both seats",
        "candidate": candidate_label,
        "candidate_overlay": (json.loads(args.candidate_overlay.read_text(encoding="utf-8"))
                              if args.candidate_overlay else None),
        "source_manifest_sha256": _manifest_sha(args.corpus),
        "summary": summary,
        "summary_error": summary_error,
        "rows": enriched,
    }
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        print(rendered)
    if summary_error:
        print(f"ERROR: {summary_error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
