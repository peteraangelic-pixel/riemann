"""Tiny adapter around the UNMODIFIED, pinned Python interpreter.

No dependency on the heavyweight Kaggle package. Only its exact seed resolver
is injected for import. Mechanics are always executed by reference/*.py.
The framework's action-step counting is mirrored explicitly; no Python game
logic is rewritten here. Optional framework smoke tests live in tools/.
"""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "reference"


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_simulator():
    helper = _load_module("kg_seed_utils", REFERENCE / "seed_utils.py")
    package = ModuleType("kaggle_environments")
    utils = ModuleType("kaggle_environments.utils")
    utils.resolve_episode_seed = helper.resolve_episode_seed
    spec = importlib.util.spec_from_file_location("kg_python_reference", REFERENCE / "kaggriculture_sim.py")
    module = importlib.util.module_from_spec(spec)
    # The supplied file expects kaggriculture.json; preserve the supplied names
    # and bytes instead of modifying the simulator or requiring a symlink.
    real_open = open

    def reference_open(file, *args, **kwargs):
        if Path(file) == REFERENCE / "kaggriculture.json":
            file = REFERENCE / "kaggriculture_config.json"
        return real_open(file, *args, **kwargs)

    module.open = reference_open
    with patch.dict(sys.modules, {"kaggle_environments": package, "kaggle_environments.utils": utils}):
        spec.loader.exec_module(module)
    return module


SIM = load_simulator()


def configuration(overrides=None):
    values = {}
    for key, value in SIM.specification["configuration"].items():
        values[key] = copy.deepcopy(value.get("default") if isinstance(value, dict) else value)
    if overrides:
        specification = "name" in overrides and "configuration" in overrides
        overrides = overrides.get("configuration", overrides)
        values.update({key: copy.deepcopy(value.get("default", value) if specification and isinstance(value, dict) else value) for key, value in overrides.items()})
    return values


def action_turns(steps, step_mode="kaggle"):
    if step_mode == "turns":
        return steps
    if steps < 1:
        raise ValueError("episodeSteps must be >= 1")
    return max(1, steps - 1)


class PythonReplay:
    def __init__(self, tape_a, tape_b, seed, *, steps=720, reverse=False, trim_hands=False, step_mode="kaggle", config=None, trim_hands_a=False, trim_hands_b=False):
        cfg = configuration(config)
        self.turns = action_turns(steps, step_mode)
        cfg["episodeSteps"] = steps if step_mode == "kaggle" else steps + 1
        cfg["seed"] = seed
        self.env = SimpleNamespace(configuration=SimpleNamespace(**cfg), info={}, done=False)
        self.state = [SimpleNamespace(observation=SimpleNamespace(step=0), action={}, status="ACTIVE", reward=0) for _ in range(2)]
        SIM.interpreter(self.state, self.env)
        self.tapes = (tape_b, tape_a) if reverse else (tape_a, tape_b)
        self.reverse = reverse
        self.trim_hands = [trim_hands or trim_hands_a, trim_hands or trim_hands_b]
        if reverse:
            self.trim_hands.reverse()
        self.step = 0

    def advance(self):
        if self.step >= self.turns:
            return False
        for p in range(2):
            seat = self.tapes[p][p]
            action = seat[min(self.step, len(seat) - 1)]
            if self.trim_hands[p] and isinstance(action, dict):
                action = dict(action)
                hands = action.get("hands", [])
                action["hands"] = hands[:len(self.state[0].observation.farms[p]["hands"])] if isinstance(hands, list) else []
            self.state[p].action = action
        self.state[0].observation.step = self.step
        SIM.interpreter(self.state, self.env)
        self.step += 1
        self.state[0].observation.step = self.step
        return True

    def rewards(self):
        result = [farm["money"] for farm in self.state[0].observation.farms]
        return result[::-1] if self.reverse else result

    def run(self):
        while self.advance():
            pass
        return self.rewards()

    def snapshot(self):
        obs = self.state[0].observation
        return {
            "step": self.step, "day": obs.day, "hour": obs.hour,
            "farms": obs.farms,
            "privates": [state.observation.private for state in self.state],
            "market": obs.market, "town": obs.town,
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tape-a", required=True, type=Path)
    parser.add_argument("--tape-b", required=True, type=Path)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--steps", type=int, default=720)
    parser.add_argument("--step-mode", choices=("kaggle", "turns"), default="kaggle")
    parser.add_argument("--reverse-seats", action="store_true")
    parser.add_argument("--trim-hands", action="store_true")
    parser.add_argument("--trim-hands-a", action="store_true")
    parser.add_argument("--trim-hands-b", action="store_true")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--trace", type=Path)
    args = parser.parse_args()
    replay = PythonReplay(json.loads(args.tape_a.read_text()), json.loads(args.tape_b.read_text()), args.seed,
                          steps=args.steps, reverse=args.reverse_seats, trim_hands=args.trim_hands,
                          step_mode=args.step_mode, config=json.loads(args.config.read_text()) if args.config else None,
                          trim_hands_a=args.trim_hands_a, trim_hands_b=args.trim_hands_b)
    if args.trace:
        with args.trace.open("w") as f:
            f.write(json.dumps(replay.snapshot()) + "\n")
            while replay.advance():
                f.write(json.dumps(replay.snapshot()) + "\n")
    else:
        replay.run()
    print(json.dumps({"rewards": replay.rewards(), "errors": []}))


if __name__ == "__main__":
    main()
