#!/usr/bin/env python3
"""Small paired screen isolating recovery-layer feature families."""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from kaggriculture_lab.stats import aggregate
from kaggriculture_lab.tournament import build_jobs, run

FLAGS = ("RECOVER_URGENT", "RECOVER_ENDGAME", "RECOVER_ANIMALS", "RECOVER_DROP")
PROFILES = {
    "identity": (),
    "urgent": ("RECOVER_URGENT",),
    "endgame": ("RECOVER_ENDGAME",),
    "animals": ("RECOVER_ANIMALS",),
    "drop": ("RECOVER_DROP",),
    "urgent_endgame": ("RECOVER_URGENT", "RECOVER_ENDGAME"),
}


def render(source: str, enabled: tuple[str, ...]) -> str:
    for flag in FLAGS:
        old = f"{flag} = True"
        assert source.count(old) == 1, flag
        source = source.replace(old, f"{flag} = {flag in enabled}")
    return source


def summary(rows: list[dict]) -> dict:
    agg = aggregate(rows)
    return {
        "games": agg.games,
        "wins": agg.wins,
        "losses": agg.losses,
        "ties": agg.ties,
        "errors": agg.errors,
        "score_rate": agg.score_rate,
        "mean_margin": agg.mean_margin,
        "mean_self": agg.mean_self,
        "mean_opp": agg.mean_opp,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--control", required=True)
    ap.add_argument("--games", type=int, default=4)
    ap.add_argument("--start-seed", type=int, default=20261100)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    source = args.base.read_text(encoding="utf-8")
    payload = {"control": args.control, "seeds": args.games, "profiles": {}}
    with tempfile.TemporaryDirectory(prefix="kg-recovery-") as temp:
        temp_path = Path(temp)
        jobs = []
        for name, flags in PROFILES.items():
            wrapper = temp_path / f"{name}.py"
            wrapper.write_text(render(source, flags), encoding="utf-8")
            candidate = f"wrap:agents/current/agent_v9_b21_s16.py:{wrapper}"
            jobs.extend(build_jobs(candidate, [args.control], args.games, args.start_seed,
                                   swap_seats=True, tag=name))
        # One shared worker pool avoids six expensive framework startups and
        # keeps the bounded screen comfortably below the Actions timeout.
        all_rows = run(jobs, args.workers, progress_every=100)
        for name in PROFILES:
            payload["profiles"][name] = summary([row for row in all_rows if row["tag"] == name])
    if any(row["errors"] for row in payload["profiles"].values()):
        raise RuntimeError("ablation contains failed games")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
