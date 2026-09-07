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
    futures: dict = {}
    pool = ProcessPoolExecutor(max_workers=workers, initializer=_worker_init)
    try:
        futures = {pool.submit(_play, j): j for j in jobs}
        for idx, fut in enumerate(as_completed(futures), 1):
            try:
                rows.append(fut.result())
            except Exception as exc:  # noqa: BLE001 - record, don't crash run
                j = futures[fut]
                rows.append({"tag": j[5], "seed": j[0], "seat": j[3],
                             "opponent": j[2], "self_reward": 0.0,
                             "opp_reward": 0.0, "margin": 0.0,
                             "outcome": "error",
                             "error": f"{type(exc).__name__}: {exc}"})
            if idx % progress_every == 0 or idx == len(futures):
                el = time.perf_counter() - started
                print(f"  {idx}/{len(futures)} games in {el:.0f}s "
                      f"({idx/el:.2f}/s)", flush=True)
    except Exception as exc:  # pool died (OOM kill etc.) - salvage what we have
        print(f"  WARNING: process pool failed ({type(exc).__name__}: {exc}); "
              f"{len(rows)}/{len(jobs)} games salvaged", flush=True)
        for fut, j in futures.items():
            if not fut.done():
                rows.append({"tag": j[5], "seed": j[0], "seat": j[3],
                             "opponent": j[2], "self_reward": 0.0,
                             "opp_reward": 0.0, "margin": 0.0,
                             "outcome": "error", "error": "pool died"})
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
    return rows


def _available_mem_gb() -> float:
    """Best-effort free+cache-reclaimable memory in GB (Linux/macOS/Windows)."""
    try:
        if os.name == "nt":  # Windows: GlobalMemoryStatusEx via ctypes
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong),
                            ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong),
                            ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong),
                            ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong),
                            ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            return stat.ullAvailPhys / 1e9
        # Linux: parse /proc/meminfo (MemAvailable)
        info = {}
        with open("/proc/meminfo") as fh:
            for line in fh:
                k, _, v = line.partition(":")
                info[k.strip()] = float(v.strip().split()[0])  # kB
        return info.get("MemAvailable", info.get("MemTotal", 0)) / 1e6
    except Exception:
        return 8.0  # conservative fallback


def default_workers() -> int:
    """Physical cores are the sweet spot, but each worker uses ~0.3 GB RAM,
    so never start more workers than memory can sustain."""
    by_cpu = min(16, os.cpu_count() or 4)
    by_mem = max(1, int(_available_mem_gb() / 0.4))
    return max(1, min(by_cpu, by_mem))
