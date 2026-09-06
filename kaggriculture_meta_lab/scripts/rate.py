"""Round-robin closed-loop rating (Elo + Bradley-Terry), mirroring the final.

    python scripts/rate.py \
        --agents v7=agents/ref/agent_v7.py \
        --agents v4=agents/ref/agent_v4.py \
        --agents starter=starter \
        --games 60 --workers 16
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kaggriculture_lab.stats import bradley_terry  # noqa: E402
from kaggriculture_lab.tournament import run  # noqa: E402
from scripts.run_tournament import parse_spec  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agents", action="append", required=True, help="label=spec")
    ap.add_argument("--games", type=int, default=60)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--start-seed", type=int, default=20260907)
    args = ap.parse_args()

    parsed = [parse_spec(a) for a in args.agents]
    labels = [l for l, _ in parsed]
    specs = {l: s for l, s in parsed}
    spec_to_label = {s: l for l, s in parsed}

    jobs = []
    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            la, lb = labels[i], labels[j]
            for k in range(args.games):
                seed = args.start_seed + k
                # candidate=la vs opponent=lb, both seats
                jobs.append((seed, specs[la], specs[lb], 0, 720, la))
                jobs.append((seed, specs[lb], specs[la], 0, 720, lb))

    print(f"{len(labels)} agents, {len(jobs)} games...")
    t0 = time.perf_counter()
    rows = run(jobs, args.workers)
    print(f"done in {time.perf_counter()-t0:.0f}s")

    wins: dict[tuple[str, str], float] = {}
    games: dict[tuple[str, str], int] = {}
    margin = {l: [] for l in labels}
    for r in rows:
        if r.get("outcome") == "error":
            continue
        cand_l = r["tag"]
        opp_l = spec_to_label.get(r["opponent"], r["opponent"])
        games[(cand_l, opp_l)] = games.get((cand_l, opp_l), 0) + 1
        score = 1.0 if r["outcome"] == "win" else 0.0 if r["outcome"] == "loss" else 0.5
        wins[(cand_l, opp_l)] = wins.get((cand_l, opp_l), 0.0) + score
        margin[cand_l].append(r["margin"])

    print("\nWIN-RATE matrix (row vs col %):")
    print("        " + "".join(f"{l[:9]:>10}" for l in labels))
    for la in labels:
        cells = []
        for lb in labels:
            if la == lb:
                cells.append("    -    ")
            else:
                n = games.get((la, lb), 0) + games.get((lb, la), 0)
                w = wins.get((la, lb), 0.0) + (games.get((lb, la), 0) - wins.get((lb, la), 0.0))
                cells.append(f"{100*w/n:8.1f} " if n else "    ?    ")
        print(f"{la[:8]:8s}" + "".join(f"{c:>10}" for c in cells))

    elo = {l: 1500.0 for l in labels}
    for (la, lb) in games:
        for _ in range(int(round(wins.get((la, lb), 0)))):
            ea = 1 / (1 + 10 ** ((elo[lb] - elo[la]) / 400))
            d = 32 * (1 - ea)
            elo[la] += d
            elo[lb] -= d
    bt = bradley_terry(wins, games, labels)

    import statistics
    print("\n" + f"{'agent':16s} {'Elo':>7} {'BT':>7} {'avg margin':>11}")
    for l in sorted(labels, key=lambda x: elo[x], reverse=True):
        m = statistics.mean(margin[l]) if margin[l] else 0.0
        print(f"{l[:16]:16s} {elo[l]:7.0f} {bt[l]:7.2f} {m:11.0f}")

    out = {"elo": elo, "bradley_terry": bt}
    p = ROOT / "reports" / f"rate-{time.strftime('%Y%m%d-%H%M%S')}.json"
    p.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("\nreport:", p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
