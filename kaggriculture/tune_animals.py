"""Matched-seed v3 animal sweep against the submitted v2 baseline.

Designed for GitHub Actions matrix jobs: each process evaluates one parameter
triple in both player positions, avoiding side bias.
"""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--geese", type=int, required=True)
    parser.add_argument("--per-worker", type=int, required=True)
    parser.add_argument("--feed-days", type=int, required=True)
    parser.add_argument("--seeds", type=int, default=12)
    args = parser.parse_args()

    from kaggle_environments import make

    candidate = load("candidate", HERE / "agent.py")
    baseline = load("submitted_v2", HERE.parent / "main.py")
    candidate.GOOSE_TARGET = args.geese
    candidate.GEESE_PER_WORKER = args.per_worker
    candidate.FEED_STOCK_DAYS = args.feed_days

    candidate_scores: list[float] = []
    baseline_scores: list[float] = []
    wins = ties = 0
    for seed in range(1, args.seeds + 1):
        for candidate_side in (0, 1):
            agents = [baseline.act, baseline.act]
            agents[candidate_side] = candidate.act
            env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
            env.run(agents)
            candidate_score = env.state[candidate_side].reward
            baseline_score = env.state[1 - candidate_side].reward
            candidate_scores.append(candidate_score)
            baseline_scores.append(baseline_score)
            wins += candidate_score > baseline_score
            ties += candidate_score == baseline_score

    games = len(candidate_scores)
    print(
        f"geese={args.geese} per_worker={args.per_worker} feed_days={args.feed_days} "
        f"games={games} wins={wins} losses={games - wins - ties} ties={ties} "
        f"candidate_avg={sum(candidate_scores) / games:.1f} "
        f"v2_avg={sum(baseline_scores) / games:.1f} "
        f"candidate_range={min(candidate_scores):.0f}-{max(candidate_scores):.0f}"
    )


if __name__ == "__main__":
    main()
