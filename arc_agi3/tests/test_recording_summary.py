"""Regression tests for the portable public-recording visual summary."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import summarize_recordings  # noqa: E402


class RecordingSummaryTests(unittest.TestCase):
    def test_frame_to_text_uses_palette_and_unknown_marker(self) -> None:
        self.assertEqual(
            summarize_recordings.frame_to_text([[[0, 10, 15, 99], [1]]]),
            "0AF?\n1???",
        )
        self.assertEqual(summarize_recordings.frame_to_text([]), "<no frame>")

    def test_summary_keeps_first_and_final_of_longest_recording_per_game(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            recordings = Path(directory)
            short = recordings / "ls20.short.recording.jsonl"
            long = recordings / "ls20.long.recording.jsonl"
            short.write_text(json.dumps({"data": {"game_id": "ls20-a", "frame": [[[1]]]}}) + "\n")
            long.write_text(
                "\n".join(
                    json.dumps({"data": event})
                    for event in (
                        {"game_id": "ls20-a", "frame": [[[1]]], "state": "NOT_FINISHED", "levels_completed": 0},
                        {
                            "game_id": "ls20-a",
                            "frame": [[[2]]],
                            "state": "WIN",
                            "levels_completed": 1,
                            "action_input": {"id": 6},
                            "reasoning": {"must_not": "appear"},
                        },
                    )
                )
                + "\n"
            )
            summary = summarize_recordings.summarize_paths(recordings.glob("*.jsonl"))

        self.assertIn("### ls20 (2 recorded frames)", summary)
        self.assertIn("**first**", summary)
        self.assertIn("**final** — action 6, state `WIN`, levels `1`", summary)
        self.assertIn("\n1\n", summary)
        self.assertIn("\n2\n", summary)
        self.assertNotIn("must_not", summary)

    def test_empty_directory_has_explicit_safe_message(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            summary = summarize_recordings.summarize_paths(Path(directory).glob("*.jsonl"))
        self.assertIn("No usable frame recording", summary)


if __name__ == "__main__":
    unittest.main()
