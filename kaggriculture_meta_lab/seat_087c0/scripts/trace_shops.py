#!/usr/bin/env python3
"""Trace H2H games collecting end-state market/town features per game.

Usage: trace_shops.py cand.py opp.py '[seeds]' out.json [--jobs N]
cand/opp: static tape modules. Output: per-game {seed, swap, r_cand, r_opp,
shops:{name:count}, prices:{...}} + correlation summary of kanno-side margin
vs shop counts. Used to test the shop-mix lead.
"""
import importlib.util
import json
import math
import statistics as st
import sys
import time
from multiprocessing import Pool
from pathlib import Path

SEAT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SEAT.parent / "rust_port" / "tools"))
from py_reference import PythonReplay  # noqa: E402


def load_tape(path):
    spec = importlib.util.spec_from_file_location("tape_" + Path(path).stem, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    A = getattr(m, "ACTIONS", None)
    if A is None:
        A = getattr(m, "_ACTIONS", None)
    if isinstance(A[0], dict):
        A = [A, A]
    return A


def trace_game(args):
    cand, opp, seed, swap = args
    r = PythonReplay(cand, opp, seed, steps=720, reverse=bool(swap), trim_hands=True)
    while r.advance():
        pass
    rw = r.rewards()
    snap = r.snapshot()
    shops = {}
    for s in snap["town"].get("unlocked_shops", []) or []:
        shops[s] = shops.get(s, 0) + 1
    return {"seed": seed, "swap": swap, "r_cand": rw[0], "r_opp": rw[1],
            "shops": shops, "prices": dict(snap["market"].get("prices", {}))}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    jobs = int(sys.argv[sys.argv.index("--jobs") + 1]) if "--jobs" in sys.argv else 0
    cpath, opath, seeds, outp = args[0], args[1], json.loads(args[2]), args[3]
    import os
    jobs = jobs or (os.cpu_count() or 2)
    cand, opp = load_tape(cpath), load_tape(opath)
    game_jobs = [(cand, opp, s, sw) for s in seeds for sw in (0, 1)]
    t0 = time.time()
    with Pool(jobs) as pool:
        games = pool.map(trace_game, game_jobs)
    dt = time.time() - t0
    margins = [g["r_cand"] - g["r_opp"] for g in games]
    allshops = sorted({s for g in games for s in g["shops"]})
    corrs = {}
    for s in allshops:
        xs = [g["shops"].get(s, 0) for g in games]
        mx, my = st.mean(xs), st.mean(margins)
        dx = [x - mx for x in xs]
        dy = [m - my for m in margins]
        den = math.sqrt(sum(a * a for a in dx) * sum(b * b for b in dy))
        corrs[s] = round(sum(a * b for a, b in zip(dx, dy)) / den, 3) if den else 0.0
    w = sum(1 for m in margins if m > 0)
    summary = {"w": w, "l": sum(1 for m in margins if m < 0),
               "t": sum(1 for m in margins if m == 0),
               "mean_margin": round(st.mean(margins), 1),
               "shop_corr": dict(sorted(corrs.items(), key=lambda kv: -abs(kv[1]))),
               "games_per_s": round(len(games) / dt, 1)}
    Path(outp).write_text(json.dumps({"summary": summary, "games": games}, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
