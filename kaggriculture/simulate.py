"""Local Kaggriculture match runner.

Runs the repo agent against simple opponents on a local engine copy
(kaggle-environments), with optional deterministic seeds, and prints a compact
win/loss summary plus average final money.

Usage:
    .venv/bin/python simulate.py --games 4 --opponent pass --steps 720
    .venv/bin/python simulate.py --games 4 --opponent random --steps 720
    .venv/bin/python simulate.py --games 4 --opponent self --steps 720
"""

from __future__ import annotations

import argparse
import importlib.util
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_agent(path: Path):
    spec = importlib.util.spec_from_file_location("kaggriculture_agent", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.act


def passive(obs, config):
    return {"farmer": ["PASS"], "hands": [], "market": []}


def randomish(obs, config):
    """A crude 'does something' opponent: random moves, occasional planting."""
    rng = random
    player = obs["player"]
    me = obs["farms"][player]
    private = obs["private"]
    fx, fy = me["farmer"]
    tile = me["tiles"][fy][fx]
    market = []
    if private["seeds"].get("WHEAT", 0) < 2 and me["money"] >= 20 and rng.random() < 0.2:
        market.append(["BUY_SEED", "WHEAT", 2])
    if isinstance(tile, dict) and tile.get("kind") == "PLANT":
        if tile.get("yield_units", 0) > 0 and not tile.get("watered_today"):
            return {"farmer": ["WATER"], "hands": [], "market": market}
    if tile is None and private["seeds"].get("WHEAT", 0) > 0 and rng.random() < 0.5:
        return {"farmer": ["PLANT", "WHEAT"], "hands": [], "market": market}
    move = rng.choice(["NORTH", "SOUTH", "EAST", "WEST", "PASS"])
    return {"farmer": [move], "hands": [], "market": market}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--games", type=int, default=3)
    parser.add_argument("--opponent", choices=["pass", "random", "self"], default="pass")
    parser.add_argument("--steps", type=int, default=720)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    from kaggle_environments import make

    mine = load_agent(HERE / "agent.py")
    opponents = {"pass": passive, "random": randomish, "self": mine}
    opponent = opponents[args.opponent]

    wins = losses = ties = 0
    my_total = opp_total = 0
    for game in range(args.games):
        seed = args.seed + game
        env = make("kaggriculture", configuration={"episodeSteps": args.steps, "seed": seed})
        env.run([mine, opponent])
        r0, r1 = env.state[0].reward, env.state[1].reward
        my_total += r0
        opp_total += r1
        if r0 > r1:
            wins += 1
        elif r0 < r1:
            losses += 1
        else:
            ties += 1
        print(f"game {game + 1} (seed {seed}): me {r0:.0f} vs opp {r1:.0f} -> {'WIN' if r0 > r1 else 'LOSS' if r0 < r1 else 'TIE'}")

    print(f"\nvs {args.opponent}: {wins}W {losses}L {ties}T  | avg money me {my_total / args.games:.0f} / opp {opp_total / args.games:.0f}")
    return 0 if wins >= losses else 1


if __name__ == "__main__":
    sys.exit(main())
