#!/usr/bin/env python3
"""One-batch screen of opening/market-step combinatorics.

Builds dozens of candidate variants from a SPEC file and evaluates ALL of
them against ALL controls in a single kg_sim batch (same pattern as the
sibling LAB: hundreds of candidates per Actions RUN).

Spec JSON:
  {"bodies": {name: path}, "donors": {name: path},
   "key_controls": [names...],
   "variants": [{"name": str, "body": str,
                 "overrides": {"<step>": {"market_from": donor_name} |
                                          {"market": [[order...]]}}}, ...]}
Step override replaces the FULL market list at that step (units untouched).

Ranking key: (min score over key_controls, min margin-delta vs body
baseline over key_controls, mean score, mean margin). Baselines are the
variants named "base-<body>" (no overrides); include them in the spec.
"""
import argparse
import copy
import json
import statistics
import sys
import tempfile
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

SEAT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SEAT / "scripts"))
sys.path.insert(0, str(SEAT.parent / "rust_port" / "tools"))
from fast_h2h import load_tape  # noqa: E402
from py_reference import PythonReplay  # noqa: E402


def build_variant(body, donors, overrides):
    v = copy.deepcopy(body)
    for step, ov in overrides.items():
        s = int(step)
        if "market_from" in ov:
            d = donors[ov["market_from"]]
            for seat in (0, 1):
                v[seat][s] = dict(v[seat][s])
                v[seat][s]["market"] = copy.deepcopy(d[seat][s].get("market", []))
        else:
            for seat in (0, 1):
                v[seat][s] = dict(v[seat][s])
                v[seat][s]["market"] = copy.deepcopy(ov["market"])
    return v


def summarize(ms):
    n = len(ms)
    w = sum(x > 0 for x in ms)
    l = sum(x < 0 for x in ms)
    return {"games": n, "wins": w, "losses": l, "ties": n - w - l,
            "score_rate": round((w + 0.5 * (n - w - l)) / n, 4),
            "mean_margin": round(statistics.mean(ms), 1)}


def _py_game(args):
    cand, opp, seed, swap = args
    r = PythonReplay(cand, opp, seed, steps=720, reverse=bool(swap), trim_hands=True)
    while r.advance():
        pass
    rw = r.rewards()
    return rw[0] - rw[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", type=Path, required=True)
    ap.add_argument("--controls", nargs="+", required=True)
    ap.add_argument("--start-seed", type=int, required=True)
    ap.add_argument("--games", type=int, required=True)
    ap.add_argument("--engine", choices=("rust", "python"), default="rust")
    ap.add_argument("--binary", type=Path, default=None)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--tag", default="screen")
    a = ap.parse_args()
    spec = json.loads(a.spec.read_text())
    bodies = {k: load_tape(v) for k, v in spec["bodies"].items()}
    donors = {k: load_tape(v) for k, v in spec["donors"].items()}
    ctrls = {}
    for item in a.controls:
        name, path = item.split("=", 1)
        ctrls[name] = load_tape(path)
    key = [c for c in spec.get("key_controls", list(ctrls)) if c in ctrls] or list(ctrls)
    variants = []
    for vspec in spec["variants"]:
        variants.append((vspec["name"], vspec["body"],
                         build_variant(bodies[vspec["body"]], donors, vspec.get("overrides", {}))))
    seeds = list(range(a.start_seed, a.start_seed + a.games))
    grouped = defaultdict(list)
    if a.engine == "rust":
        from rust_client import Job, replay_many
        binary = a.binary or (SEAT.parent / "rust_port" / "target" / "release" / "kg_sim")
        with tempfile.TemporaryDirectory(prefix="kg-screen-") as raw:
            td = Path(raw)
            vpaths = []
            for i, (_, _, v) in enumerate(variants):
                p = td / f"cand-{i}.json"
                p.write_text(json.dumps(v, separators=(",", ":")))
                vpaths.append(p)
            cpaths = {}
            for j, (c, t) in enumerate(ctrls.items()):
                p = td / f"ctrl-{j}.json"
                p.write_text(json.dumps(t, separators=(",", ":")))
                cpaths[c] = p
            jobs, meta = [], []
            for i, p in enumerate(vpaths):
                for c, op in cpaths.items():
                    for s in seeds:
                        for sw in (0, 1):
                            jobs.append(Job(s, p, op, reverse=bool(sw)))
                            meta.append((i, c))
            rows = replay_many(jobs, binary=binary, steps=720, threads=a.threads,
                               trim_hands_a=True, trim_hands_b=True,
                               allow_errors=True, timeout=1200)
        for r, k in zip(rows, meta):
            if r.get("errors") or r.get("rewards") is None:
                raise RuntimeError(f"rust game failed: {r.get('errors')}")
            grouped[k].append(float(r["rewards"][0]) - float(r["rewards"][1]))
        total = len(jobs)
    else:
        total = 0
        with Pool(a.threads) as pool:
            for i, (_, _, v) in enumerate(variants):
                for c, op in ctrls.items():
                    ms = pool.map(_py_game, [(v, op, s, w) for s in seeds for w in (0, 1)])
                    grouped[(i, c)].extend(ms)
                    total += len(ms)
    stats = [{c: summarize(grouped[(i, c)]) for c in ctrls} for i in range(len(variants))]
    base_idx = {}
    for i, (name, body, _) in enumerate(variants):
        if name == f"base-{body}":
            base_idx[body] = i
    ranked = []
    for i, (name, body, _) in enumerate(variants):
        s = stats[i]
        b = stats[base_idx[body]] if body in base_idx else None
        dmin = min(s[c]["score_rate"] for c in key)
        mmin = (min(s[c]["mean_margin"] - b[c]["mean_margin"] for c in key)
                if b is not None else 0.0)
        ranked.append(((dmin, mmin,
                        statistics.mean(x["score_rate"] for x in s.values()),
                        statistics.mean(x["mean_margin"] for x in s.values())), i))
    ranked.sort(reverse=True)
    out = {"tag": a.tag, "total_jobs": total, "key_controls": key,
           "controls": list(ctrls),
           "ranked": [{"rank": r + 1, "name": variants[i][0], "body": variants[i][1],
                       "key": [round(v, 4) for v in k], "stats": stats[i]}
                      for r, (k, i) in enumerate(ranked)]}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(out, indent=1) + "\n")
    for r, (k, i) in enumerate(ranked[:12]):
        s = stats[i]
        cells = " ".join(f"{c}:{s[c]['wins']}-{s[c]['losses']}" for c in key)
        print(f"#{r + 1} {variants[i][0]} key={[round(v, 2) for v in k]} {cells}", flush=True)
    print(json.dumps({"tag": a.tag, "total_jobs": total, "variants": len(variants)}), flush=True)


if __name__ == "__main__":
    main()
