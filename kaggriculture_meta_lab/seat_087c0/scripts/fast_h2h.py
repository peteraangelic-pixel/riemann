#!/usr/bin/env python3
"""Fast H2H for STATIC tape agents via the pinned raw simulator.

Bypasses kaggle_environments (no observation copies, agent deepcopies,
renderer, or replay logging) using rust_port/tools/py_reference.py, whose
mechanics are the byte-identical pinned interpreter. Multiprocess batch.

ONLY for pure-playback tape modules (module-level ACTIONS/_ACTIONS plus
optional import-time edits and runtime hand-trimming). State-dependent
agents (market overlays like G2/G4, reactive policies) are NOT valid here:
use --parity-k to cross-check N games against the slow framework harness
and abort on any mismatch.

CLI: fast_h2h.py '[cand_paths]' '[opp_paths]' '[seeds]' log.json [--jobs N] [--parity-k K]
Output format matches h2h_tape_runner.py.
"""
import importlib.util
import json
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
    if A is None:
        raise ValueError(f"{path}: no ACTIONS/_ACTIONS")
    if isinstance(A[0], dict):
        A = [A, A]  # single stream mirrored to both seats
    if not (isinstance(A, list) and len(A) == 2 and all(A)):
        raise ValueError(f"{path}: expected [seat0, seat1] action lists")
    return A


def fast_game(args):
    cand, opp, seed, swap = args
    t0 = time.time()
    r = PythonReplay(cand, opp, seed, steps=720, reverse=bool(swap), trim_hands=True)
    while r.advance():
        pass
    st = [s.status for s in r.state]
    rw = r.rewards()
    return seed, swap, rw[0], rw[1], st, time.time() - t0


def slow_game(cpath, opath, seed, swap):
    from kaggle_environments import make

    def load(p, n):
        spec = importlib.util.spec_from_file_location(n, p)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m.act if hasattr(m, "act") else m.agent

    a, b = load(cpath, "sa"), load(opath, "sb")
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    if swap:
        env.run([b, a])
        r0, r1 = env.state[1].reward, env.state[0].reward
    else:
        env.run([a, b])
        r0, r1 = env.state[0].reward, env.state[1].reward
    return r0, r1, [s.get("status") for s in env.state]


def main():
    args = sys.argv[1:]
    jobs = 0
    parity_k = 0
    rest = []
    i = 0
    while i < len(args):
        if args[i] == "--jobs":
            jobs = int(args[i + 1]); i += 2
        elif args[i] == "--parity-k":
            parity_k = int(args[i + 1]); i += 2
        else:
            rest.append(args[i]); i += 1
    cand_files, opp_files, seeds, logpath = json.loads(rest[0]), json.loads(rest[1]), json.loads(rest[2]), rest[3]
    import os
    jobs = jobs or (os.cpu_count() or 2)
    log = []
    for cpath in cand_files:
        cand = load_tape(cpath)
        for opath in opp_files:
            if Path(cpath).stem == Path(opath).stem:
                continue
            opp = load_tape(opath)
            game_jobs = [(cand, opp, s, sw) for s in seeds for sw in (0, 1)]
            if parity_k:
                print(f"parity check: {parity_k} slow games for {Path(cpath).stem} vs {Path(opath).stem} ...", flush=True)
                for (c, o, s, sw) in game_jobs[:parity_k]:
                    _, _, fr0, fr1, _, _ = fast_game((c, o, s, sw))
                    sr0, sr1, _ = slow_game(cpath, opath, s, sw)
                    if (fr0, fr1) != (sr0, sr1):
                        print(f"PARITY FAIL seed {s} swap {sw}: fast=({fr0},{fr1}) slow=({sr0},{sr1})", flush=True)
                        sys.exit(2)
                print("parity OK", flush=True)
            t0 = time.time()
            with Pool(jobs) as pool:
                results = pool.map(fast_game, game_jobs)
            dt = time.time() - t0
            w = l = t = 0; ms = sc = so = 0.0; games = []
            for (s, sw, r0, r1, st, _) in results:
                if any(e not in ("DONE", "ACTIVE") for e in st):
                    print(f"  !! status {cpath} vs {opath} seed {s} swap {sw}: {st}", flush=True)
                w, l, t = w + (r0 > r1), l + (r0 < r1), t + (r0 == r1)
                ms += r0 - r1; sc += r0; so += r1
                games.append({"seed": s, "swap": sw, "r0": r0, "r1": r1})
            n = w + l + t
            line = {"cand": Path(cpath).stem, "opp": Path(opath).stem, "w": w, "l": l, "t": t,
                    "margin_sum": ms, "mean_cand": sc / n, "mean_opp": so / n,
                    "games_per_s": round(n / dt, 2), "games": games}
            log.append(line)
            print(json.dumps({k: v for k, v in line.items() if k != "games"}) + f"  [{dt:.1f}s]", flush=True)
    Path(logpath).write_text(json.dumps(log, indent=1))


if __name__ == "__main__":
    main()
