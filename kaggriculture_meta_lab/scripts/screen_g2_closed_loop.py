#!/usr/bin/env python3
"""Paired closed-loop one-factor screen around the proven compact G2 policy."""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from kaggriculture_lab.stats import aggregate
from kaggriculture_lab.tournament import build_jobs, run

PROFILES = {
    "identity": (6, 250, 1),
    "cash200": (6, 200, 1),
    "cash300": (6, 300, 1),
    "milk0": (6, 250, 0),
    "milk2": (6, 250, 2),
    "milk3": (6, 250, 3),
    "start4": (4, 250, 1),
    "start8": (8, 250, 1),
}


def render(source: str, profile: tuple[int, int, int]) -> str:
    start, cash, milk = profile
    replacements = {
        "if step//turns<6:return action": f"if step//turns<{start}:return action",
        'milk=max(0,shed.get("MILK",0)-1);market=[]': f'milk=max(0,shed.get("MILK",0)-{milk});market=[]',
        'float(farm.get("money",0) or 0)<=250': f'float(farm.get("money",0) or 0)<={cash}',
    }
    for old, new in replacements.items():
        if source.count(old) != 1:
            raise ValueError(f"expected one exact G2 token: {old}")
        source = source.replace(old, new)
    compile(source, "<g2-variant>", "exec")
    return source


def summarize(rows: list[dict]) -> dict:
    a = aggregate(rows)
    return {"games": a.games, "wins": a.wins, "losses": a.losses, "ties": a.ties,
            "errors": a.errors, "score_rate": a.score_rate, "mean_margin": a.mean_margin,
            "mean_self": a.mean_self, "mean_opp": a.mean_opp}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--games", type=int, default=3)
    ap.add_argument("--start-seed", type=int, default=20261220)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    source = args.base.read_text(encoding="utf-8")
    jobs = []
    with tempfile.TemporaryDirectory(prefix="kg-g2-screen-") as temp:
        for name, profile in PROFILES.items():
            path = Path(temp) / f"{name}.py"
            path.write_text(render(source, profile), encoding="utf-8")
            jobs.extend(build_jobs(str(path), [str(args.base)], args.games, args.start_seed,
                                   swap_seats=True, tag=name))
        rows = run(jobs, args.workers, progress_every=100)
    result = {"base": str(args.base), "seeds": args.games, "profiles": {
        name: summarize([row for row in rows if row["tag"] == name]) for name in PROFILES}}
    if any(row["errors"] for row in result["profiles"].values()):
        raise RuntimeError("G2 screen contains failed games")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
