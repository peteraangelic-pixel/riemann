"""Summarize every collected Kaggriculture public replay.

Reads compressed telemetry from online/<episode>/ and prints one TSV row per
match with submission ref, result, money, opponent and peak economy. This is
kept dependency-free so it can run locally and in GitHub Actions.
"""
from __future__ import annotations

import collections
import gzip
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUR_TEAM = "Lauresowe 3D"
ANIMALS = ("GOOSE", "COW", "SHEEP")


def metadata(path: Path) -> dict[str, str]:
    return dict(line.split("=", 1) for line in path.read_text().splitlines() if "=" in line)


def summarize(replay_path: Path) -> dict:
    with gzip.open(replay_path, "rt") as stream:
        replay = json.load(stream)
    names = replay["info"]["TeamNames"]
    ours = names.index(OUR_TEAM)
    opponent = 1 - ours
    peak: collections.Counter[str] = collections.Counter()
    sales: collections.Counter[str] = collections.Counter()

    for step in replay["steps"]:
        state = step[opponent]
        action = state.get("action") or {}
        objects: collections.Counter[str] = collections.Counter()
        for row in state["observation"]["farms"][opponent]["tiles"]:
            for tile in row:
                if not isinstance(tile, dict):
                    continue
                key = tile.get("crop") if tile.get("kind") == "PLANT" else tile.get("animal") or tile.get("kind")
                objects[key] += 1
        for key, value in objects.items():
            peak[key] = max(peak[key], value)
        for order in action.get("market") or []:
            if order and order[0] == "SELL" and len(order) > 2:
                sales[order[1]] += int(order[2])

    episode_dir = replay_path.parent
    meta = metadata(episode_dir / "metadata.txt")
    our_money = replay["rewards"][ours]
    opponent_money = replay["rewards"][opponent]
    return {
        "episode": meta.get("episode_id", episode_dir.name),
        "submission": meta.get("submission_ref", "?"),
        "result": "WIN" if our_money > opponent_money else "LOSS" if our_money < opponent_money else "TIE",
        "our_money": int(our_money),
        "opponent": names[opponent],
        "opponent_money": int(opponent_money),
        "animals": sum(peak[name] for name in ANIMALS),
        "geese": peak["GOOSE"],
        "cows": peak["COW"],
        "sheep": peak["SHEEP"],
        "strawberries": peak["STRAWBERRY"],
        "melons": peak["MELON"],
        "sold_eggs": sales["EGG"],
        "sold_milk": sales["MILK"],
        "sold_wool": sales["WOOL"],
        "sold_fertilizer": sales["FERTILIZER"],
    }


def main() -> None:
    rows = [summarize(path) for path in sorted((HERE / "online").glob("*/replay.json.gz"))]
    columns = [
        "episode", "submission", "result", "our_money", "opponent", "opponent_money",
        "animals", "geese", "cows", "sheep", "strawberries", "melons",
        "sold_eggs", "sold_milk", "sold_wool", "sold_fertilizer",
    ]
    print("\t".join(columns))
    for row in rows:
        print("\t".join(str(row[column]) for column in columns))

    print("\nSUMMARY BY SUBMISSION")
    for submission in sorted({row["submission"] for row in rows}):
        group = [row for row in rows if row["submission"] == submission]
        wins = sum(row["result"] == "WIN" for row in group)
        losses = sum(row["result"] == "LOSS" for row in group)
        print(
            f"{submission}: games={len(group)} W-L={wins}-{losses} "
            f"our_avg={sum(row['our_money'] for row in group) / len(group):.1f} "
            f"opponent_avg={sum(row['opponent_money'] for row in group) / len(group):.1f}"
        )


if __name__ == "__main__":
    main()
