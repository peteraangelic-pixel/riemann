"""Regression tests embedded in patches/lab-replay-correctness.patch.

Run after applying that patch in the actual Meta-Lab checkout. This file's name
intentionally avoids default pytest collection in the standalone Rust branch.
"""
from __future__ import annotations

import gzip
import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from kaggriculture_lab.agents import resolve
from kaggriculture_lab.corpus import score_episode, tape_agent
from kaggriculture_lab.engine import play_game
from kaggriculture_lab.tournament import _play

PASS = {"farmer": ["PASS"], "hands": [], "market": []}
FIRST = {"farmer": ["EAST"], "hands": [], "market": [["BUY_SEED", "WHEAT", 2]]}
LAST = {"farmer": ["WEST"], "hands": [], "market": []}


def replay_fixture():
    return {
        "configuration": {"seed": None},
        "info": {"seed": 123456},
        "steps": [
            [{"action": None, "reward": 0}, {"action": None, "reward": 0}],
            [{"action": FIRST, "reward": 0}, {"action": PASS, "reward": 0}],
            [{"action": LAST, "reward": 100}, {"action": PASS, "reward": 90}],
        ],
    }


def test_both_tape_loaders_use_replay_row_step_plus_one(tmp_path):
    replay = replay_fixture()
    path = tmp_path / "replay.json.gz"
    with gzip.open(path, "wt", encoding="utf8") as f:
        json.dump(replay, f)
    for agent in (resolve(f"tape:{path}#0"), tape_agent(replay["steps"], 0)):
        assert agent({"step": 0}) == FIRST
        assert agent({"step": 1}) == LAST
        assert agent({"step": 9999}) == LAST
        returned = agent({"step": 0})
        returned["market"][0][1] = "MUTATED"
        assert agent({"step": 0}) == FIRST


def test_invalid_tape_seat_cannot_silently_create_a_pass_opponent(tmp_path):
    path = tmp_path / "replay.json"
    path.write_text(json.dumps(replay_fixture()), encoding="utf8")
    for seat in (-1, 2):
        with pytest.raises(ValueError, match="seat"):
            resolve(f"tape:{path}#{seat}")


@pytest.mark.parametrize("info_seed,config_seed,expected", [(123456, None, 123456), (0, 999, 0), (42, 7, 42), (None, 5, 5)])
def test_corpus_uses_resolved_seed_with_legacy_fallback(info_seed, config_seed, expected):
    replay = replay_fixture()
    replay["info"]["seed"] = info_seed
    replay["configuration"]["seed"] = config_seed
    with patch("kaggriculture_lab.engine.play_game", return_value={"rewards": [100, 90], "statuses": ["DONE", "DONE"], "error": None}) as called:
        result = score_episode("pass", replay, 0)
    assert result["error"] is None
    assert result["seed"] == expected
    assert called.call_args.kwargs["seed"] == expected


def test_missing_seed_is_an_error_not_an_invented_zero():
    replay = replay_fixture()
    replay["info"].clear()
    with patch("kaggriculture_lab.engine.play_game") as called:
        result = score_episode("pass", replay, 0)
    assert result["error"]
    called.assert_not_called()


def test_historical_error_survives_terminal_done_overwrite(monkeypatch):
    import kaggle_environments
    failed = [SimpleNamespace(status="ERROR", reward=None), SimpleNamespace(status="ACTIVE", reward=0)]
    final = [SimpleNamespace(status="DONE", reward=3000), SimpleNamespace(status="DONE", reward=3000)]
    env = SimpleNamespace(steps=[failed, final], info={"seed": 1}, run=lambda agents: None, interpreter=lambda state, context: state)
    monkeypatch.setattr(kaggle_environments, "make", lambda *args, **kwargs: env)
    result = play_game("pass", "pass", 1, steps=2)
    assert result["statuses"] == ["DONE", "DONE"]
    assert result["error"] and "ERROR" in result["error"]


@pytest.mark.parametrize("reward,status", [(None, "DONE"), (float("nan"), "DONE"), (float("inf"), "DONE"), (3.0, "TIMEOUT"), (3.0, "ACTIVE")])
def test_invalid_terminal_results_do_not_become_scores(monkeypatch, reward, status):
    import kaggle_environments
    final = [SimpleNamespace(status=status, reward=reward), SimpleNamespace(status="DONE", reward=90)]
    env = SimpleNamespace(steps=[final], info={"seed": 1}, run=lambda agents: None, interpreter=lambda state, context: state)
    monkeypatch.setattr(kaggle_environments, "make", lambda *args, **kwargs: env)
    assert play_game("pass", "pass", 1, steps=2)["error"]


@pytest.mark.parametrize("result", [
    {"rewards": [100, 0], "statuses": ["DONE", "ERROR"], "error": None},
    {"rewards": [100, 0], "statuses": ["DONE", "DONE"], "error": "historical timeout"},
    {"rewards": [float("nan"), 0], "statuses": ["DONE", "DONE"], "error": None},
    {"rewards": [100, 0], "error": None},
])
def test_tournament_never_counts_failed_or_malformed_results_as_wins(result):
    with patch("kaggriculture_lab.engine.play_game", return_value=result):
        row = _play((0, "pass", "pass", 0, 720, "regression"))
    assert row["outcome"] == "error"
    assert row["error"]


def test_last_turn_exception_is_not_hidden_before_the_replay_is_recorded():
    def fails_on_last(observation, configuration):
        if observation["step"] == configuration.episodeSteps - 2:
            raise RuntimeError("last-turn failure")
        return PASS
    result = play_game(fails_on_last, "pass", seed=0, steps=4)
    assert result["statuses"] == ["DONE", "DONE"]
    assert result["error"] and "ERROR" in result["error"]
