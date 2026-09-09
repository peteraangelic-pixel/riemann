#!/usr/bin/env python3
"""Generation-0 Rust screen of market overlays on the static Subin unit tape."""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "rust_port/tools"))

from kaggriculture_lab.rust_backend import _source  # noqa: E402
from rust_client import Job, replay_many  # noqa: E402
from scripts.benchmark_corpus import build_top30_jobs  # noqa: E402
from scripts.generate_market_overlays import (  # noqa: E402
    BOUNDS, LOCAL_OPTIONS, generate_local_profiles, generate_profiles,
    generate_refined_profiles,
)

SOURCE_EPISODE = 106845775


def wilson(wins: int, losses: int, ties: int) -> tuple[float, float]:
    n = wins + losses + ties
    if not n:
        return (0.0, 0.0)
    p = (wins + 0.5 * ties) / n
    z = 1.959963984540054
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def summarize(rows: list[tuple[dict, dict]]) -> dict:
    if any(result.get("errors") or result.get("rewards") is None for result, _ in rows):
        raise RuntimeError("profile has failed games; refusing to rank it")
    wins = losses = ties = 0
    margins: list[float] = []
    teams: dict[str, list[float]] = defaultdict(list)
    for result, meta in rows:
        a, b = map(float, result["rewards"])
        score = 1.0 if a > b else 0.0 if a < b else 0.5
        wins += score == 1.0
        losses += score == 0.0
        ties += score == 0.5
        margins.append(a - b)
        teams[meta["team"]].append(score)
    low, high = wilson(wins, losses, ties)
    return {
        "games": len(rows), "wins": wins, "losses": losses, "ties": ties,
        "score_rate": (wins + 0.5 * ties) / len(rows),
        "team_balanced_score": statistics.mean(statistics.mean(v) for v in teams.values()),
        "wilson_95": [low, high], "mean_margin": statistics.mean(margins),
        "worst_team_score": min(statistics.mean(v) for v in teams.values()),
        "teams": len(teams),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--candidate", type=Path,
                    default=ROOT / "agents/variants/agent_v10_subin_106845775.py")
    ap.add_argument("--binary", type=Path,
                    default=ROOT / "rust_port/target/release/kg_sim")
    ap.add_argument("--population", type=int, default=1000)
    ap.add_argument("--generation", choices=("g0", "g1", "g2"), default="g0")
    ap.add_argument("--profiles-from", type=Path,
                    help="validate retained_top10 from an earlier result instead of sampling")
    ap.add_argument("--max-rank", type=int, choices=(5, 10, 15, 20, 30), default=10)
    ap.add_argument("--seed", type=int, default=20260909)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    if args.profiles_from:
        previous = json.loads(args.profiles_from.read_text(encoding="utf-8"))
        profiles = [{"enabled": False}]
        for entry in previous["retained_top10"]:
            if entry["profile"] not in profiles:
                profiles.append(entry["profile"])
        generation = "validation"
    else:
        if args.generation == "g2":
            profiles = generate_refined_profiles()
        elif args.generation == "g1":
            profiles = generate_local_profiles(args.population, args.seed)
        else:
            profiles = generate_profiles(args.population, args.seed)
        generation = args.generation
    target_jobs, target_meta = build_top30_jobs(
        args.corpus.resolve(), args.candidate, args.max_rank)
    selected = [(job, meta) for job, meta in zip(target_jobs, target_meta)
                if meta["best_listed_submission"] and meta["episode_id"] != SOURCE_EPISODE]
    if not selected:
        raise SystemExit("no non-source TOP10 best-listed targets")

    candidate_source = _source(str(args.candidate.resolve()))
    if candidate_source is None:
        raise SystemExit("candidate is not compilable as a static tape")
    opponent_sources = {}
    for job, _ in selected:
        opponent_sources.setdefault(job[2], _source(job[2]))
    if any(source is None for source in opponent_sources.values()):
        raise SystemExit("a target did not compile as a raw tape")

    with tempfile.TemporaryDirectory(prefix="kg-overlay-screen-") as raw_temp:
        temp = Path(raw_temp)
        candidate_tape = temp / "candidate.json"
        candidate_tape.write_text(json.dumps(candidate_source.actions), encoding="utf-8")
        opponent_paths = {}
        for i, (spec, source) in enumerate(opponent_sources.items()):
            path = temp / f"opponent-{i}.json"
            path.write_text(json.dumps(source.actions), encoding="utf-8")
            opponent_paths[spec] = path
        profile_paths = []
        for i, profile in enumerate(profiles):
            path = temp / f"profile-{i}.json"
            path.write_text(json.dumps(profile), encoding="utf-8")
            profile_paths.append(path)

        jobs: list[Job] = []
        owners: list[int] = []
        metadata: list[dict] = []
        for owner, profile_path in enumerate(profile_paths):
            for job, meta in selected:
                seed, _candidate, opponent, seat, _steps, _tag = job
                jobs.append(Job(seed, candidate_tape, opponent_paths[opponent],
                                reverse=seat == 1, overlay_a=profile_path))
                owners.append(owner)
                metadata.append(meta)
        print(f"screening {len(profiles)} profiles in {len(jobs)} games "
              f"against {len(selected) // 2} non-source records, both seats")
        native = replay_many(jobs, binary=args.binary, threads=args.workers,
                             steps=720, trim_hands_a=candidate_source.trim_hands,
                             allow_errors=True, timeout=540)

    grouped: list[list[tuple[dict, dict]]] = [[] for _ in profiles]
    for result, meta, owner in zip(native, metadata, owners):
        grouped[owner].append((result, meta))
    entries = []
    for index, (profile, rows) in enumerate(zip(profiles, grouped)):
        stats = summarize(rows)
        curricula = {
            f"top{limit}": summarize([
                row for row in rows if row[1]["rank"] <= limit
            ])
            for limit in (10, 20, 30) if limit <= args.max_rank
        }
        entries.append({"index": index, "name": f"market-{generation}-{index:05d}",
                        "profile": profile, "summary": stats, "curricula": curricula})
    if not args.profiles_from and args.generation in {"g1", "g2"}:
        control = entries[0]["summary"]
        identity = entries[1]["summary"]
        contract = ("wins", "losses", "ties", "mean_margin", "team_balanced_score")
        if any(identity[key] != control[key] for key in contract):
            raise RuntimeError("enabled identity profile diverged from disabled control")
    entries.sort(key=lambda e: (
        e["summary"]["team_balanced_score"], e["summary"]["wilson_95"][0],
        e["summary"]["mean_margin"]), reverse=True)
    baseline = next(e for e in entries if e["index"] == 0)
    output = {
        "format": "kaggriculture-market-overlay-screen-v1",
        "mode": (f"TOP{args.max_rank} best-listed raw tapes; source episode excluded; "
                 "both seats"),
        "generation": generation, "max_rank": args.max_rank,
        "population": len(profiles), "games": len(jobs), "generation_seed": args.seed,
        "search_space": (
            "retained_top10" if args.profiles_from else
            "refined start/cash/wheat-price/milk-reserve grid"
            if args.generation == "g2" else
            LOCAL_OPTIONS if args.generation == "g1" else BOUNDS
        ),
        "baseline": baseline, "retained_top10": entries[:10],
        "top50": entries[:50],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(f"baseline score={baseline['summary']['score_rate']:.3f}; "
          f"winner={entries[0]['name']} score={entries[0]['summary']['score_rate']:.3f}")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
