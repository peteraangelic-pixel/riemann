#!/usr/bin/env python3
"""Optional online smoke test against the actual pinned Kaggle core + agent.

Only requests/jsonschema are required. Extract a verified wheel, import its real
core/agent/utils and real game, without running the environment auto-discovery
__init__ (which otherwise imports unrelated heavyweight games).
No core/agent/game-rule function is stubbed. The wrapper adapter and Rust are
compared against the actual Environment.run([example_agent, example_agent]).
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib
import json
from pathlib import Path
import runpy
import subprocess
import sys
from types import ModuleType
import urllib.request
import zipfile

from check import bits, difference, verify_sources
from export_tape import DEFAULT_AGENT, extract, write_tape
from py_reference import PythonReplay

ROOT = Path(__file__).resolve().parents[1]
WHEEL_URL = "https://files.pythonhosted.org/packages/f1/a3/16f3211bec7d5b594619e4f53400111783cc0c1575343bef006485d02f64/kaggle_environments-1.32.7-py3-none-any.whl"
WHEEL_SHA256 = "2a1bb862ad2d6463080f80f6a766f46d94b53fd57168cfeddb9857fc3dbc4c8f"


def load_framework(wheel, directory):
    digest = hashlib.sha256()
    with wheel.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            digest.update(chunk)
    if digest.hexdigest() != WHEEL_SHA256:
        raise ValueError("wheel SHA-256 mismatch; refusing to execute unverified code")
    with zipfile.ZipFile(wheel) as archive:
        names = [name for name in archive.namelist() if name.startswith("kaggle_environments/") and name.count("/") == 1 and name.endswith((".py", ".json"))]
        names += ["kaggle_environments/envs/kaggriculture/kaggriculture.py", "kaggle_environments/envs/kaggriculture/kaggriculture.json"]
        for name in names:
            archive.extract(name, directory)
    package_path = directory / "kaggle_environments"
    assert (package_path / "envs/kaggriculture/kaggriculture.py").read_bytes() == (ROOT / "reference/kaggriculture_sim.py").read_bytes()
    assert (package_path / "envs/kaggriculture/kaggriculture.json").read_bytes() == (ROOT / "reference/kaggriculture_config.json").read_bytes()
    namespace = ModuleType("kaggle_environments")
    namespace.__path__ = [str(package_path)]
    namespace.__version__ = "1.32.7"
    sys.modules["kaggle_environments"] = namespace
    core = importlib.import_module("kaggle_environments.core")
    sim = importlib.import_module("kaggle_environments.envs.kaggriculture.kaggriculture")
    core.register("kaggriculture", {"specification": sim.specification, "interpreter": sim.interpreter, "renderer": sim.renderer, "html_renderer": sim.html_renderer, "agents": sim.agents})
    return core


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path)
    parser.add_argument("--download", action="store_true", help="download the 60 MB pinned wheel (no Kaggle package dependencies)")
    parser.add_argument("--binary", type=Path, default=ROOT / "target/release/kg_sim")
    parser.add_argument("--python-only", action="store_true", help="validate the adapter only, without a Rust binary")
    args = parser.parse_args()
    if args.wheel is None and not args.download:
        parser.error("supply --wheel or explicitly allow --download")
    work = ROOT / "work/framework"
    work.mkdir(parents=True, exist_ok=True)
    wheel = args.wheel or work / "kaggle_environments-1.32.7-py3-none-any.whl"
    if not wheel.exists() and args.download:
        with urllib.request.urlopen(WHEEL_URL, timeout=120) as response, wheel.open("wb") as f:
            while chunk := response.read(1024 * 1024):
                f.write(chunk)
    verify_sources()
    core = load_framework(wheel, work / "upstream")
    agent = runpy.run_path(str(DEFAULT_AGENT))["agent"]
    tape = extract()
    path = work / "example.json"
    write_tape(path, tape)
    records = []
    cases = [(0, 1, {}), (0, 2, {}), (0, 24, {}), (0, 25, {}), (0, 721, {})]
    cases += [(seed, 720, {}) for seed in (0, 1, -1, 2**32)]
    cases += [(0, 25, overrides) for overrides in [
        {"marketParams": {"default": {"WHEAT": {"base": 900}}, "WHEAT": {"base": 40}}},
        {"marketParams": {"default": {}}},
        {"startingMoney": 5000.0, "boardSize": 10.0, "turnsPerDay": 6.0,
         "shedCapacity": 3.0, "farmHandCostMult": 0.0, "maxMarketOrdersPerTurn": 2.0},
    ]]

    def compare_core_state(env, replay):
        obs = env.state[0].observation
        core_snapshot = {"step": obs.step, "day": obs.day, "hour": obs.hour,
                         "farms": obs.farms, "privates": [s.observation.private for s in env.state],
                         "market": obs.market, "town": obs.town}
        diff = difference(core_snapshot, replay.snapshot())
        assert not diff, diff
        assert len(env.steps) == replay.turns + 1

    for seed, steps, overrides in cases:
        env = core.make("kaggriculture", configuration={**overrides, "episodeSteps": steps, "seed": seed})
        env.run([agent, agent])
        actual = [state.reward for state in env.state]
        replay = PythonReplay(tape, tape, seed, steps=steps, trim_hands=True, config=overrides)
        assert bits(replay.run()) == bits(actual)
        compare_core_state(env, replay)
        if not args.python_only:
            command = [str(args.binary.resolve()), "--tape-a", str(path), "--tape-b", str(path), "--seed", str(seed), "--steps", str(steps), "--trim-hands"]
            if overrides:
                cfg_path = work / "overrides.json"
                cfg_path.write_text(json.dumps(overrides))
                command += ["--config", str(cfg_path)]
            rust = json.loads(subprocess.check_output(command, text=True))
            assert not rust["errors"] and bits(rust["rewards"]) == bits(actual), (seed, steps, rust, actual)
        records.append({"seed": seed, "episodeSteps": steps, "action_turns": replay.turns, "rewards": actual, "overrides": overrides})

    # Independently prove mixed wrapper/raw semantics using actual callable
    # agents in Environment.run. Their cash differs, not just a trace flag.
    actions = [{} for _ in range(50)]
    actions[0] = {"market": [["BUY_SEED", "WHEAT", 1]]}
    actions[1] = {"farmer": ["PLANT", "WHEAT"], "hands": [["PLANT", "WHEAT"]]}
    actions[2] = {"farmer": ["WATER"]}
    actions[24] = {"farmer": ["WATER"]}
    actions[48] = {"farmer": ["HARVEST"]}
    actions[49] = {"farmer": ["DROP"], "market": [["SELL", "WHEAT", 100]]}
    phantom = [actions, actions]
    phantom_path = work / "phantom.json"
    write_tape(phantom_path, phantom)

    def tape_agent(trim):
        def play(observation, configuration):
            action = copy.deepcopy(phantom[observation.player][min(observation.step, 49)])
            if trim:
                action["hands"] = action.get("hands", [])[:len(observation.farms[observation.player]["hands"])]
            return action
        return play

    for a_trim, b_trim in [(True, False), (False, True)]:
        for reverse in (False, True):
            players = [tape_agent(a_trim), tape_agent(b_trim)]
            if reverse:
                players.reverse()
            env = core.make("kaggriculture", configuration={"episodeSteps": 51, "seed": 17})
            env.run(players)
            actual = [state.reward for state in env.state]
            if reverse:
                actual.reverse()
            replay = PythonReplay(phantom, phantom, 17, steps=51, reverse=reverse, trim_hands_a=a_trim, trim_hands_b=b_trim)
            assert bits(replay.run()) == bits(actual)
            assert (actual[0] > 2990) == a_trim and (actual[1] > 2990) == b_trim
            compare_core_state(env, replay)
            if not args.python_only:
                command = [str(args.binary.resolve()), "--tape-a", str(phantom_path), "--tape-b", str(phantom_path), "--seed", "17", "--steps", "51"]
                command += ["--trim-hands-a"] if a_trim else ["--trim-hands-b"]
                if reverse:
                    command += ["--reverse-seats"]
                rust = json.loads(subprocess.check_output(command, text=True))
                assert not rust["errors"] and bits(rust["rewards"]) == bits(actual)
            records.append({"seed": 17, "episodeSteps": 51, "action_turns": 50,
                            "trim_hands_a": a_trim, "trim_hands_b": b_trim,
                            "reverse": reverse, "rewards": actual})
    report = {"status": "passed", "actual_framework": "kaggle-environments==1.32.7", "wheel_sha256": WHEEL_SHA256, "rust_checked": not args.python_only, "cases": records}
    (ROOT / "work/framework-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
