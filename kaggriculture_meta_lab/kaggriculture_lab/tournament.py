"""Closed-loop, process-parallel, paired-seed tournament.

This is the evaluator V7 was missing: two *real* policies react to each other on
the same seeds, from both seats, in parallel. Unlike open-loop replay tapes,
this honestly estimates adaptive win rate - which is what the final
Bradley-Terry ranking rewards.

Design:
  * worker processes (not threads) -> no GIL bottleneck;
  * agents resolved once per worker and cached;
  * paired seeds: for every seed the candidate plays BOTH seats against the same
    opponent on the same RNG, so seat/map effects cancel;
  * one crashed game -> an error row, never a dead batch;
  * Wilson CI + promotion gate decide keep/reject.
"""
from __future__ import annotations

import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _worker_init() -> None:
    if _ROOT not in sys.path:
        sys.path.insert(0, _ROOT)


def _play(job: tuple) -> dict[str, Any]:
    seed, cand_spec, opp_spec, seat, steps, tag = job
    from kaggriculture_lab.agents import resolve
    from kaggriculture_lab.engine import play_game

    try:
        cand = resolve(cand_spec)
        opp = resolve(opp_spec)
        a0, a1 = (cand, opp) if seat == 0 else (opp, cand)
        res = play_game(a0, a1, seed=seed, steps=steps)
        if res.get("error"):
            return {"tag": tag, "seed": seed, "seat": seat, "opponent": opp_spec,
                    "self_reward": 0.0, "opp_reward": 0.0, "margin": 0.0,
                    "outcome": "error", "error": res["error"]}
        rewards = res["rewards"]
        self_r = rewards[seat]
        opp_r = rewards[1 - seat]
        return {"tag": tag, "seed": seed, "seat": seat, "opponent": opp_spec,
                "self_reward": self_r, "opp_reward": opp_r,
                "margin": self_r - opp_r,
                "outcome": "win" if self_r > opp_r else "loss" if self_r < opp_r else "tie",
                "error": None}
    except Exception as exc:  # resolution errors etc.
        return {"tag": tag, "seed": seed, "seat": seat, "opponent": opp_spec,
                "self_reward": 0.0, "opp_reward": 0.0, "margin": 0.0,
                "outcome": "error", "error": f"{type(exc).__name__}: {exc}"}


@dataclass
class Matchup:
    candidate: str
    opponent: str


def build_jobs(candidate: str, opponents: list[str], games: int, start_seed: int,
               swap_seats: bool = True, steps: int = 720, tag: str | None = None) -> list[tuple]:
    jobs: list[tuple] = []
    for opp in opponents:
        for i in range(games):
            seed = start_seed + i
            jobs.append((seed, candidate, opp, 0, steps, tag or candidate))
            if swap_seats:
                jobs.append((seed, candidate, opp, 1, steps, tag or candidate))
    return jobs


def run(jobs: list[tuple], workers: int, progress_every: int = 200) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    started = time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers, initializer=_worker_init) as pool:
        futures = [pool.submit(_play, j) for j in jobs]
        for idx, fut in enumerate(as_completed(futures), 1):
            rows.append(fut.result())
            if idx % progress_every == 0 or idx == len(futures):
                el = time.perf_counter() - started
                print(f"  {idx}/{len(futures)} games in {el:.0f}s "
                      f"({idx/el:.2f}/s)", flush=True)
    return rows


def default_workers() -> int:
    # Physical cores are the sweet spot for this Python-heavy engine.
    return min(16, os.cpu_count() or 4)
