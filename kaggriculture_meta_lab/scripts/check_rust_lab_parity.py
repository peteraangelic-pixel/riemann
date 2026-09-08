#!/usr/bin/env python3
"""Parity gate for the integrated LAB backend on repository-native workloads."""
from __future__ import annotations

import gzip
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT))

from kaggriculture_lab import rust_backend  # noqa: E402
from kaggriculture_lab.tournament import _play  # noqa: E402


def bits(value: float) -> bytes:
    return struct.pack(">d", float(value))


def main() -> int:
    b21 = ROOT / "agents/current/agent_v9_b21_s16.py"
    b20 = REPO / "kaggriculture/v10_candidates/opening_rating/agent_v10_b20_s15.py"
    jobs = []
    for seed in (0, 1, 20294000, 20294001):
        for seat in (0, 1):
            jobs.append((seed, str(b21), str(b20), seat, 720, f"static-{seed}-{seat}"))

    corpus = REPO / "kaggriculture/top49_full"
    for replay_path in sorted(corpus.glob("*/replay.json.gz"))[:3]:
        with gzip.open(replay_path, "rt", encoding="utf-8") as stream:
            replay = json.load(stream)
        names = replay["info"]["TeamNames"]
        recorded_seat = 0 if replay["steps"][-1][0].get("reward", 0) > replay["steps"][-1][1].get("reward", 0) else 1
        tape = f"tape:{replay_path}#{recorded_seat}"
        for seat in (0, 1):
            jobs.append((int(replay["info"]["seed"]), str(b21), tape, seat,
                         len(replay["steps"]), f"raw-{replay_path.parent.name}-{seat}"))

    python_rows = [_play(job) for job in jobs]
    rust_rows = rust_backend.run_rust(jobs, workers=4)
    mismatches = []
    for job, python_row, rust_row in zip(jobs, python_rows, rust_rows):
        same = (
            python_row["outcome"] == rust_row["outcome"]
            and bool(python_row["error"]) == bool(rust_row["error"])
            and bits(python_row["self_reward"]) == bits(rust_row["self_reward"])
            and bits(python_row["opp_reward"]) == bits(rust_row["opp_reward"])
        )
        if not same:
            mismatches.append({"job": job, "python": python_row, "rust": rust_row})
    report = {
        "games": len(jobs),
        "static_games": 8,
        "raw_replay_games": len(jobs) - 8,
        "mismatches": mismatches,
    }
    print(json.dumps(report, indent=2, default=str))
    if mismatches:
        return 1
    print("LAB_RUST_PARITY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
