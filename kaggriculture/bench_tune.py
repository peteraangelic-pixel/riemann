"""Tuning bench: monkeypatch agent module constants and measure several configs."""
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from kaggle_environments import make  # noqa: E402

spec = importlib.util.spec_from_file_location("ag", HERE / "agent.py")
ag = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ag)

PASSIVE = {"farmer": ["PASS"], "hands": [], "market": []}


def game_self(seed):
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([ag.act, ag.act])
    return env.state[0].reward


def game_pass(seed):
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([ag.act, PASSIVE])
    return env.state[0].reward


def game_rand(seed):
    from simulate import randomish
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([ag.act, randomish])
    return env.state[0].reward


import argparse
ap = argparse.ArgumentParser()
ap.add_argument("--opp", choices=["pass", "self", "random"], nargs="+", default=["pass", "self"])
args = ap.parse_args()

# (label, kwargs)
def mc(n):  # melon cell list helper
    return {"MELON_CELLS": [(x, 0) for x in range(n)]}

configs = [
    ("m4 k0.7 noSE (default)", {"CARROT_KAPPA": 0.7, **mc(4)}),
    ("m4 k0.7 SE on", {"CARROT_KAPPA": 0.7, **mc(4), "SELL_BUY": True}),
]
seeds = [1, 2, 3, 5, 7, 11, 13, 21, 22, 23]
fns = {"pass": game_pass, "self": game_self, "random": game_rand}
print(f"{'config':24s} " + " | ".join(args.opp))
for label, kw in configs:
    for k, v in kw.items():
        setattr(ag, k, v)
    out = []
    for opp in args.opp:
        r = [fns[opp](s) for s in seeds]
        out.append(f"{opp} avg {sum(r)/len(r):6.0f} ({min(r):.0f}-{max(r):.0f})")
    print(f"{label:24s} " + " | ".join(out), flush=True)
