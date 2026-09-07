#!/usr/bin/env python3
"""Open-loop, both-seat screening against selected full TOP49 trajectories."""
from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PASS = {"farmer": ["PASS"], "hands": [], "market": []}


def load_agent(path: Path):
    spec = importlib.util.spec_from_file_location("top49_candidate", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, "agent", getattr(module, "act", None))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", required=True)
    ap.add_argument("--player", required=True)
    ap.add_argument("--selection", type=Path, default=ROOT / "kaggriculture/research/top49_selected_episodes.json")
    ap.add_argument("--replays", type=Path, default=ROOT / "kaggriculture/top49_full")
    args = ap.parse_args()

    from kaggle_environments import make

    candidate = load_agent((ROOT / args.agent).resolve())
    selection = json.loads(args.selection.read_text(encoding="utf8"))
    row = next(row for row in selection["players"] if row["player"] == args.player)
    results = []
    for episode in row["episodes"]:
        with gzip.open(args.replays / str(episode) / "replay.json.gz", "rt") as stream:
            replay = json.load(stream)
        recorded_side = replay["info"]["TeamNames"].index(args.player)
        tape = [step[recorded_side].get("action") or PASS for step in replay["steps"]]

        def opponent(obs, config, tape=tape):
            return tape[min(int(obs.get("step", 0)) + 1, len(tape) - 1)]

        for candidate_side in (0, 1):
            config = dict(replay["configuration"])
            config["seed"] = replay["info"]["seed"]
            agents = [opponent, opponent]
            agents[candidate_side] = candidate
            env = make("kaggriculture", configuration=config)
            env.run(agents)
            ours = float(env.state[candidate_side].reward or 0)
            theirs = float(env.state[1 - candidate_side].reward or 0)
            results.append({"episode": episode, "side": candidate_side, "ours": ours,
                            "theirs": theirs, "win": ours > theirs})
            print(f"episode={episode} side={candidate_side} ours={ours:.0f} theirs={theirs:.0f} "
                  f"result={'WIN' if ours > theirs else 'LOSS'}")
    wins = sum(row["win"] for row in results)
    margins = [row["ours"] - row["theirs"] for row in results]
    summary = {
        "agent": args.agent, "opponent_player": args.player, "games": len(results),
        "wins": wins, "losses": len(results) - wins,
        "win_rate": wins / len(results),
        "our_mean": statistics.mean(row["ours"] for row in results),
        "opponent_mean": statistics.mean(row["theirs"] for row in results),
        "margin_mean": statistics.mean(margins), "margin_median": statistics.median(margins),
        "results": results,
    }
    print("SUMMARY_JSON=" + json.dumps(summary, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
