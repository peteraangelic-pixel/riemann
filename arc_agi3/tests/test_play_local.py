"""Tests for the local public-game runner's portable outcome report."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import play_local  # noqa: E402


class _State:
    value = "game_over"


class _Scorecard:
    score = 1.75


class LocalRunnerReportTests(unittest.TestCase):
    def test_state_name_accepts_sdk_like_enums_and_plain_values(self) -> None:
        self.assertEqual(play_local._state_name(_State()), "GAME_OVER")
        self.assertEqual(play_local._state_name("win"), "WIN")

    def test_write_report_is_compact_json_safe_and_frame_free(self) -> None:
        result = play_local.RunResult(
            game_id="ls20",
            state="NOT_FINISHED",
            levels_completed=2,
            actions=17,
            policy_evidence={"ACTION6": {"attempts": 4, "changed": 3}},
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "report.json"
            play_local.write_report(
                path,
                requested_games=["ls20", "vc33"],
                results=[result],
                scorecard=_Scorecard(),
            )
            report = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["requested_games"], ["ls20", "vc33"])
        self.assertEqual(report["scorecard"], "1.75")
        self.assertEqual(report["results"], [
            {
                "actions": 17,
                "game_id": "ls20",
                "levels_completed": 2,
                "policy_evidence": {"ACTION6": {"attempts": 4, "changed": 3}},
                "state": "NOT_FINISHED",
            }
        ])
        self.assertNotIn("frame", path.name + json.dumps(report).lower())


if __name__ == "__main__":
    unittest.main()
