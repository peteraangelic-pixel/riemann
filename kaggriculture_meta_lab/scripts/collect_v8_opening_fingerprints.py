#!/usr/bin/env python3
"""Collect exact public post-turn-0 states for fail-closed V8 tail routing."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
from benchmark_top30 import build_top30_jobs  # noqa: E402
from kaggriculture_lab.rust_backend import _source  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--max-rank", type=int, default=30)
    parser.add_argument("--decision-turn", type=int, default=1,
                        help="public observation turn to capture after executing this many actions")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    jobs, metadata = build_top30_jobs(args.corpus.resolve(), args.candidate.resolve(), args.max_rank)
    candidate = _source(str(args.candidate.resolve()))
    if candidate is None:
        raise RuntimeError("candidate is not a static tape")

    rows = []
    with tempfile.TemporaryDirectory(prefix="kg-v8-fingerprints-") as raw:
        temp = Path(raw)
        candidate_path = temp / "candidate.json"
        candidate_path.write_text(json.dumps(candidate.actions), encoding="utf-8")
        exported: dict[str, Path] = {}
        for index, (job, meta) in enumerate(zip(jobs, metadata)):
            seed, _candidate, opponent, candidate_seat, _steps, _tag = job
            if opponent not in exported:
                source = _source(opponent)
                if source is None:
                    raise RuntimeError(f"opponent is not a tape: {opponent}")
                path = temp / f"opponent-{len(exported)}.json"
                path.write_text(json.dumps(source.actions), encoding="utf-8")
                exported[opponent] = path
            trace = temp / f"trace-{index}.jsonl"
            command = [
                str(args.binary.resolve()), "--tape-a", str(candidate_path),
                "--tape-b", str(exported[opponent]), "--seed", str(seed),
                "--steps", str(args.decision_turn), "--step-mode", "turns", "--trim-hands-a",
                "--trace", str(trace),
            ]
            if candidate_seat == 1:
                command.append("--reverse-seats")
            result = subprocess.run(command, text=True, capture_output=True)
            if result.returncode:
                raise RuntimeError(f"trace failed: {result.stdout} {result.stderr}")
            states = [json.loads(line) for line in trace.read_text().splitlines()]
            if len(states) != args.decision_turn + 1 or states[-1].get("step") != args.decision_turn:
                raise RuntimeError(f"unexpected trace horizon: {len(states)}")
            state = states[-1]
            own = state["farms"][candidate_seat]
            opp = state["farms"][1 - candidate_seat]
            def tile_counts(farm):
                counts = {}
                for row in farm.get("tiles", []):
                    for tile in row:
                        if isinstance(tile, dict):
                            key = str(tile.get("animal") or tile.get("crop") or tile.get("kind") or "OTHER")
                            counts[key] = counts.get(key, 0) + 1
                return counts
            rows.append({
                **meta,
                "seed": seed,
                "candidate_seat": candidate_seat,
                "own_money": own["money"],
                "opponent_money": opp["money"],
                "own_hands": len(own["hands"]),
                "opponent_hands": len(opp["hands"]),
                "own_unlocked": len(own.get("unlocked_quadrants", [])),
                "opponent_unlocked": len(opp.get("unlocked_quadrants", [])),
                "own_tiles": tile_counts(own),
                "opponent_tiles": tile_counts(opp),
                "market_inventory": state["market"]["inventory"],
                "market_prices": state["market"]["prices"],
            })

    result = {
        "format": "v8-public-route-fingerprints-v2",
        "mode": "candidate versus every selected replay policy, both physical seats",
        "decision_turn": args.decision_turn,
        "candidate": str(args.candidate),
        "policies": len(rows) // 2,
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"policies": result["policies"], "rows": len(rows),
                      "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
