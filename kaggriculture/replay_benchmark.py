"""Evaluate the current candidate against actions of real Kaggle opponents.

For each collected replay, the opponent's original actions are replayed open
loop in the original seed and player position. With the submitted agent this
reproduces the Kaggle result exactly; with a candidate it measures changes
against realistic market pressure and logistics. Sharding supports parallel
GitHub Actions jobs.
"""
from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUR_TEAM = "Lauresowe 3D"
PASS = {"farmer": ["PASS"], "hands": [], "market": []}


def load_agent(path: Path):
    spec = importlib.util.spec_from_file_location("replay_candidate", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.act


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--shards", type=int, default=1)
    parser.add_argument("--animal-kind", choices=["GOOSE", "COW", "SHEEP"])
    parser.add_argument("--animal-target", type=int)
    parser.add_argument("--per-worker", type=int)
    parser.add_argument("--feed-days", type=int)
    args = parser.parse_args()
    if not 0 <= args.shard < args.shards:
        parser.error("shard must satisfy 0 <= shard < shards")

    from kaggle_environments import make

    candidate = load_agent(HERE / "agent.py")
    module = candidate.__globals__
    if args.animal_kind is not None:
        module["ANIMAL_KIND"] = args.animal_kind
    if args.animal_target is not None:
        module["ANIMAL_TARGET"] = args.animal_target
    if args.per_worker is not None:
        module["ANIMALS_PER_WORKER"] = args.per_worker
    if args.feed_days is not None:
        module["FEED_STOCK_DAYS"] = args.feed_days

    replay_paths = sorted((HERE / "online").glob("*/replay.json.gz"))
    replay_paths = replay_paths[args.shard :: args.shards]
    scores: list[float] = []
    original_scores: list[float] = []
    wins = 0

    for path in replay_paths:
        with gzip.open(path, "rt") as stream:
            replay = json.load(stream)
        names = replay["info"]["TeamNames"]
        our_side = names.index(OUR_TEAM)
        opponent_side = 1 - our_side
        actions = [step[opponent_side].get("action") or PASS for step in replay["steps"]]

        def recorded_opponent(obs, config, actions=actions):
            # steps[0] is initial state; the action for agent step N is stored
            # in replay steps[N + 1].
            return actions[min(int(obs.get("step", 0)) + 1, len(actions) - 1)]

        configuration = dict(replay["configuration"])
        configuration["seed"] = replay["info"]["seed"]
        agents = [recorded_opponent, recorded_opponent]
        agents[our_side] = candidate
        env = make("kaggriculture", configuration=configuration)
        env.run(agents)
        candidate_score = env.state[our_side].reward
        opponent_score = env.state[opponent_side].reward
        original_score = replay["rewards"][our_side]
        scores.append(candidate_score)
        original_scores.append(original_score)
        wins += candidate_score > opponent_score
        print(
            f"{path.parent.name} side={our_side} opponent={names[opponent_side]!r} "
            f"original={original_score:.0f} candidate={candidate_score:.0f} "
            f"scripted_opponent={opponent_score:.0f} "
            f"result={'WIN' if candidate_score > opponent_score else 'LOSS'}"
        )

    if scores:
        print(
            f"SUMMARY kind={module['ANIMAL_KIND']} target={module['ANIMAL_TARGET']} "
            f"per_worker={module['ANIMALS_PER_WORKER']} feed_days={module['FEED_STOCK_DAYS']} "
            f"shard={args.shard}/{args.shards} games={len(scores)} wins={wins} "
            f"candidate_avg={sum(scores) / len(scores):.1f} "
            f"original_avg={sum(original_scores) / len(original_scores):.1f} "
            f"delta_avg={(sum(scores) - sum(original_scores)) / len(scores):+.1f}"
        )


if __name__ == "__main__":
    main()
