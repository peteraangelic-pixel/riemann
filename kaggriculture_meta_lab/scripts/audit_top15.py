#!/usr/bin/env python3
"""Fail-closed audit of the per-team TOP15 Kaggriculture replay corpus."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def load(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def audit(root: Path, archive: Path | None = None) -> dict[str, Any]:
    manifest_paths = sorted(root.glob("*/manifest.json"))
    require(len(manifest_paths) == 15, "expected exactly 15 per-team manifests")
    loaded = [(path, load(path)) for path in manifest_paths]
    for path, team in loaded:
        require(team.get("folder") == path.parent.name,
                f"folder identity mismatch: {path}")
    teams = [team for _, team in loaded]
    teams.sort(key=lambda team: int(team["rank"]))
    require([int(team["rank"]) for team in teams] == list(range(1, 16)), "bad TOP15 ranks")

    folders = [team.get("folder") for team in teams]
    require(all(isinstance(folder, str) for folder in folders), "bad folder field")
    require(len(set(folders)) == 15, "duplicate folder field")
    require({path.name for path in root.iterdir() if path.is_dir()} == set(folders),
            "corpus directories do not match manifests")

    slots: list[dict[str, Any]] = []
    paths: set[str] = set()
    hashes_by_episode: dict[int, set[str]] = defaultdict(set)
    seed_counts: Counter[int] = Counter()
    status_counts: Counter[str] = Counter()
    submission_counts: Counter[int] = Counter()
    self_plays = 0

    for team in teams:
        folder = root / team["folder"]
        active = team.get("active_submissions")
        require(isinstance(active, list) and active, f"missing active submissions: {team['folder']}")
        active_ids = {int(item["submission_id"]) for item in active}
        require(len(active_ids) == len(active), f"duplicate active submission: {team['folder']}")
        episodes = team.get("selected_episodes")
        require(isinstance(episodes, list) and len(episodes) == 7,
                f"expected seven selected episodes: {team['folder']}")
        expected = {entry.get("file") for entry in episodes}
        require(len(expected) == 7 and all(isinstance(name, str) for name in expected),
                f"bad replay filenames: {team['folder']}")
        actual = {path.name for path in folder.glob("replay_*.json")}
        require(actual == expected, f"raw replay set mismatch: {team['folder']}")

        for slot, entry in enumerate(episodes, 1):
            path = folder / entry["file"]
            replay = load(path)
            episode_id = int(entry["episode_id"])
            submission_id = int(entry["submission_id"])
            require(submission_id in active_ids, f"inactive selected submission: {path}")
            require(replay.get("name") == "kaggriculture", f"wrong replay game: {path}")
            info = replay.get("info", {})
            require(info.get("EpisodeId") == episode_id, f"episode mismatch: {path}")
            seed = info.get("seed")
            require(isinstance(seed, int) and not isinstance(seed, bool),
                    f"missing integer replay seed (no fallback allowed): {path}")
            names = info.get("TeamNames")
            matching_seats = [index for index, name in enumerate(names or [])
                              if name == team["team_name"]]
            require(len(names or []) == 2 and len(matching_seats) in (1, 2),
                    f"cannot identify selected team: {path}: {names}")
            self_play = matching_seats == [0, 1]
            self_plays += int(self_play)

            steps = replay.get("steps")
            require(isinstance(steps, list) and steps, f"missing steps: {path}")
            require(replay.get("configuration", {}).get("episodeSteps") == len(steps),
                    f"replay horizon mismatch: {path}")
            require(all(isinstance(row, list) and len(row) == 2 for row in steps),
                    f"bad step rows: {path}")
            require(all(isinstance(agent.get("action"), dict) for row in steps for agent in row),
                    f"missing recorded action: {path}")
            rewards = replay.get("rewards")
            statuses = replay.get("statuses")
            require(isinstance(rewards, list) and len(rewards) == 2 and
                    all(isinstance(value, (int, float)) and math.isfinite(value) for value in rewards),
                    f"bad final rewards: {path}")
            require(statuses == [agent.get("status") for agent in steps[-1]],
                    f"final status mismatch: {path}")
            require(rewards == [agent.get("reward") for agent in steps[-1]],
                    f"final reward mismatch: {path}")
            require(statuses == ["DONE", "DONE"], f"failed episode: {path}: {statuses}")

            digest = sha256(path)
            hashes_by_episode[episode_id].add(digest)
            relative = path.relative_to(root).as_posix()
            require(relative not in paths, f"duplicate selected path: {relative}")
            paths.add(relative)
            seed_counts[seed] += 1
            status_counts.update(statuses)
            submission_counts[submission_id] += 1
            slots.append({
                "rank": int(team["rank"]), "team": team["team_name"], "slot": slot,
                "episode_id": episode_id, "submission_id": submission_id, "seed": seed,
                "team_seats": matching_seats, "self_play": self_play, "steps": len(steps),
                "rewards": rewards, "statuses": statuses, "file": relative,
                "bytes": path.stat().st_size, "sha256": digest,
            })

    conflicting = {str(key): sorted(values) for key, values in hashes_by_episode.items()
                   if len(values) != 1}
    require(not conflicting, f"same episode has conflicting raw bytes: {conflicting}")
    require(len(slots) == len(paths) == 105, "expected 105 selected replay paths")

    manifest_digest = hashlib.sha256()
    for path in manifest_paths:
        manifest_digest.update(path.relative_to(root).as_posix().encode())
        manifest_digest.update(path.read_bytes())
    result: dict[str, Any] = {
        "format": "kaggriculture-top15-audit-v1",
        "source_manifests_sha256": manifest_digest.hexdigest(),
        "archive": None,
        "summary": {
            "teams": 15, "selected_slots": len(slots), "raw_files": len(paths),
            "unique_episodes": len(hashes_by_episode),
            "duplicate_episode_slots": len(slots) - len(hashes_by_episode),
            "unique_seeds": len(seed_counts), "zero_seed_slots": seed_counts[0],
            "self_play_slots": self_plays, "unique_submissions": len(submission_counts),
            "status_counts": dict(sorted(status_counts.items())),
        },
        "teams": [{
            "rank": int(team["rank"]), "team_id": team["team_id"],
            "team_name": team["team_name"], "leaderboard_score": team["leaderboard_score"],
            "folder": team["folder"],
        } for team in teams],
        "slots": slots,
    }
    if archive is not None:
        result["archive"] = {"file": archive.name, "bytes": archive.stat().st_size,
                             "sha256": sha256(archive)}
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, help="extracted per-team TOP15 directory")
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rendered = json.dumps(audit(args.root.resolve(), args.archive), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
