#!/usr/bin/env python3
"""Fast paired tournament for conservatively compiled static tapes.

This is the no-Rust fallback for large static diagnostics.  Unlike ad-hoc tape
loaders it uses ``rust_backend._source`` and therefore rejects reactive agents
such as G2/G4 instead of silently dropping their overlays.  Promotion evidence
against those agents must still use ``run_tournament.py``.
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "rust_port" / "tools")]

from kaggriculture_lab.rust_backend import _source  # noqa: E402
from py_reference import PythonReplay  # noqa: E402

_A = _B = None
_TRIM_A = _TRIM_B = False
_STEPS = 720


def _init(a, b, trim_a: bool, trim_b: bool, steps: int) -> None:
    global _A, _B, _TRIM_A, _TRIM_B, _STEPS
    _A, _B, _TRIM_A, _TRIM_B, _STEPS = a, b, trim_a, trim_b, steps


def _game(job: tuple[int, int]) -> dict:
    seed, seat = job
    replay = PythonReplay(_A, _B, seed, steps=_STEPS, reverse=bool(seat),
                          trim_hands_a=_TRIM_A, trim_hands_b=_TRIM_B)
    rewards = replay.run()
    statuses = [state.status for state in replay.state]
    error = None if all(s in {"ACTIVE", "DONE"} for s in statuses) else f"statuses={statuses}"
    return {"seed": seed, "seat": seat, "self_reward": rewards[0],
            "opp_reward": rewards[1], "margin": rewards[0] - rewards[1], "error": error}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--opponent", type=Path, required=True)
    parser.add_argument("--start-seed", type=int, default=100)
    parser.add_argument("--games", type=int, default=32, help="unique seeds; both seats are run")
    parser.add_argument("--workers", type=int, default=max(1, mp.cpu_count() or 1))
    parser.add_argument("--steps", type=int, default=720)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.games < 1 or args.workers < 1:
        parser.error("games and workers must be positive")
    candidate = _source(str(args.candidate.resolve()))
    opponent = _source(str(args.opponent.resolve()))
    if candidate is None or opponent is None:
        raise SystemExit("both agents must match an audited static-tape template; reactive overlays are rejected")
    jobs = [(seed, seat) for seed in range(args.start_seed, args.start_seed + args.games)
            for seat in (0, 1)]
    started = time.perf_counter()
    with mp.Pool(args.workers, initializer=_init,
                 initargs=(candidate.actions, opponent.actions, candidate.trim_hands,
                           opponent.trim_hands, args.steps)) as pool:
        rows = pool.map(_game, jobs)
    elapsed = time.perf_counter() - started
    errors = [row for row in rows if row["error"]]
    wins = sum(row["margin"] > 0 for row in rows if not row["error"])
    losses = sum(row["margin"] < 0 for row in rows if not row["error"])
    ties = sum(row["margin"] == 0 for row in rows if not row["error"])
    summary = {"candidate": str(args.candidate), "opponent": str(args.opponent),
               "games": len(rows), "wins": wins, "losses": losses, "ties": ties,
               "errors": len(errors), "mean_margin": sum(r["margin"] for r in rows) / len(rows),
               "elapsed_seconds": elapsed, "games_per_second": len(rows) / elapsed,
               "rows": rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"{wins}-{losses}-{ties}, errors={len(errors)}, margin={summary['mean_margin']:.1f}, "
          f"{summary['games_per_second']:.1f} games/s")
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
