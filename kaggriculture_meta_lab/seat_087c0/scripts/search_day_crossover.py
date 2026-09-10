#!/usr/bin/env python3
"""Day-level crossover search between two static parent tapes.

Method adopted from sibling branch arena/01a0712c-riemann
(search_kanno_german_day_crossover.py): swap coherent 24-turn days between
two parents, never individual fields. Pure-Python port for this branch's
stack (fast_h2h loader + pinned py_reference simulator).

Pipeline per parent pair:
  S1 screen:  100 masks (58 single-cut + 42 random sparse) vs {parentA, b21}
              on train seeds -> top 12 by (worst score-rate, mean, margin)
  S2 confirm: top 12 vs {v3, v1, b21, subin} on fresh seeds -> top 3
  S3 holdout: top 3 + parentA baseline vs same 4 controls, fresh seeds.
              Winner agent file is EMITTED but NOT promoted; promotion is a
              manual decision after reading the holdout card.

Workers share tapes via Pool initializer (py_reference never mutates the
tape: advance() shallow-copies each action before trim; a hash guard aborts
if the shared tapes ever change).
"""
import argparse
import base64
import copy
import hashlib
import importlib.util
import json
import random
import statistics
import sys
import time
from multiprocessing import Pool
from pathlib import Path

SEAT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SEAT / "scripts"))
sys.path.insert(0, str(SEAT.parent / "rust_port" / "tools"))
from fast_h2h import load_tape  # noqa: E402
from py_reference import PythonReplay  # noqa: E402

_TAPES = []
_HASH0 = ""


def _tape_hash():
    h = hashlib.sha256()
    for t in _TAPES:
        h.update(json.dumps(t, sort_keys=True).encode())
    return h.hexdigest()


def _init(tapes):
    global _TAPES, _HASH0
    _TAPES = tapes
    _HASH0 = _tape_hash()


def _game(job):
    ci, oi, seed, swap = job
    r = PythonReplay(_TAPES[ci], _TAPES[oi], seed, steps=720,
                     reverse=bool(swap), trim_hands=True)
    while r.advance():
        pass
    st = [s.status for s in r.state]
    rw = r.rewards()
    err = None if all(s in ("ACTIVE", "DONE") for s in st) else str(st)
    return (ci, oi, seed, swap, rw[0], rw[1], err)


def check_tapes_unchanged(pool):
    h = pool.apply(_tape_hash_job)
    assert h == pool.apply(_hash0_job), "WORKER TAPES MUTATED - results invalid"


def _tape_hash_job():
    return _tape_hash()


def _hash0_job():
    return _HASH0


def masks_100(rng_seed):
    out = []
    for cut in range(1, 30):
        out.append((False,) * cut + (True,) * (30 - cut))
        out.append((True,) * cut + (False,) * (30 - cut))
    assert len(out) == 58
    rng = random.Random(rng_seed)
    seen = set(out)
    while len(out) < 100:
        v = [False] * 30
        for d in rng.sample(range(30), rng.randint(1, 10)):
            v[d] = True
        v = tuple(v)
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def crossover(sa, sb, mask):
    n = min(len(sa), len(sb))
    return [copy.deepcopy(sb[i] if mask[min(i // 24, 29)] else sa[i]) for i in range(n)]


def summarize(rows):
    by = {}
    for (ci, oi, seed, swap, r0, r1, err) in rows:
        by.setdefault((ci, oi), []).append((r0 - r1, err))
    out = {}
    for key, games in by.items():
        errs = [e for _, e in games if e]
        ms = [m for m, e in games if not e]
        w = sum(m > 0 for m in ms)
        l = sum(m < 0 for m in ms)
        t = sum(m == 0 for m in ms)
        n = len(ms)
        out[key] = {"games": n, "wins": w, "losses": l, "ties": t,
                    "errors": len(errs),
                    "score_rate": (w + 0.5 * t) / n if n else 0.0,
                    "mean_margin": statistics.mean(ms) if ms else 0.0,
                    "worst_margin": min(ms) if ms else 0.0}
    return out


def rank_key(controls):
    ss = [c["score_rate"] for c in controls]
    return (min(ss), statistics.mean(ss), statistics.mean([c["mean_margin"] for c in controls]))


def run_jobs(pool, jobs):
    t0 = time.time()
    rows = pool.map(_game, jobs, chunksize=4)
    dt = time.time() - t0
    check_tapes_unchanged(pool)
    return rows, dt


def emit_agent(path, stream, mask, pa_name, pb_name, card):
    blob = base64.b85encode(json.dumps(stream, separators=(",", ":")).encode()).decode()
    doc = (f"Crossover candidate {mask} ({pa_name} x {pb_name}).\n\n"
           f"LAB EMISSION - NOT PROMOTED. Holdout card:\n{json.dumps(card, indent=1)}\n")
    src = (f'"""{doc}"""\nimport base64, copy, json\n'
           f'_BLOB = {blob!r}\n'
           f'_ACTIONS = json.loads(base64.b85decode(_BLOB).decode())\n\n'
           'def _safe_pass(observation):\n'
           '    try:\n'
           '        p = int(observation.get("player", 0))\n'
           '        hands = ((observation.get("farms") or [])[p] or {}).get("hands") or []\n'
           '        n = len(hands)\n'
           '    except Exception:\n'
           '        n = 0\n'
           '    return {"farmer": ["PASS"], "hands": [["PASS"]] * n, "market": []}\n\n'
           'def agent(observation, configuration=None):\n'
           '    try:\n'
           '        step = min(int(observation.get("step", 0)), len(_ACTIONS) - 1)\n'
           '        action = copy.deepcopy(_ACTIONS[step])\n'
           '        p = int(observation.get("player", 0))\n'
           '        hands = ((observation.get("farms") or [])[p] or {}).get("hands") or []\n'
           '        action["hands"] = action.get("hands", [])[:len(hands)]\n'
           '        return action\n'
           '    except Exception:\n'
           '        return _safe_pass(observation)\n\n'
           'def act(observation, configuration=None):\n'
           '    return agent(observation, configuration)\n')
    path.write_text(src)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pa", required=True, help="parent A tape (= promotion baseline)")
    ap.add_argument("--pb", required=True, help="parent B tape (donor days)")
    ap.add_argument("--controls", nargs="+", required=True, help="S2/S3 control tapes")
    ap.add_argument("--b21", required=True, help="S1 second screen opponent")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--jobs", type=int, default=0)
    ap.add_argument("--mask-seed", type=int, default=20260910)
    ap.add_argument("--top1", type=int, default=12)
    ap.add_argument("--top2", type=int, default=3)
    a = ap.parse_args()
    import os
    jobs = a.jobs or (os.cpu_count() or 2)

    A = load_tape(a.pa)
    B = load_tape(a.pb)
    sa, sb = A[0], B[0]
    print(f"parents: {Path(a.pa).stem} ({len(sa)}) x {Path(a.pb).stem} ({len(sb)})", flush=True)
    masks = masks_100(a.mask_seed)
    kids = [crossover(sa, sb, m) for m in masks]
    kid_tapes = [[k, k] for k in kids]

    ctrl_tapes = {c: load_tape(c) for c in a.controls}
    b21 = load_tape(a.b21)
    pa_tape = load_tape(a.pa)

    # tape table: [kids(100), pa, b21, controls...]
    names = [f"kid-{i}" for i in range(100)] + ["parentA", "b21"] + [Path(c).stem for c in a.controls]
    tapes = kid_tapes + [pa_tape, b21] + [ctrl_tapes[c] for c in a.controls]
    KID = list(range(100))
    PAA, B21 = 100, 101
    CTRL = {c: 102 + i for i, c in enumerate(a.controls)}

    out = {"tag": a.tag, "pa": a.pa, "pb": a.pb, "controls": a.controls,
           "mask_seed": a.mask_seed}
    with Pool(jobs, initializer=_init, initargs=(tapes,)) as pool:
        # S1 screen
        s1seeds = list(range(500, 506))
        jobs1 = [(k, o, s, w) for k in KID for o in (PAA, B21) for s in s1seeds for w in (0, 1)]
        rows, dt = run_jobs(pool, jobs1)
        s1 = summarize(rows)
        scored = []
        for k in KID:
            cs = [s1[(k, PAA)], s1[(k, B21)]]
            scored.append((rank_key(cs), k))
        scored.sort(reverse=True)
        out["s1"] = {"seeds": s1seeds, "games": len(rows), "seconds": round(dt, 1),
                     "top": [{"kid": k, "mask": "".join("B" if x else "A" for x in masks[k]),
                              "key": [round(v, 4) for v in key],
                              "vs_pa": s1[(k, PAA)], "vs_b21": s1[(k, B21)]}
                             for key, k in scored[:a.top1]]}
        print(f"S1: {len(rows)} games in {dt:.0f}s; best: " +
              ", ".join(f"k{t['kid']}({t['key'][0]:.2f}/{t['key'][1]:.2f}/{t['key'][2]:.0f})" for t in out["s1"]["top"][:5]), flush=True)
        fin1 = [t["kid"] for t in out["s1"]["top"]]

        # S2 confirm
        s2seeds = list(range(510, 518))
        jobs2 = [(k, CTRL[c], s, w) for k in fin1 for c in a.controls for s in s2seeds for w in (0, 1)]
        rows, dt = run_jobs(pool, jobs2)
        s2 = summarize(rows)
        scored = []
        for k in fin1:
            cs = [s2[(k, CTRL[c])] for c in a.controls]
            scored.append((rank_key(cs), k))
        scored.sort(reverse=True)
        out["s2"] = {"seeds": s2seeds, "games": len(rows), "seconds": round(dt, 1),
                     "top": [{"kid": k, "mask": "".join("B" if x else "A" for x in masks[k]),
                              "key": [round(v, 4) for v in key],
                              "controls": {Path(c).stem: s2[(k, CTRL[c])] for c in a.controls}}
                             for key, k in scored[:a.top2]]}
        print(f"S2: {len(rows)} games in {dt:.0f}s; best: " +
              ", ".join(f"k{t['kid']}({t['key'][0]:.2f}/{t['key'][1]:.2f}/{t['key'][2]:.0f})" for t in out["s2"]["top"]), flush=True)
        fin2 = [t["kid"] for t in out["s2"]["top"]]

        # S3 holdout: finalists + parentA baseline
        s3seeds = list(range(520, 552))
        jobs3 = [(k, CTRL[c], s, w) for k in fin2 + [PAA] for c in a.controls for s in s3seeds for w in (0, 1)]
        rows, dt = run_jobs(pool, jobs3)
        s3 = summarize(rows)
        cards = []
        for k in fin2:
            cs = [s3[(k, CTRL[c])] for c in a.controls]
            cards.append({"kid": k, "mask": "".join("B" if x else "A" for x in masks[k]),
                          "key": [round(v, 4) for v in rank_key(cs)],
                          "controls": {Path(c).stem: s3[(k, CTRL[c])] for c in a.controls}})
        cards.sort(key=lambda t: t["key"], reverse=True)
        base = {"kid": "parentA",
                "controls": {Path(c).stem: s3[(PAA, CTRL[c])] for c in a.controls}}
        out["s3"] = {"seeds": [s3seeds[0], s3seeds[-1]], "games": len(rows),
                     "seconds": round(dt, 1), "finalists": cards, "baseline": base}
        for t in cards:
            print(f"S3 kid-{t['kid']} {t['mask']} key={t['key']}", flush=True)
            for cn, c in t["controls"].items():
                print(f"    vs {cn}: {c['wins']}-{c['losses']}-{c['ties']} m={c['mean_margin']:.0f}", flush=True)
        print("S3 parentA baseline:", flush=True)
        for cn, c in base["controls"].items():
            print(f"    vs {cn}: {c['wins']}-{c['losses']}-{c['ties']} m={c['mean_margin']:.0f}", flush=True)

    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / f"{a.tag}.json").write_text(json.dumps(out, indent=1))
    win = cards[0]
    emit_agent(a.out / f"{a.tag}_winner.py", kids[win["kid"]], win["mask"],
               Path(a.pa).stem, Path(a.pb).stem, win)
    print(f"wrote {a.tag}.json + {a.tag}_winner.py", flush=True)


if __name__ == "__main__":
    main()
