#!/usr/bin/env python3
"""Reproduce the small terminal-action discovery screen; NEVER a promotion gate.

Requires the source checkout's three TOP49 replays and frozen B21. Preserves
candidate-only hand trimming: recorded opponents remain raw, as in
kaggriculture/research/screen_top49_all.py. Uses the unmodified Python interpreter.
"""
from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PORT = HERE.parent / "rust_port"
sys.path.insert(0, str(PORT / "tools"))
from export_tape import extract
from py_reference import PythonReplay
from terminal_salvage import plan_terminal

PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER")
CASES = [("Kenneth Alonso", 106178365), ("Mengfei Li", 106180186), ("elmo", 106180027)]
MODELS = ("control", "sell", "drop", "clear", "home", "harvest4", "harvest6", "harvest8")


def simple_patch(action, farm, private, step, model, last):
    if model == "control":
        return action
    if (step == last - 1 and model in ("clear", "home")) or step == last:
        seen = set()
        orders = []
        for order in action.get("market", [])[:10]:
            if order and order[0] == "SELL" and order[1] in PRODUCTS:
                orders.append(["SELL", order[1], 500])
                seen.add(order[1])
            else:
                orders.append(["PASS"])
        for product in PRODUCTS:
            if product not in seen and len(orders) < 10:
                orders.append(["SELL", product, 500])
        action["market"] = orders
    positions = [farm["farmer"], *farm["hands"]]
    acts = [action.get("farmer", ["PASS"]), *action.get("hands", [])]
    acts += [["PASS"] for _ in range(len(positions) - len(acts))]
    access = ((4, 4), (5, 4), (4, 5), (5, 5))
    for index, (pos, inv) in enumerate(zip(positions, private["inventories"])):
        if not any(inv.get(p, 0) > 0 for p in PRODUCTS):
            continue
        if step == last and model in ("drop", "clear", "home") and tuple(pos) in access:
            acts[index] = ["DROP"]
        if step == last - 1 and model == "home":
            target = min(access, key=lambda q: abs(q[0] - pos[0]) + abs(q[1] - pos[1]))
            dx, dy = target[0] - pos[0], target[1] - pos[1]
            if abs(dx) + abs(dy) == 1:
                acts[index] = ["EAST" if dx == 1 else "WEST" if dx == -1 else "SOUTH" if dy == 1 else "NORTH"]
    action["farmer"], action["hands"] = acts[0], acts[1:]
    return action


def play(base, replay, opponent_side, candidate_side, model):
    candidate = copy.deepcopy(base)
    stream = [frame[opponent_side].get("action") or {} for frame in replay["steps"][1:]]
    opponent = [stream, stream]
    game = PythonReplay(candidate, opponent, replay["info"]["seed"], steps=len(replay["steps"]),
                        reverse=candidate_side == 1, trim_hands=False, config=replay["configuration"])
    last = game.turns - 1
    while game.step < game.turns:
        step = game.step
        observation = dict(vars(game.state[candidate_side].observation))
        observation["step"] = step  # framework shares this field with both seats
        farm = game.state[0].observation.farms[candidate_side]
        index = min(step, len(base[candidate_side]) - 1)
        action = copy.deepcopy(base[candidate_side][index])
        action["hands"] = action.get("hands", [])[:len(farm["hands"])]
        if model.startswith("harvest"):
            action = plan_terminal(action, observation, game.env.configuration, int(model[7:]))
        elif step >= last - 1:
            action = simple_patch(action, farm, observation["private"], step, model, last)
        candidate[candidate_side][index] = action
        game.advance()
    return game.rewards()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-ref", default="unspecified; see file checksums")
    parser.add_argument("--output", type=Path, default=PORT / "work/terminal-probe.json")
    args = parser.parse_args()
    source = args.source_root.resolve()
    path = source / "kaggriculture_meta_lab/agents/current/agent_v9_b21_s16.py"
    base = extract(path)
    if base != extract(PORT / "reference/agent_v9_b21_s16.example.py"):
        raise ValueError("not the frozen B21 action data; do not silently compare a different baseline")
    reference = json.loads((source / "kaggriculture/research/V10_B21_RATING_FINALISTS_TOP49.json").read_text())["rows"]["control_b21s16"]
    rows = []
    hashes = {}
    for owner, episode in CASES:
        path = source / f"kaggriculture/top49_full/{episode}/replay.json.gz"
        hashes[str(episode)] = hashlib.sha256(path.read_bytes()).hexdigest()
        with gzip.open(path, "rt", encoding="utf8") as f:
            replay = json.load(f)
        if replay.get("module_version") != "1.32.7":
            raise ValueError("unvalidated engine version in replay")
        side = replay["info"]["TeamNames"].index(owner)
        for model in MODELS:
            values = [play(base, replay, side, ours, model) for ours in (0, 1)]
            row = {"owner": owner, "episode": episode, "model": model, "rewards": values,
                   "wins": sum(a > b for a, b in values),
                   "own_mean": sum(x[0] for x in values) / 2,
                   "margin_mean": sum(x[0] - x[1] for x in values) / 2}
            if model == "control":
                expected = next(x for x in reference if x["player"] == owner and x["episode"] == episode)
                if row["own_mean"] != expected["our_mean"] or row["margin_mean"] != expected["margin_mean"]:
                    raise AssertionError(f"control does not reproduce authoritative TOP49 row: {row}")
            rows.append(row)
            print(json.dumps(row), flush=True)
    report = {"source_ref": args.source_ref, "engine": "1.32.7", "discovery_only": True,
              "promotion": False, "independent_holdout": False, "games": len(rows) * 2,
              "replay_sha256": hashes, "rows": rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf8")


if __name__ == "__main__":
    main()
