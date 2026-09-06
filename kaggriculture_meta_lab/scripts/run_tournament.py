"""Closed-loop paired-seed tournament.

Examples (Windows PowerShell - use backticks; bash - use backslashes as shown):
    python scripts/run_tournament.py \
        --candidate agents/ref/agent_v7.py \
        --opponent starter=starter --opponent v4=agents/ref/agent_v4.py \
        --opponent renoir="tape:corpus/sample/105787151/replay.json.gz" \
        --games 200 --workers 16

Add --baseline to compare a candidate mutation against an earlier policy and
enforce the promotion gate (Wilson CI low > 0.5, positive margin, no errors).
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kaggriculture_lab.agents import label as spec_label  # noqa: E402
from kaggriculture_lab.stats import aggregate, promotion_gate  # noqa: E402
from kaggriculture_lab.tournament import build_jobs, default_workers, run  # noqa: E402


def parse_spec(raw: str) -> tuple[str, str]:
    if "=" in raw:
        name, spec = raw.split("=", 1)
        return name.strip(), spec.strip()
    return spec_label(raw), raw


def main() -> int:
    ap = argparse.ArgumentParser(description="Closed-loop paired-seed tournament")
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--opponent", action="append", required=True)
    ap.add_argument("--games", type=int, default=100, help="seeds per opponent (both seats)")
    ap.add_argument("--workers", type=int, default=default_workers())
    ap.add_argument("--start-seed", type=int, default=20260907)
    ap.add_argument("--steps", type=int, default=720)
    ap.add_argument("--no-swap", action="store_true", help="only seat 0")
    ap.add_argument("--gate", action="store_true", help="enforce promotion gate on pooled result")
    ap.add_argument("--min-games", type=int, default=200)
    ap.add_argument("--tag", default=None)
    args = ap.parse_args()

    opponents = [parse_spec(o) for o in args.opponent]
    jobs = build_jobs(args.candidate, [s for _, s in opponents], args.games,
                      args.start_seed, swap_seats=not args.no_swap, steps=args.steps,
                      tag=args.tag)
    print(f"Closed-loop: {len(jobs)} games ({len(opponents)} opponents x {args.games} seeds "
          f"x {'2 seats' if not args.no_swap else '1 seat'}) on {args.workers} workers")
    t0 = time.perf_counter()
    rows = run(jobs, args.workers)
    elapsed = time.perf_counter() - t0

    out_dir = ROOT / "reports"
    out_dir.mkdir(exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")

    def _wlt(a):
        return f"{a['wins']}-{a['losses']}-{a['ties']}"

    def _ci(a):
        return f"{a['ci_low']*100:.1f}-{a['ci_high']*100:.1f}"

    grouped = {}
    print(f"\n{'opponent':22s} {'W-L-T':>9} {'score%':>7} {'95% CI':>15} {'margin':>9} err")
    for name, spec in opponents:
        sub = [r for r in rows if r.get("opponent") == spec]
        agg = aggregate(sub).to_dict()
        grouped[name] = agg
        print(f"{name:22s} {_wlt(agg):>9} {agg['score_rate']*100:6.1f}% "
              f"{_ci(agg):>15} {agg['mean_margin']:9.0f} {agg['errors']:>3}")

    total = aggregate(rows)
    td = total.to_dict()
    print(f"\n{'POOLED':22s} {_wlt(td):>9} {td['score_rate']*100:6.1f}% "
          f"{_ci(td):>15} {td['mean_margin']:9.0f} {td['errors']:>3}")
    print(f"elapsed {elapsed:.0f}s, {len(rows)/elapsed:.2f} games/s")

    payload = {"candidate": args.candidate, "games": args.games, "workers": args.workers,
               "elapsed_seconds": elapsed, "games_per_second": len(rows)/elapsed if elapsed else 0,
               "opponents": grouped, "pooled": td, "rows": rows}
    (out_dir / f"tournament-{stamp}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    with (out_dir / f"tournament-{stamp}.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["tag", "seed", "seat", "opponent", "self_reward",
                                          "opp_reward", "margin", "outcome", "error"],
                           extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print("reports:", out_dir / f"tournament-{stamp}.json")

    if args.gate:
        ok, reasons = promotion_gate(total, min_games=args.min_games)
        print(("\nGATE PASS: " if ok else "\nGATE FAIL: ") + " | ".join(reasons))
        return 0 if ok else 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
