"""Fertilizer-leverage probe.

Compares the base V7 policy against a fertilizer-buying variant in BOTH:
  * closed-loop head-to-head (adaptive), and
  * open-loop elite corpus (realistic shared market).

The hypothesis (verified in the engine): cheap fertilizer (~$1 floor, no shop
demand, cows supply it free) doubles the per-watering yield bonus, and the
elite shapes buy it heavily while V7 keeps FERTILIZER_RESERVE=0 (sells it).

    python scripts/fert_probe.py --base agents/ref/agent_v7.py \
        --variant "wrap:agents/ref/agent_v7.py:agents/variants/fert_buyer.py" \
        --corpus corpus/sample --games 60 --workers 12

Multiple fertilizer settings can be swept by monkeypatching the wrapper module
constants before import (see --buy-below / --buy-qty / --all-crops).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kaggriculture_lab.stats import aggregate  # noqa: E402
from kaggriculture_lab.tournament import build_jobs, default_workers, run  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="agents/ref/agent_v7.py")
    ap.add_argument("--variant",
                    default="wrap:agents/ref/agent_v7.py:agents/variants/fert_buyer.py")
    ap.add_argument("--opponent", action="append", default=["starter", "pass"],
                    help="closed-loop opponents (builtins or specs)")
    ap.add_argument("--corpus", default="corpus/sample")
    ap.add_argument("--games", type=int, default=60)
    ap.add_argument("--workers", type=int, default=default_workers())
    ap.add_argument("--start-seed", type=int, default=20260907)
    args = ap.parse_args()

    report = {"base": args.base, "variant": args.variant}

    # ---- closed-loop: variant vs base (this is the honest adaptive test) ----
    print("=== Closed-loop: fertilizer variant vs base policy ===")
    jobs = build_jobs(args.variant, [args.base, *args.opponent], args.games,
                      args.start_seed, swap_seats=True)
    t0 = time.perf_counter()
    rows = run(jobs, args.workers)
    report["closed_loop_elapsed"] = time.perf_counter() - t0

    vs_base = [r for r in rows if Path(r.get("opponent", "")).name.startswith("agent_v7")]
    vs_pool = rows
    print("\nVariant vs BASE policy:")
    a = aggregate(vs_base)
    print(f"  {a.wins}W {a.losses}L {a.ties}T  score {a.score_rate*100:.1f}% "
          f"(CI {a.ci_low*100:.1f}-{a.ci_high*100:.1f})  margin {a.mean_margin:+,.0f}  err {a.errors}")
    print("Variant vs whole pool (base+builtins):")
    a2 = aggregate(vs_pool)
    print(f"  {a2.wins}W {a2.losses}L {a2.ties}T  score {a2.score_rate*100:.1f}% "
          f"margin {a2.mean_margin:+,.0f}  mean cash {a2.mean_self:,.0f} vs {a2.mean_opp:,.0f}")
    report["variant_vs_base"] = a.to_dict()
    report["variant_vs_pool"] = a2.to_dict()

    # ---- open-loop corpus: base vs variant mean cash on the same replays -----
    print("\n=== Open-loop elite corpus ===")
    from concurrent.futures import ProcessPoolExecutor, as_completed
    from scripts.run_corpus import _job

    episodes = list((ROOT / args.corpus).rglob("replay.json*"))[: args.games]
    if episodes:
        for label, cand in (("base", args.base), ("variant", args.variant)):
            with ProcessPoolExecutor(max_workers=args.workers) as pool:
                res = [f.result() for f in as_completed(
                    [pool.submit(_job, (str(p), cand, ("Lauresowe",))) for p in episodes])]
            good = [r for r in res if not r.get("error")]
            means = [r["self"] for r in good]
            if means:
                import statistics
                print(f"  {label:8s}: mean cash {statistics.mean(means):,.0f} "
                      f"over {len(good)} episodes")
                report[f"corpus_{label}_mean"] = statistics.mean(means)

    (ROOT / "reports").mkdir(exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    out = ROOT / "reports" / f"fert-probe-{stamp}.json"
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("\nreport:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
