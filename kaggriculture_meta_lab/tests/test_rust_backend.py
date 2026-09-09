from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from kaggriculture_lab import rust_backend

PASS = {"farmer": ["PASS"], "hands": [], "market": []}
FIRST = {"farmer": ["EAST"], "hands": [], "market": [["BUY_SEED", "WHEAT", 2]]}
LAST = {"farmer": ["WEST"], "hands": [], "market": []}


def _module(path: Path) -> Path:
    from rust_port.tools.agent_tape import emit_source
    path.write_text(emit_source([[PASS], [PASS]], trim_hands=True), encoding="utf-8")
    return path


def _replay(path: Path) -> Path:
    replay = {
        "info": {"seed": 123},
        "steps": [
            [{"action": None, "reward": 0}, {"action": None, "reward": 0}],
            [{"action": FIRST, "reward": 0}, {"action": PASS, "reward": 0}],
            [{"action": LAST, "reward": 100}, {"action": PASS, "reward": 90}],
        ],
    }
    with gzip.open(path, "wt", encoding="utf-8") as stream:
        json.dump(replay, stream)
    return path


def test_raw_replay_source_skips_initial_row_and_stays_untrimmed(tmp_path):
    source = rust_backend._source(f"tape:{_replay(tmp_path / 'replay.json.gz')}#0")
    assert source is not None
    assert source.trim_hands is False
    assert source.actions == [[FIRST, LAST], [FIRST, LAST]]


def test_invalid_replay_seat_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="seat"):
        rust_backend._source(f"tape:{_replay(tmp_path / 'replay.json.gz')}#2")


def test_actions_do_not_freeze_a_reactive_policy(tmp_path):
    path = tmp_path / "reactive.py"
    path.write_text(
        'ACTIONS=[[{}],[{}]]\ndef agent(observation, configuration):\n'
        ' return {"market": [["BUY_SEED", "WHEAT", int(observation["farms"][0]["money"])]]}\n',
        encoding="utf-8",
    )
    assert rust_backend._source(str(path)) is None


def test_backend_partitions_mixed_hand_semantics_and_preserves_order(tmp_path, monkeypatch):
    candidate = _module(tmp_path / "candidate.py")
    opponent = _module(tmp_path / "opponent.py")
    replay = _replay(tmp_path / "replay.json.gz")
    executable = tmp_path / "kg_sim"
    executable.write_text("fake", encoding="utf-8")

    calls = []

    class Job:
        def __init__(self, seed, tape_a, tape_b, reverse=False, overlay_a=None):
            self.seed, self.tape_a, self.tape_b, self.reverse = seed, tape_a, tape_b, reverse
            self.overlay_a = overlay_a

    def replay_many(jobs, **kwargs):
        calls.append((jobs, kwargs))
        return [{"rewards": [100.0 + job.seed, 90.0], "errors": []} for job in jobs]

    monkeypatch.setitem(sys.modules, "rust_client", SimpleNamespace(Job=Job, replay_many=replay_many))
    jobs = [
        (1, str(candidate), str(opponent), 0, 720, "static"),
        (2, str(candidate), f"tape:{replay}#0", 1, 720, "raw"),
    ]
    rows = rust_backend.run_rust(jobs, workers=4, binary=executable)

    assert [row["tag"] for row in rows] == ["static", "raw"]
    assert [row["outcome"] for row in rows] == ["win", "win"]
    assert len(calls) == 2
    modes = {(call[1]["trim_hands_a"], call[1]["trim_hands_b"]) for call in calls}
    assert modes == {(True, True), (True, False)}
    raw_jobs = next(call[0] for call in calls if call[1]["trim_hands_b"] is False)
    assert raw_jobs[0].reverse is True


def test_rust_game_error_is_not_scored(tmp_path, monkeypatch):
    candidate = _module(tmp_path / "candidate.py")
    executable = tmp_path / "kg_sim"
    executable.write_text("fake", encoding="utf-8")

    class Job:
        def __init__(self, *args, **kwargs):
            pass

    monkeypatch.setitem(
        sys.modules,
        "rust_client",
        SimpleNamespace(Job=Job, replay_many=lambda *a, **k: [{"rewards": None, "errors": ["bad tape"]}]),
    )
    row = rust_backend.run_rust(
        [(1, str(candidate), str(candidate), 0, 720, "broken")],
        workers=1,
        binary=executable,
    )[0]
    assert row["outcome"] == "error"
    assert row["error"] == "bad tape"


def test_auto_does_not_hide_rust_failure_with_python_rerun(tmp_path, monkeypatch):
    monkeypatch.setattr(rust_backend, "rust_binary", lambda: tmp_path / "kg_sim")
    monkeypatch.setattr(rust_backend, "run_rust", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("parity")))
    with pytest.raises(RuntimeError, match="parity"):
        rust_backend.run_auto([], workers=1)
