#!/usr/bin/env python3
"""Single-block revert ablation: base tape with each market block reverted to donor.

Variant i (0..N-1): base stream with market orders on steps [i*B,(i+1)*B)
replaced by the donor's market; variant N = unmodified base (baseline).
All variants play every control (both seats) in ONE kg_sim batch.
Reports per-variant W/L/margin AND mean own gold (absolute economy):
blocks whose revert GAINS own gold but LOSES H2H margin are pure
shared-market denial (local edge that should not transfer live).

CLI mirrors search jobs: --base P --donor P --block 6 --controls n=p ...
  --start-seed N --games M --binary P --threads T --output J --tag T
"""
import argparse
import copy
import json
import statistics
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

SEAT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SEAT / "scripts"))
sys.path.insert(0, str(SEAT.parent / "rust_port" / "tools"))
from fast_h2h import load_tape  # noqa: E402
from rust_client import Job, replay_many  # noqa: E402

STEPS = 719


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--donor", required=True)
    ap.add_argument("--block", type=int, default=6)
    ap.add_argument("--controls", nargs="+", required=True)
    ap.add_argument("--start-seed", type=int, required=True)
    ap.add_argument("--games", type=int, required=True)
    ap.add_argument("--binary", type=Path, required=True)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--tag", default="ablate")
    a = ap.parse_args()
    n = (STEPS + a.block - 1) // a.block
    base = load_tape(a.base)
    donor = load_tape(a.donor)
    ctrls = {}
    for item in a.controls:
        name, path = item.split("=", 1)
        ctrls[name] = load_tape(path)
    variants = []
    for i in range(n):
        v = copy.deepcopy(base)
        for seat in (0, 1):
            for s in range(i * a.block, min((i + 1) * a.block, STEPS)):
                v[seat][s] = dict(v[seat][s])
                v[seat][s]["market"] = copy.deepcopy(donor[seat][s].get("market", []))
        variants.append(v)
    variants.append(base)  # index n = baseline
    seeds = list(range(a.start_seed, a.start_seed + a.games))
    with tempfile.TemporaryDirectory(prefix="kg-ablate-") as raw:
        td = Path(raw)
        vpaths = []
        for i, v in enumerate(variants):
            p = td / f"var-{i}.json"
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
        rows = replay_many(jobs, binary=a.binary, steps=720, threads=a.threads,
                           trim_hands_a=True, trim_hands_b=True,
                           allow_errors=True, timeout=1200)
    grouped = defaultdict(list)
    for r, key in zip(rows, meta):
        if r.get("errors") or r.get("rewards") is None:
            raise RuntimeError(f"rust game failed: {r.get('errors')}")
        grouped[key].append((float(r["rewards"][0]), float(r["rewards"][1])))
    out = {"tag": a.tag, "base": a.base, "donor": a.donor, "block": a.block,
           "variants": []}
    for i in range(n + 1):
        entry = {"variant": i if i < n else "baseline",
                 "steps": [i * a.block, min((i + 1) * a.block, STEPS)] if i < n else None,
                 "controls": {}}
        for c in ctrls:
            ms = [(x - y, x) for x, y in grouped[(i, c)]]
            margins = [m for m, _ in ms]
            own = [x for _, x in ms]
            w = sum(m > 0 for m in margins)
            l = sum(m < 0 for m in margins)
            entry["controls"][c] = {
                "games": len(ms), "wins": w, "losses": l, "ties": len(ms) - w - l,
                "score_rate": round((w + 0.5 * (len(ms) - w - l)) / len(ms), 4),
                "mean_margin": round(statistics.mean(margins), 1),
                "mean_own": round(statistics.mean(own), 1)}
        out["variants"].append(entry)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({"tag": a.tag, "jobs": len(jobs),
                      "baseline": out["variants"][n]["controls"]}, indent=1))


if __name__ == "__main__":
    main()
