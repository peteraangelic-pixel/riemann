#!/usr/bin/env python3
"""Build immutable standalone tape candidates from selected TOP49 replays."""
from __future__ import annotations

import argparse
import base64
import gzip
import json
import re
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PASS = {"farmer": ["PASS"], "hands": [], "market": []}


def slug(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return value or "delayed28"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selection", type=Path, default=ROOT / "kaggriculture/research/top49_selected_episodes.json")
    ap.add_argument("--replays", type=Path, default=ROOT / "kaggriculture/top49_full")
    ap.add_argument("--output", type=Path, default=ROOT / "kaggriculture/v9_candidates")
    ap.add_argument("--player", action="append", default=["我都先道歉", "SJY321"])
    args = ap.parse_args()
    selected = json.loads(args.selection.read_text(encoding="utf8"))
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = []
    for player in args.player:
        row = next(row for row in selected["players"] if row["player"] == player)
        for index, episode in enumerate(row["episodes"], 1):
            replay_path = args.replays / str(episode) / "replay.json.gz"
            with gzip.open(replay_path, "rt") as stream:
                replay = json.load(stream)
            side = replay["info"]["TeamNames"].index(player)
            # Kaggle replay step 0 is the initial state. ACTIONS[0] is the
            # action attached to replay step 1; pad the 720th call with PASS.
            actions = [(step[side].get("action") or PASS) for step in replay["steps"][1:]]
            actions.append(PASS)
            payload = base64.b85encode(zlib.compress(json.dumps(actions, separators=(",", ":")).encode(), 9)).decode()
            name = f"agent_v9_third_{slug(player)}_{index:02d}"
            path = args.output / f"{name}.py"
            path.write_text(
                f'''"""V9 third-policy candidate reconstructed from {player}, episode {episode}."""\n'''
                "import base64, copy, json, zlib\n"
                "def _d(x): return json.loads(zlib.decompress(base64.b85decode(x)).decode())\n"
                f"ACTIONS = _d({payload!r})\n"
                f"SOURCE_PLAYER = {player!r}\nSOURCE_EPISODE = {episode}\n"
                "def act(observation, configuration):\n"
                "    player = int(observation.get('player', 0))\n"
                "    step = min(int(observation.get('step', 0)), len(ACTIONS) - 1)\n"
                "    action = copy.deepcopy(ACTIONS[step])\n"
                "    farms = observation.get('farms') or []\n"
                "    hands = farms[player].get('hands') or [] if player < len(farms) else []\n"
                "    action['hands'] = action.get('hands', [])[:len(hands)]\n"
                "    return action\n"
                "def agent(observation, configuration): return act(observation, configuration)\n",
                encoding="utf8",
            )
            manifest.append({"name": name, "path": str(path.relative_to(ROOT)), "source_player": player,
                             "source_episode": episode, "source_side": side, "actions": len(actions)})
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    print(f"built {len(manifest)} candidates in {args.output}")


if __name__ == "__main__":
    main()
