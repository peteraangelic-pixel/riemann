#!/usr/bin/env python3
"""Screen current controls and TOP10 policy-tape exemplars on TOP10/20/30.

The exemplar policies are actions observed for the named team in best-listed
TOP10 submission records. They are emitted as hand-trimming static agents and
are research leads only: a recorded tape is not the original reactive agent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kaggriculture_lab import rust_backend  # noqa: E402
from scripts.benchmark_top30 import _summary, build_top30_jobs  # noqa: E402
from rust_port.tools.agent_tape import emit_source  # noqa: E402

PASS = {"farmer": ["PASS"], "hands": [], "market": []}
CONTROLS = (
    ("control_v7_scripted", ROOT / "agents/current/agent_v7_scripted.py"),
    ("control_v8_aastik", ROOT / "agents/current/agent_v8_aastik.py"),
    ("control_v8_hybrid", ROOT / "agents/current/agent_v8_hybrid.py"),
    ("control_b21_s16", ROOT / "agents/current/agent_v9_b21_s16.py"),
)


def _load(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def _slug(text: str) -> str:
    clean = "".join(c.lower() if c.isascii() and c.isalnum() else "-" for c in text)
    return "-".join(filter(None, clean.split("-"))) or "team"


def make_candidates(corpus: Path, directory: Path) -> list[dict[str, Any]]:
    manifest = _load(corpus / "manifest.json")
    candidates = [{"name": name, "path": path.resolve(), "kind": "control",
                   "source_episode_id": None, "source_team": None}
                  for name, path in CONTROLS]
    seen: dict[str, str] = {}
    for team in manifest["teams"][:10]:
        submission_scores = {int(x["submission_id"]): float(x["public_score"])
                             for x in team["active_submissions"]}
        best = max(submission_scores.values())
        for slot, entry in enumerate(team["selected_episodes"], 1):
            if submission_scores[int(entry["submission_id"])] != best:
                continue
            replay = _load(corpus / team["folder"] / entry["file"])
            seat = replay["info"]["TeamNames"].index(team["team_name"])
            actions = []
            for row in replay["steps"][1:]:
                action = row[seat].get("action") if isinstance(row, list) and len(row) == 2 else None
                actions.append(action if isinstance(action, dict) else PASS)
            while len(actions) < 720:
                actions.append(PASS)
            actions = actions[:720]
            payload = json.dumps(actions, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            fingerprint = hashlib.sha256(payload.encode()).hexdigest()
            if fingerprint in seen:
                continue
            name = f"ex-r{team['rank']:02d}-{_slug(team['team_name'])}-{entry['episode_id']}"
            path = directory / f"{name}.py"
            path.write_text(emit_source([actions, actions], trim_hands=True), encoding="utf-8")
            seen[fingerprint] = name
            candidates.append({
                "name": name,
                "path": path,
                "kind": "top10_best_tape",
                "source_episode_id": int(entry["episode_id"]),
                "source_team": team["team_name"],
                "source_rank": int(team["rank"]),
                "source_slot": slot,
                "source_submission_id": int(entry["submission_id"]),
                "action_fingerprint": fingerprint,
            })
    return candidates


def _safe_summary(rows: list[dict]) -> dict[str, Any] | None:
    return _summary(rows) if rows else None


def candidate_summary(rows: list[dict], source_episode_id: int | None) -> dict[str, Any]:
    if any(row.get("error") or row.get("outcome") == "error" for row in rows):
        raise RuntimeError("candidate has failed games")
    curricula = {}
    for limit in (10, 20, 30):
        current = [row for row in rows if row["rank"] <= limit]
        nonleak = ([row for row in current if row["episode_id"] != source_episode_id]
                   if source_episode_id is not None else current)
        curricula[f"top{limit}"] = {
            "all_recent": _safe_summary(current),
            "best_listed": _safe_summary([row for row in current if row["best_listed_submission"]]),
            "all_recent_source_episode_excluded": _safe_summary(nonleak),
            "best_listed_source_episode_excluded": _safe_summary(
                [row for row in nonleak if row["best_listed_submission"]]),
        }
    per_team = {}
    for team in sorted({row["team"] for row in rows}):
        per_team[team] = _summary([row for row in rows if row["team"] == team])
    return {"curricula": curricula, "per_team": per_team}


def _ranking(results: list[dict], curriculum: str, subset: str) -> list[str]:
    def key(result: dict) -> tuple[float, float]:
        stats = result["summary"]["curricula"][curriculum][subset]
        return (stats["score_rate"], stats["mean_margin"])
    return [result["candidate"]["name"] for result in sorted(results, key=key, reverse=True)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    corpus = args.corpus.resolve()

    # Build target records once. Candidate fields are replaced below; this also
    # validates every target team seat and info.seed before native execution.
    target_jobs, target_metadata = build_top30_jobs(corpus, CONTROLS[-1][1], 30)
    with tempfile.TemporaryDirectory(prefix="kg-top30-exemplars-") as temp:
        candidates = make_candidates(corpus, Path(temp))
        jobs: list[tuple] = []
        metadata: list[dict] = []
        owners: list[int] = []
        for candidate_index, candidate in enumerate(candidates):
            for target, meta in zip(target_jobs, target_metadata):
                seed, _old_candidate, opponent, seat, steps, _tag = target
                jobs.append((seed, str(candidate["path"]), opponent, seat, steps,
                             candidate["name"]))
                metadata.append(meta)
                owners.append(candidate_index)
        print(f"screening {len(candidates)} candidates in {len(jobs)} games")
        native_rows = rust_backend.run_rust(jobs, args.workers)

        grouped: list[list[dict]] = [[] for _ in candidates]
        for row, meta, owner in zip(native_rows, metadata, owners):
            grouped[owner].append({**row, "opponent": meta["replay_file"], **meta})
        results = []
        for candidate, rows in zip(candidates, grouped):
            public_candidate = {k: v for k, v in candidate.items() if k != "path"}
            results.append({
                "candidate": public_candidate,
                "summary": candidate_summary(rows, candidate["source_episode_id"]),
            })

    output = {
        "format": "kaggriculture-top30-exemplar-screen-v1",
        "mode": "open-loop policy tapes; original target seeds; candidate both seats",
        "candidate_count": len(results),
        "game_count": len(jobs),
        "rankings": {
            curriculum: {
                subset: _ranking(results, curriculum, subset)
                for subset in ("all_recent_source_episode_excluded",
                               "best_listed_source_episode_excluded")
            }
            for curriculum in ("top10", "top20", "top30")
        },
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
