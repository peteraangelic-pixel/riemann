#!/usr/bin/env python3
"""Run one actual-framework match and persist compact daily farm telemetry."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from kaggle_environments import make
from kaggriculture_lab.agents import resolve


def farm_summary(observation: dict, seat: int) -> dict:
    farm = observation["farms"][seat]
    tiles = farm.get("tiles", []) or []
    kinds: Counter[str] = Counter()
    crops: Counter[str] = Counter()
    animals: Counter[str] = Counter()
    for row in tiles:
        for tile in row:
            if not isinstance(tile, dict):
                continue
            kinds[str(tile.get("kind"))] += 1
            if tile.get("crop"):
                crops[str(tile["crop"])] += 1
            if tile.get("animal"):
                animals[str(tile["animal"])] += 1
    private = observation.get("private", {}) or {}
    inventories = private.get("inventories", []) or []
    return {
        "money": farm.get("money"),
        "hands": len(farm.get("hands", []) or []),
        "quadrants": list(farm.get("unlocked_quadrants", []) or []),
        "crops": dict(sorted(crops.items())),
        "animals": dict(sorted(animals.items())),
        "structures": {k: kinds[k] for k in ("PASTURE", "COOP") if kinds[k]},
        "weeds": kinds["WEED"],
        "shed": dict(sorted((private.get("shed", {}) or {}).items())),
        "carried": int(sum(sum((inv or {}).values()) for inv in inventories)),
    }


def run(candidate: str, control: str, seed: int, candidate_seat: int) -> dict:
    agents = [resolve(candidate), resolve(control)]
    if candidate_seat:
        agents.reverse()
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run(agents)
    daily = []
    for step, states in enumerate(env.steps):
        if step % 24 != 23 and step != len(env.steps) - 1:
            continue
        row = {"step": step, "day": step // 24, "players": []}
        for seat, state in enumerate(states):
            obs = state.get("observation") or {}
            row["players"].append(farm_summary(obs, seat) if obs.get("farms") else {})
        daily.append(row)
    return {
        "seed": seed,
        "candidate_seat": candidate_seat,
        "status": [str(s.status) for s in env.state],
        "reward": [s.reward for s in env.state],
        "daily": daily,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--control", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    payload = {
        "candidate": args.candidate,
        "control": args.control,
        "games": [run(args.candidate, args.control, args.seed, seat) for seat in (0, 1)],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
