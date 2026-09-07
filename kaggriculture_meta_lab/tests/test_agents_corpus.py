import gzip
import json
from pathlib import Path

import pytest

from kaggriculture_lab.agents import resolve, label
from kaggriculture_lab.corpus import tape_agent, _find_steps, score_episode

ROOT = Path(__file__).resolve().parents[1]


def _make_replay(path: Path, seed: int = 20260907, steps_n: int = 48):
    """Generate a tiny real replay via the engine and save it gzipped."""
    from kaggle_environments import make
    env = make("kaggriculture", configuration={"episodeSteps": steps_n, "seed": seed}, debug=False)
    env.run(["starter", "pass"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(env.toJSON(), f)


def test_builtin_and_labels():
    assert resolve("starter") == "starter"
    assert label("pass") == "pass"


def test_tape_from_gzipped_replay(tmp_path):
    rp = tmp_path / "12345" / "replay.json.gz"
    _make_replay(rp)
    fn = resolve(f"tape:{rp}")  # default = winner seat
    out = fn({"step": 0})
    assert set(out) == {"farmer", "hands", "market"}
    # beyond tape length still returns a valid action (last/PASS)
    assert fn({"step": 9999})["farmer"]


def test_score_episode_runs(tmp_path):
    rp = tmp_path / "67890" / "replay.json.gz"
    _make_replay(rp, seed=42, steps_n=48)
    replay = json.loads(gzip.open(rp, "rt").read())
    # candidate = starter, evaluated against the recorded opponent at seat 0
    res = score_episode("starter", replay, our_seat=0)
    assert res.get("error") is None
    assert res["outcome"] in ("win", "loss", "tie")
    assert res["self"] >= 0


def test_find_steps_tolerant():
    assert _find_steps({"steps": []}) == []
    assert _find_steps({"a": {"steps": [[{"action": {}}]]}})
