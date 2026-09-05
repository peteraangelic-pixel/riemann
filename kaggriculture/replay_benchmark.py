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
import zipfile
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
    parser.add_argument("--agent", default="agent.py")
    parser.add_argument(
        "--archive", type=Path,
        help="ZIP of external replays; candidate is tested on both sides of each match",
    )
    parser.add_argument("--profile", choices=[
        "cow5", "cow5-s16", "cow8", "cow8-s16", "sheep6-s16",
        "mix5-2", "mix5-2-s8", "mix5-2-s16",
        "mix5-4", "mix5-4-s8", "mix5-4-s16", "mix5-4-s24",
        "mix5-4-s16-f0", "mix5-4-s16-f24", "mix5-4-s16-m8",
        "mix6-4", "mix6-4-s8", "mix6-4-s16",
        "mix6-6-s20", "mix8-4", "mix10-4", "mix8-8",
        "mix8-6", "mix8-6-f0", "mix8-6-s20", "mix8-6-s28-m12",
        "mix11-9", "mix12-8", "crop-s42-m12",
    ])
    parser.add_argument("--animal-kind", choices=["GOOSE", "COW", "SHEEP"])
    parser.add_argument("--animal-target", type=int)
    parser.add_argument("--per-worker", type=int)
    parser.add_argument("--feed-days", type=int)
    parser.add_argument(
        "--set", action="append", default=[], metavar="NAME=VALUE",
        help="override an uppercase candidate constant; VALUE is JSON when possible",
    )
    args = parser.parse_args()
    if not 0 <= args.shard < args.shards:
        parser.error("shard must satisfy 0 <= shard < shards")

    from kaggle_environments import make

    candidate = load_agent(HERE / args.agent)
    module = candidate.__globals__
    profiles = {
        "cow5": ({"COW": 5, "SHEEP": 0}, 0, 12, 4),
        "cow5-s16": ({"COW": 5, "SHEEP": 0}, 16, 12, 4),
        "cow8": ({"COW": 8, "SHEEP": 0}, 0, 0, 4),
        "cow8-s16": ({"COW": 8, "SHEEP": 0}, 16, 12, 4),
        "sheep6-s16": ({"COW": 0, "SHEEP": 6}, 16, 12, 4),
        "mix5-2": ({"COW": 5, "SHEEP": 2}, 0, 12, 4),
        "mix5-2-s8": ({"COW": 5, "SHEEP": 2}, 8, 12, 4),
        "mix5-2-s16": ({"COW": 5, "SHEEP": 2}, 16, 12, 4),
        "mix5-4": ({"COW": 5, "SHEEP": 4}, 0, 12, 4),
        "mix5-4-s8": ({"COW": 5, "SHEEP": 4}, 8, 12, 4),
        "mix5-4-s16": ({"COW": 5, "SHEEP": 4}, 16, 12, 4),
        "mix5-4-s24": ({"COW": 5, "SHEEP": 4}, 24, 12, 4),
        "mix5-4-s16-f0": ({"COW": 5, "SHEEP": 4}, 16, 0, 4),
        "mix5-4-s16-f24": ({"COW": 5, "SHEEP": 4}, 16, 24, 4),
        "mix5-4-s16-m8": ({"COW": 5, "SHEEP": 4}, 16, 12, 8),
        "mix6-4": ({"COW": 6, "SHEEP": 4}, 0, 12, 4),
        "mix6-4-s8": ({"COW": 6, "SHEEP": 4}, 8, 12, 4),
        "mix6-4-s16": ({"COW": 6, "SHEEP": 4}, 16, 12, 4),
        "mix6-6-s20": ({"COW": 6, "SHEEP": 6}, 20, 12, 4),
        "mix8-4": ({"COW": 8, "SHEEP": 4}, 0, 12, 4),
        "mix10-4": ({"COW": 10, "SHEEP": 4}, 0, 12, 4),
        "mix8-8": ({"COW": 8, "SHEEP": 8}, 0, 12, 4),
        "mix8-6": ({"COW": 8, "SHEEP": 6}, 0, 12, 4),
        "mix8-6-f0": ({"COW": 8, "SHEEP": 6}, 0, 0, 4),
        "mix8-6-s20": ({"COW": 8, "SHEEP": 6}, 20, 12, 4),
        "mix8-6-s28-m12": ({"COW": 8, "SHEEP": 6}, 28, 12, 12),
        "mix11-9": ({"COW": 11, "SHEEP": 9}, 0, 12, 4),
        "mix12-8": ({"COW": 12, "SHEEP": 8}, 0, 12, 4),
        "crop-s42-m12": ({"COW": 0, "SHEEP": 0}, 42, 0, 12),
    }
    if args.profile:
        targets, strawberries, fertilizer, melons = profiles[args.profile]
        module["ANIMAL_TARGETS"] = targets
        module["STRAWBERRY_TARGET"] = strawberries
        module["FERTILIZER_RESERVE"] = fertilizer
        module["MELON_CELLS"] = [(x, y) for y in range(2) for x in range(4)][:melons]
        module["ANIMAL_TARGET"] = sum(targets.values())
    if args.animal_kind is not None:
        module["ANIMAL_KIND"] = args.animal_kind
    if args.animal_target is not None:
        module["ANIMAL_TARGET"] = args.animal_target
    if args.per_worker is not None:
        module["ANIMALS_PER_WORKER"] = args.per_worker
    if args.feed_days is not None:
        module["FEED_STOCK_DAYS"] = args.feed_days
    for override in args.set:
        if "=" not in override:
            parser.error(f"invalid --set {override!r}; expected NAME=VALUE")
        name, raw = override.split("=", 1)
        if not name.isupper() or name not in module:
            parser.error(f"unknown or non-constant override {name!r}")
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            value = raw
        if name == "MELON_CELLS" and isinstance(value, list):
            value = [tuple(cell) for cell in value]
        module[name] = value

    records: list[tuple[str, dict, int]] = []
    if args.archive:
        archive_path = args.archive if args.archive.is_absolute() else HERE.parent / args.archive
        with zipfile.ZipFile(archive_path) as archive:
            for member in sorted(n for n in archive.namelist() if n.endswith(".json")):
                with archive.open(member) as stream:
                    replay = json.load(stream)
                # External champion matches do not contain our team. Running
                # both seats prevents side-specific seeds/layouts from biasing
                # the small elite corpus.
                for candidate_side in (0, 1):
                    records.append((Path(member).stem, replay, candidate_side))
    else:
        for path in sorted((HERE / "online").glob("*/replay.json.gz")):
            with gzip.open(path, "rt") as stream:
                replay = json.load(stream)
            records.append((path.parent.name, replay, replay["info"]["TeamNames"].index(OUR_TEAM)))
    records = records[args.shard :: args.shards]
    scores: list[float] = []
    original_scores: list[float] = []
    wins = 0

    for replay_id, replay, our_side in records:
        names = replay["info"]["TeamNames"]
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
            f"{replay_id} side={our_side} opponent={names[opponent_side]!r} "
            f"original={original_score:.0f} candidate={candidate_score:.0f} "
            f"scripted_opponent={opponent_score:.0f} "
            f"result={'WIN' if candidate_score > opponent_score else 'LOSS'}"
        )

    if scores:
        print(
            f"SUMMARY agent={args.agent} profile={args.profile or 'default'} overrides={','.join(args.set) or '-'} "
            f"kind={module.get('ANIMAL_KIND')} target={module.get('ANIMAL_TARGET')} "
            f"targets={module.get('ANIMAL_TARGETS', {})} strawberries={module.get('STRAWBERRY_TARGET', 0)} "
            f"per_worker={module['ANIMALS_PER_WORKER']} feed_days={module['FEED_STOCK_DAYS']} "
            f"shard={args.shard}/{args.shards} games={len(scores)} wins={wins} "
            f"candidate_avg={sum(scores) / len(scores):.1f} "
            f"original_avg={sum(original_scores) / len(original_scores):.1f} "
            f"delta_avg={(sum(scores) - sum(original_scores)) / len(scores):+.1f}"
        )


if __name__ == "__main__":
    main()
