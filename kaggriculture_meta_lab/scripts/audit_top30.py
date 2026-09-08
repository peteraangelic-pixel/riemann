#!/usr/bin/env python3
"""Validate an extracted TOP30 replay corpus and write a compact inventory.

This deliberately audits the raw Kaggle replay JSON independently of any
precomputed per_replay reports. It does not execute the bundled analysis script.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def _load(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def audit(root: Path, archive: Path | None = None) -> dict[str, Any]:
    manifest_path = root / "manifest.json"
    manifest = _load(manifest_path)
    teams = manifest.get("teams")
    _require(manifest.get("competition") == "kaggriculture", "wrong competition")
    _require(manifest.get("requested_top_n") == 30, "manifest is not TOP30")
    _require(manifest.get("replays_per_team") == 5, "expected five slots per team")
    _require(isinstance(teams, list) and len(teams) == 30, "expected 30 teams")
    _require([team.get("rank") for team in teams] == list(range(1, 31)), "bad ranks")

    folders = [team.get("folder") for team in teams]
    _require(len(set(folders)) == 30 and all(isinstance(x, str) for x in folders), "bad folders")
    actual_dirs = {p.name for p in root.iterdir() if p.is_dir()} - {"per_replay"}
    _require(actual_dirs == set(folders), "player folders do not match manifest")

    slots: list[dict[str, Any]] = []
    hashes_by_episode: dict[int, set[str]] = defaultdict(set)
    raw_paths: set[str] = set()
    status_counts: Counter[str] = Counter()
    seeds: set[int] = set()
    step_counts: Counter[int] = Counter()
    reward_min = math.inf
    reward_max = -math.inf

    for team in teams:
        folder = root / team["folder"]
        local_manifest = _load(folder / "manifest.json")
        _require(local_manifest == team, f"local manifest mismatch: {team['folder']}")
        episodes = team.get("selected_episodes")
        _require(isinstance(episodes, list) and len(episodes) == 5, f"bad slots: {team['folder']}")
        expected_files = {entry.get("file") for entry in episodes}
        actual_files = {p.name for p in folder.glob("replay_*.json")}
        _require(actual_files == expected_files, f"raw file mismatch: {team['folder']}")

        for slot, entry in enumerate(episodes, 1):
            path = folder / entry["file"]
            raw = _load(path)
            episode_id = entry.get("episode_id")
            _require(raw.get("name") == "kaggriculture", f"bad replay name: {path}")
            _require(raw.get("info", {}).get("EpisodeId") == episode_id, f"episode mismatch: {path}")
            seed = raw.get("info", {}).get("seed")
            _require(isinstance(seed, int) and not isinstance(seed, bool), f"bad seed: {path}")
            steps = raw.get("steps")
            _require(isinstance(steps, list) and steps, f"missing steps: {path}")
            _require(raw.get("configuration", {}).get("episodeSteps") == len(steps), f"horizon mismatch: {path}")
            _require(all(isinstance(step, list) and len(step) == 2 for step in steps), f"bad step rows: {path}")
            rewards = raw.get("rewards")
            statuses = raw.get("statuses")
            _require(isinstance(rewards, list) and len(rewards) == 2, f"bad rewards: {path}")
            _require(all(isinstance(x, (int, float)) and math.isfinite(x) for x in rewards), f"non-finite rewards: {path}")
            _require(statuses == [agent.get("status") for agent in steps[-1]], f"final status mismatch: {path}")
            _require(rewards == [agent.get("reward") for agent in steps[-1]], f"final reward mismatch: {path}")
            _require(all(status == "DONE" for status in statuses), f"failed episode: {path}: {statuses}")
            _require(all(isinstance(agent.get("action"), dict) for step in steps for agent in step), f"bad action: {path}")

            digest = _sha256(path)
            hashes_by_episode[episode_id].add(digest)
            rel = path.relative_to(root).as_posix()
            raw_paths.add(rel)
            seeds.add(seed)
            step_counts[len(steps)] += 1
            status_counts.update(statuses)
            reward_min = min(reward_min, *rewards)
            reward_max = max(reward_max, *rewards)
            slots.append({
                "rank": team["rank"],
                "team": team["team_name"],
                "slot": slot,
                "episode_id": episode_id,
                "submission_id": entry.get("submission_id"),
                "seed": seed,
                "steps": len(steps),
                "rewards": rewards,
                "statuses": statuses,
                "file": rel,
                "bytes": path.stat().st_size,
                "sha256": digest,
            })

    conflicting = {str(k): sorted(v) for k, v in hashes_by_episode.items() if len(v) != 1}
    _require(not conflicting, f"same episode has conflicting raw bytes: {conflicting}")
    _require(len(slots) == 150 and len(raw_paths) == 150, "expected 150 selected raw files")

    report_dir = root / "per_replay"
    reports = sorted(report_dir.glob("*.json"))
    report_sources: list[str] = []
    report_parser_counts: Counter[str] = Counter()
    reports_with_scores = 0
    reports_with_winner = 0
    report_raw_count = 0
    report_manifest_count = 0
    for path in reports:
        report = _load(path)
        source = report.get("replay")
        _require(isinstance(source, str) and source.startswith("TOP30/"), f"bad analysis source: {path}")
        report_sources.append(source.removeprefix("TOP30/"))
        report_parser_counts[str(report.get("parser"))] += 1
        reports_with_scores += bool(report.get("final_scores"))
        reports_with_winner += report.get("winner") is not None
        report_manifest_count += source.endswith("/manifest.json")
        report_raw_count += "/replay_" in source
    expected_report_sources = raw_paths | {f"{folder}/manifest.json" for folder in folders}
    _require(len(reports) == 180, "expected 180 per_replay reports")
    _require(set(report_sources) == expected_report_sources, "analysis reports do not cover source files exactly")
    _require(len(report_sources) == len(set(report_sources)), "duplicate analysis source")

    unique_episode_ids = sorted(hashes_by_episode)
    result: dict[str, Any] = {
        "format": "kaggriculture-top30-audit-v1",
        "source_manifest": {
            "sha256": _sha256(manifest_path),
            "generated_at_utc": manifest.get("generated_at_utc"),
            "selection_rule": manifest.get("selection_rule"),
        },
        "archive": None,
        "summary": {
            "teams": 30,
            "selected_slots": len(slots),
            "raw_files": len(raw_paths),
            "unique_episodes": len(unique_episode_ids),
            "duplicate_slots": len(slots) - len(unique_episode_ids),
            "unique_seeds": len(seeds),
            "step_counts": {str(k): v for k, v in sorted(step_counts.items())},
            "status_counts": dict(sorted(status_counts.items())),
            "reward_min": reward_min,
            "reward_max": reward_max,
            "analysis_reports": len(reports),
            "analysis_raw_reports": report_raw_count,
            "analysis_manifest_reports": report_manifest_count,
            "analysis_parser_counts": dict(sorted(report_parser_counts.items())),
            "analysis_reports_with_final_scores": reports_with_scores,
            "analysis_reports_with_winner": reports_with_winner,
        },
        "teams": [{
            "rank": team["rank"],
            "team_id": team["team_id"],
            "team_name": team["team_name"],
            "leaderboard_score": team["leaderboard_score"],
            "folder": team["folder"],
        } for team in teams],
        "slots": slots,
    }
    if archive is not None:
        result["archive"] = {
            "file": archive.name,
            "bytes": archive.stat().st_size,
            "sha256": _sha256(archive),
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, help="extracted TOP30 directory")
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.root, args.archive)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
