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
    cases = [(0, 1), (0, 2), (0, 24), (0, 25), (0, 721)] + [(seed, 720) for seed in (0, 1, -1, 2**32)]
    for seed, steps in cases:
        env = core.make("kaggriculture", configuration={"episodeSteps": steps, "seed": seed})
        env.run([agent, agent])
        actual = [state.reward for state in env.state]
        replay = PythonReplay(tape, tape, seed, steps=steps, trim_hands=True)
        assert bits(replay.run()) == bits(actual)
        obs = env.state[0].observation
        core_snapshot = {"step": obs.step, "day": obs.day, "hour": obs.hour, "farms": obs.farms, "privates": [s.observation.private for s in env.state], "market": obs.market, "town": obs.town}
        diff = difference(core_snapshot, replay.snapshot())
        assert not diff, diff
        if not args.python_only:
            output = subprocess.check_output([str(args.binary.resolve()), "--tape-a", str(path), "--tape-b", str(path), "--seed", str(seed), "--steps", str(steps), "--trim-hands"], text=True)
            rust = json.loads(output)
            assert not rust["errors"] and bits(rust["rewards"]) == bits(actual), (seed, steps, rust, actual)
        assert len(env.steps) == replay.turns + 1
        records.append({"seed": seed, "episodeSteps": steps, "action_turns": replay.turns, "rewards": actual})
    report = {"status": "passed", "actual_framework": "kaggle-environments==1.32.7", "wheel_sha256": WHEEL_SHA256, "rust_checked": not args.python_only, "cases": records}
    (ROOT / "work/framework-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
