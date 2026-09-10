#!/usr/bin/env python3
"""Rust-powered joint evolution: German-opening cut + market-block donors.

Genome = (cut, b0..bN-1): `cut` = German-unit days (0..cut_max), then V3
units; each 6-hour market block takes its orders from one of K donor
tapes. Method adopted from sibling branch arena/01a0712c-riemann
(search_ours_peer_v4_hybrid.py): day-coherent breeding, per-control
regression floors, disjoint holdout, strict eligibility.

Designed for GitHub Actions (kg_sim, --engine rust). --engine python runs
the same logic on the pinned interpreter for small local logic tests.

Donors are full tape files; only their market streams are used. Units come
from --units-german / --units-v3. Clones of the champions (cut=9/all-V4,
cut=5/all-hybrid, cut=0/all-V3) are re-injected every generation; floors
are computed from the V4 clone. Eligibility (holdout): no control may
regress vs the V4 clone (score -0.01 / margin -250 tolerance), H2H vs v4
must clear (0.55, +100), H2H vs hybrid must clear 0.50.
"""
import argparse
import base64
import copy
import json
import os
import random
import statistics
import subprocess
import sys
import tempfile
import zlib
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

SEAT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SEAT / "scripts"))
sys.path.insert(0, str(SEAT.parent / "rust_port" / "tools"))
from fast_h2h import load_tape  # noqa: E402
from py_reference import PythonReplay  # noqa: E402

STEPS = 719


def parse_specs(items):
    out = {}
    for item in items:
        name, path = item.split("=", 1)
        out[name] = path
    return out


def materialize(g, donor_seats, gj, v3, block, n):
    cut = g[0]
    out = []
    for seat in (0, 1):
        stream = []
        for step in range(STEPS):
            unit = gj[seat][step] if step // 24 < cut else v3[seat][step]
            d = donor_seats[g[1 + min(step // block, n - 1)]][seat][step]
            stream.append({"farmer": unit.get("farmer", ["PASS"]),
                           "hands": unit.get("hands", []),
                           "market": d.get("market", [])})
        out.append(stream)
    return out


def clones(k):
    return [(c,) + (i,) * 120 for c in (9, 5, 0) for i in range(k)][:3 * k]


def initial(n, k, cut_max, seed):
    rng = random.Random(seed)
    out = [(9,) + (None,) * 0]  # placeholder removed below
    out = []
    for c in (9, 5, 0):
        for i in range(k):
            out.append((c,) + (i,) * 120)
    while len(out) < n:
        cut = rng.randrange(cut_max + 1)
        g = [rng.randrange(k) if rng.random() < 0.45 else (0 if rng.random() < 0.6 else rng.randrange(k))
             for _ in range(120)]
        out.append((cut,) + tuple(g))
    seen, res = set(), []
    for x in out:
        if x not in seen:
            seen.add(x)
            res.append(x)
    while len(res) < n:
        x = (rng.randrange(cut_max + 1),) + tuple(rng.randrange(k) for _ in range(120))
        if x not in seen:
            seen.add(x)
            res.append(x)
    return res[:n]


def breed(elite, n, k, cut_max, seed):
    rng = random.Random(seed)
    out, seen = list(elite), set(elite)
    while len(out) < n:
        a, b = rng.sample(elite, 2)
        cut = a[0] if rng.random() < 0.5 else b[0]
        if rng.random() < 0.08:
            cut = max(0, min(cut_max, cut + rng.choice([-1, 1])))
        g, use = [], a
        for i in range(120):
            if i % 4 == 0 and rng.random() < 0.2:
                use = b if use is a else a
            x = use[i + 1]
            if rng.random() < 0.02:
                x = rng.randrange(k)
            g.append(x)
        child = (cut,) + tuple(g)
        if child not in seen:
            seen.add(child)
            out.append(child)
    return out


def summarize(margins):
    n = len(margins)
    w = sum(x > 0 for x in margins)
    l = sum(x < 0 for x in margins)
    return {"games": n, "wins": w, "losses": l, "ties": n - w - l,
            "score_rate": (w + 0.5 * (n - w - l)) / n,
            "mean_margin": statistics.mean(margins), "worst_margin": min(margins)}


def fitness(stats, floor, h2h_primary):
    d_score = min(stats[c]["score_rate"] - floor[c]["score_rate"] for c in stats)
    d_margin = min(stats[c]["mean_margin"] - floor[c]["mean_margin"] for c in stats)
    return (d_score, stats[h2h_primary]["score_rate"], d_margin,
            statistics.mean(s["score_rate"] for s in stats.values()),
            statistics.mean(s["mean_margin"] for s in stats.values()))


def _py_game(args):
    cand, opp, seed, swap = args
    r = PythonReplay(cand, opp, seed, steps=720, reverse=bool(swap), trim_hands=True)
    while r.advance():
        pass
    rw = r.rewards()
    return rw[0] - rw[1]


def evaluate(pop, donor_seats, gj, v3t, controls, ctrl_tapes, seeds, block, n,
             engine, binary, threads, td, prefix):
    cand_tapes = [materialize(g, donor_seats, gj, v3t, block, n) for g in pop]
    grouped = defaultdict(list)
    total = 0
    if engine == "rust":
        from rust_client import Job, replay_many
        paths = []
        for i, t in enumerate(cand_tapes):
            p = td / f"{prefix}-cand-{i}.json"
            p.write_text(json.dumps(t, separators=(",", ":")))
            paths.append(p)
        jobs, meta = [], []
        for i, p in enumerate(paths):
            for name, op in controls.items():
                for seed in seeds:
                    for seat in (0, 1):
                        jobs.append(Job(seed, p, op, reverse=bool(seat)))
                        meta.append((i, name))
        total = len(jobs)
        raw = replay_many(jobs, binary=binary, steps=720, threads=threads,
                          trim_hands_a=True, trim_hands_b=True,
                          allow_errors=True, timeout=1200)
        for r, key in zip(raw, meta):
            if r.get("errors") or r.get("rewards") is None:
                raise RuntimeError(f"rust game failed: {r.get('errors')}")
            grouped[key].append(float(r["rewards"][0]) - float(r["rewards"][1]))
    else:
        with Pool(threads) as pool:
            for i, t in enumerate(cand_tapes):
                for name, op in ctrl_tapes.items():
                    ms = pool.map(_py_game, [(t, op, s, w) for s in seeds for w in (0, 1)])
                    grouped[(i, name)].extend(ms)
                    total += len(ms)
    return [{name: summarize(grouped[(i, name)]) for name in controls} for i in range(len(pop))], total


def emit_agent(path, stream_seat0, provenance):
    blob = base64.b85encode(zlib.compress(json.dumps(stream_seat0, separators=(",", ":")).encode(), 9)).decode()
    doc = f"Evolved champion candidate (search_rust_evolve.py).\n\n{provenance}\n\nLAB EMISSION - NOT PROMOTED until independent H2H + slow-G2 gates pass.\n"
    src = (f'"""{doc}"""\nimport base64, copy, json, zlib\n'
           f"_BLOB = {blob!r}\n"
           "_ACTIONS = json.loads(zlib.decompress(base64.b85decode(_BLOB)).decode())\n\n"
           "def _safe_pass(observation):\n"
           "    try:\n"
           '        p = int(observation.get("player", 0))\n'
           '        hands = ((observation.get("farms") or [])[p] or {}).get("hands") or []\n'
           "        n = len(hands)\n"
           "    except Exception:\n"
           "        n = 0\n"
           '    return {"farmer": ["PASS"], "hands": [["PASS"]] * n, "market": []}\n\n'
           "def agent(observation, configuration=None):\n"
           "    try:\n"
           '        step = min(int(observation.get("step", 0)), len(_ACTIONS) - 1)\n'
           "        action = copy.deepcopy(_ACTIONS[step])\n"
           '        p = int(observation.get("player", 0))\n'
           '        hands = ((observation.get("farms") or [])[p] or {}).get("hands") or []\n'
           '        action["hands"] = action.get("hands", [])[:len(hands)]\n'
           "        return action\n"
           "    except Exception:\n"
           "        return _safe_pass(observation)\n\n"
           "def act(observation, configuration=None):\n"
           "    return agent(observation, configuration)\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(src)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--donors", nargs="+", required=True, help="name=path market donors")
    ap.add_argument("--units-german", required=True)
    ap.add_argument("--units-v3", required=True)
    ap.add_argument("--controls", nargs="+", required=True, help="name=path static controls")
    ap.add_argument("--idx-v4", type=int, required=True, help="donor index of V4 market")
    ap.add_argument("--idx-hybrid", type=int, required=True)
    ap.add_argument("--idx-v3", type=int, required=True)
    ap.add_argument("--population", type=int, default=384)
    ap.add_argument("--generations", type=int, default=4)
    ap.add_argument("--elite", type=int, default=48)
    ap.add_argument("--finalists", type=int, default=24)
    ap.add_argument("--block", type=int, default=6)
    ap.add_argument("--cut-max", type=int, default=12)
    ap.add_argument("--train-seeds", type=int, default=8)
    ap.add_argument("--seed-base", type=int, default=41000)
    ap.add_argument("--holdout-start", type=int, default=42000)
    ap.add_argument("--holdout-games", type=int, default=64)
    ap.add_argument("--engine", choices=("rust", "python"), default="rust")
    ap.add_argument("--binary", type=Path, default=None)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--mask-seed", type=int, default=20260910)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--agent-output", type=Path, required=True)
    ap.add_argument("--tag", default="evolve")
    a = ap.parse_args()
    n = (STEPS + a.block - 1) // a.block
    assert n == 120, n
    donors = parse_specs(a.donors)
    dnames = list(donors)
    k = len(dnames)
    assert a.population > 3 * k, "population must exceed clone count"
    ctrls = parse_specs(a.controls)
    assert "v4" in ctrls and "hybrid" in ctrls, "controls must include v4 + hybrid"

    donor_seats = [load_tape(donors[d]) for d in dnames]
    gj = load_tape(a.units_german)
    v3t = load_tape(a.units_v3)
    ctrl_tapes = {c: load_tape(p) for c, p in ctrls.items()}
    V4C = (9,) + (a.idx_v4,) * n
    HYBC = (5,) + (a.idx_hybrid,) * n
    V3C = (0,) + (a.idx_v3,) * n

    with tempfile.TemporaryDirectory(prefix="kg-evolve-") as raw:
        td = Path(raw)
        if a.engine == "rust":
            if a.binary is None:
                a.binary = SEAT.parent / "rust_port" / "target" / "release" / "kg_sim"
            assert a.binary.exists(), f"missing rust binary: {a.binary}"
            ctrl_paths = {}
            for i, (c, t) in enumerate(ctrl_tapes.items()):
                p = td / f"control-{i}.json"
                p.write_text(json.dumps(t, separators=(",", ":")))
                ctrl_paths[c] = p
        else:
            ctrl_paths = {c: None for c in ctrl_tapes}

        # donor smoke: each all-donor clone vs v3, 2 seeds
        smoke_pop = [(0,) + (i,) * n for i in range(k)]
        sstats, sj = evaluate(smoke_pop, donor_seats, gj, v3t, {"v3": ctrl_paths.get("v3", list(ctrl_paths.values())[0])} if a.engine == "rust" else {"v3": None},
                              {"v3": ctrl_tapes.get("v3", list(ctrl_tapes.values())[0])},
                              [a.seed_base - 10, a.seed_base - 9], a.block, n,
                              a.engine, a.binary, a.threads, td, "smoke")
        print(f"donor smoke OK ({sj} games, 0 errors)", flush=True)

        pop = initial(a.population, k, a.cut_max, a.mask_seed)
        history, total = [], sj
        for gen in range(a.generations):
            seeds = range(a.seed_base + gen * 101, a.seed_base + gen * 101 + a.train_seeds)
            stats, j = evaluate(pop, donor_seats, gj, v3t, ctrl_paths, ctrl_tapes,
                                seeds, a.block, n, a.engine, a.binary, a.threads, td, f"g{gen}")
            total += j
            floor = stats[pop.index(V4C)]
            rank = sorted(range(len(pop)), key=lambda i: fitness(stats[i], floor, "v4"), reverse=True)
            best = rank[0]
            history.append({"generation": gen, "seeds": [seeds.start, seeds.stop - 1],
                            "best": {"cut": pop[best][0], "genes": list(pop[best][1:]), "stats": stats[best]},
                            "floor_v4clone": floor,
                            "hybrid_clone": stats[pop.index(HYBC)] if HYBC in pop else None})
            print(f"gen {gen}: {j} games; best cut={pop[best][0]} fit={[round(v,4) for v in fitness(stats[best], floor, 'v4')]}; "
                  f"v4clone-h2h={floor['v4']['wins']}-{floor['v4']['losses']}-{floor['v4']['ties']}", flush=True)
            elite = [pop[i] for i in rank[:a.elite]]
            if gen + 1 < a.generations:
                pop = breed(elite, a.population, k, a.cut_max, a.mask_seed + 1 + gen)
                pop[0], pop[1], pop[2] = V4C, HYBC, V3C

        fins = [pop[i] for i in rank[:a.finalists]]
        for c in (V4C, HYBC):
            if c not in fins:
                fins.append(c)
        hs, hj = evaluate(fins, donor_seats, gj, v3t, ctrl_paths, ctrl_tapes,
                          range(a.holdout_start, a.holdout_start + a.holdout_games),
                          a.block, n, a.engine, a.binary, a.threads, td, "holdout")
        total += hj
        base = hs[fins.index(V4C)]
        eligible = []
        for i, s in enumerate(hs):
            if fins[i] in (V4C, HYBC, V3C):
                continue
            guard = all(s[c]["score_rate"] >= base[c]["score_rate"] - 0.01 and
                        s[c]["mean_margin"] >= base[c]["mean_margin"] - 250 for c in s)
            if guard and s["v4"]["score_rate"] > 0.55 and s["v4"]["mean_margin"] > 100 and s["hybrid"]["score_rate"] > 0.5:
                eligible.append(i)
        winner = max(eligible, key=lambda i: fitness(hs[i], base, "v4")) if eligible else fins.index(V4C)
        emitted = bool(eligible)
        out = {"tag": a.tag, "donors": dnames, "controls": list(ctrls), "population": a.population,
               "generations": a.generations, "total_jobs": total, "history": history,
               "holdout": {"start": a.holdout_start, "games": a.holdout_games,
                           "finalists": [{"cut": g[0], "genes": list(g[1:]), "stats": s,
                                          "fitness": list(fitness(s, base, "v4"))} for g, s in zip(fins, hs)],
                           "baseline_v4clone": base, "eligible": eligible,
                           "winner_index": winner, "emitted": emitted}}
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(out, indent=1) + "\n")
        if emitted:
            seat0 = materialize(fins[winner], donor_seats, gj, v3t, a.block, n)[0]
            emit_agent(a.agent_output, seat0,
                       f"tag={a.tag}; cut={fins[winner][0]}; donors={dnames}; "
                       f"holdout={a.holdout_start}+{a.holdout_games}; total_jobs={total}")
            print(f"EMITTED {a.agent_output}", flush=True)
        else:
            print("no eligible winner (V4 clone retained as best)", flush=True)
        print(json.dumps({"total_jobs": total, "eligible": eligible, "winner": winner, "emitted": emitted}), flush=True)


if __name__ == "__main__":
    main()
