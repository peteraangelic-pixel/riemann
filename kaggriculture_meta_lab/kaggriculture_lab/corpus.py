"""Open-loop replay corpus benchmark (the V7-style check, packaged).

For each collected episode replay (.json or .json.gz), the candidate is run
against the *recorded actions* of its real opponent, in the original seed and
seat. With the submitted agent this reproduces the Kaggle result; with a
candidate it measures the change against realistic market pressure.

This is open-loop (the tape does not react), so use it for physical/market
regression and elite benchmarking - and use ``tournament`` for adaptive win-rate.

Corpus layout (each episode is a directory):
    <corpus>/<episode_id>/replay.json.gz
    <corpus>/<episode_id>/metadata.txt        (optional, key=value lines)
"""
from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any, Iterator

from .agents import _find_steps  # reuse tolerant step finder


def iter_episodes(corpus_dir: Path) -> Iterator[Path]:
    corpus_dir = Path(corpus_dir)
    if not corpus_dir.exists():
        return
    for replay in sorted(corpus_dir.rglob("replay.json*")):
        yield replay
    # also tolerate flat dumps
    for replay in sorted(corpus_dir.rglob("*.json*")):
        if replay.name.startswith("replay"):
            continue
        if "episode" in replay.name.lower() or replay.stem.isdigit():
            yield replay


def load_replay(path: Path) -> dict:
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def tape_agent(steps: list, seat: int):
    """Build an open-loop callable that replays ``seat``'s recorded actions."""
    tape = []
    for row in steps:
        action = {"farmer": ["PASS"], "hands": [], "market": []}
        if isinstance(row, list) and seat < len(row) and isinstance(row[seat], dict):
            a = row[seat].get("action")
            if isinstance(a, dict):
                action = a
        tape.append(action)

    def _agent(obs: dict, *a: Any, **k: Any) -> dict:
        step = int(obs.get("step", 0) or 0)
        act = tape[min(step, len(tape) - 1)] if tape else {"farmer": ["PASS"], "hands": [], "market": []}
        return {"farmer": list(act.get("farmer", ["PASS"])),
                "hands": [list(h) for h in act.get("hands", [])],
                "market": [list(o) for o in act.get("market", [])]}

    return _agent


def _team_seat(replay: dict, team_substrings: tuple[str, ...]) -> int | None:
    """Find the seat whose team name contains any substring (e.g. our team)."""
    names = replay.get("info", {}).get("TeamNames")
    if not names:
        return None
    for i, name in enumerate(names):
        if any(s.lower() in str(name).lower() for s in team_substrings):
            return i
    return None


def score_episode(candidate_fn, replay: dict, our_seat: int) -> dict[str, Any]:
    """Run candidate vs the recorded opponent in the episode's seed/seat.

    Returns a dict with the candidate's score, opponent replay score and outcome.
    The environment seed is read from the replay configuration so the map/market
    matches the original game.
    """
    from .engine import play_game

    steps = _find_steps(replay)
    if not steps:
        return {"error": "no steps in replay"}
    opp_seat = 1 - our_seat
    opp = tape_agent(steps, opp_seat)
    # the recorded final scores (from the real game)
    try:
        last = steps[-1]
        rec_rewards = [float(s.get("reward") or 0.0) for s in last]
    except Exception:
        rec_rewards = [0.0, 0.0]
    seed = replay.get("configuration", {}).get("seed") or 0
    n_steps = len(steps)
    a0, a1 = (candidate_fn, opp) if our_seat == 0 else (opp, candidate_fn)
    res = play_game(a0, a1, seed=int(seed), steps=n_steps)
    if res.get("error"):
        return {"error": res["error"], "rec_self": rec_rewards[our_seat],
                "rec_opp": rec_rewards[opp_seat]}
    rewards = res["rewards"]
    self_r = rewards[our_seat]
    opp_r = rewards[opp_seat]
    return {
        "self": self_r, "opp": opp_r, "margin": self_r - opp_r,
        "outcome": "win" if self_r > opp_r else "loss" if self_r < opp_r else "tie",
        "rec_self": rec_rewards[our_seat], "rec_opp": rec_rewards[opp_seat],
        "seed": seed, "error": None,
    }
