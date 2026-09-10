#!/usr/bin/env python3
"""Census market/production timing features from an extracted leader corpus."""
from __future__ import annotations
import argparse, json, statistics
from pathlib import Path


def analyze_team(folder: Path, manifest: dict) -> dict:
    team = manifest["team_name"]
    rows = []
    for item in manifest["selected_episodes"]:
        replay = json.loads((folder / item["file"]).read_text(encoding="utf-8"))
        names = replay["info"]["TeamNames"]
        if team not in names:
            continue
        seat = names.index(team)
        r = {"buy": 0, "sell": 0, "hire": 0, "animals": 0, "fertilizer": 0,
             "first_sell": None, "first_land": None}
        for step_no, step in enumerate(replay["steps"]):
            action = step[seat].get("action", {})
            for order in action.get("market", []) or []:
                if not order:
                    continue
                kind = order[0]
                if kind == "SELL":
                    r["sell"] += 1
                    r["first_sell"] = step_no if r["first_sell"] is None else r["first_sell"]
                elif kind.startswith("BUY"):
                    r["buy"] += 1
                    if kind == "BUY_LAND":
                        r["first_land"] = step_no if r["first_land"] is None else r["first_land"]
                elif kind == "HIRE":
                    r["hire"] += 1
                if len(order) > 1 and order[1] in {"COW", "SHEEP", "GOOSE"}:
                    r["animals"] += 1
                if len(order) > 1 and order[1] == "FERTILIZER":
                    r["fertilizer"] += 1
        rows.append(r)
    keys = ("buy", "sell", "hire", "animals", "fertilizer", "first_sell", "first_land")
    return {"rank": manifest["rank"], "team": team,
            "leaderboard_score": manifest["leaderboard_score"], "replays": len(rows),
            **{k: statistics.mean(r[k] for r in rows if r[k] is not None) if any(r[k] is not None for r in rows) else None for k in keys}}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("corpus", type=Path, help="extracted corpus directory")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = []
    for manifest_path in sorted(args.corpus.glob("*/manifest.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        result.append(analyze_team(manifest_path.parent, manifest))
    result.sort(key=lambda x: x["rank"])
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
