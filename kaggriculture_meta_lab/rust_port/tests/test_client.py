from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.rust_client import Job, SimulatorError, _invoke, replay, replay_many


class ClientProtocolTests(unittest.TestCase):
    def invoke(self, data, *, code=0, allow_errors=False, expected=1, raw=False):
        stdout = data if raw else json.dumps(data) + "\n"
        process = subprocess.CompletedProcess(["kg_sim"], code, stdout, "diagnostic")
        with patch("tools.rust_client.subprocess.run", return_value=process):
            return _invoke(["kg_sim"], expected, allow_errors)

    def test_valid_response_preserved(self):
        row = {"rewards": [10, 20.5], "errors": [], "future_metadata": 1}
        self.assertEqual(self.invoke(row), [row])

    def test_wrong_shapes_always_rejected(self):
        for row in [[], 1, None, {}, {"rewards": [1, 2]},
                    {"rewards": [1, 2], "errors": "oops"},
                    {"rewards": [1, 2], "errors": [1]},
                    {"rewards": [1], "errors": []},
                    {"rewards": [1, 2, 3], "errors": []},
                    {"rewards": [True, 2], "errors": []},
                    {"rewards": ["1", 2], "errors": []},
                    {"rewards": [None, 2], "errors": []},
                    {"rewards": None, "errors": []}]:
            with self.subTest(row=row):
                for allowed in (False, True):
                    with self.assertRaises(SimulatorError):
                        self.invoke(row, allow_errors=allowed)

    def test_nan_infinity_and_numeric_overflow_always_rejected(self):
        for value in [float("nan"), float("inf"), -float("inf"), 10**400]:
            for allowed in (False, True):
                with self.subTest(value=str(value)[:20], allow_errors=allowed):
                    with self.assertRaises(SimulatorError):
                        self.invoke({"rewards": [value, 1], "errors": []}, allow_errors=allowed)
        with self.assertRaises(SimulatorError):
            self.invoke('{"rewards":[1e400,2],"errors":[]}', raw=True)

    def test_bad_exit_never_becomes_a_valid_game(self):
        for allowed in (False, True):
            with self.assertRaises(SimulatorError):
                self.invoke({"rewards": [1, 2], "errors": []}, code=1, allow_errors=allowed)

    def test_explicit_errors_can_be_returned_only_when_requested(self):
        for rewards in (None, [1, 2]):
            row = {"rewards": rewards, "errors": ["game failed or guard reached"]}
            with self.assertRaises(SimulatorError):
                self.invoke(row, code=1)
            self.assertEqual(self.invoke(row, code=1, allow_errors=True), [row])

    def test_missing_extra_and_non_json_output_rejected(self):
        with self.assertRaises(SimulatorError):
            self.invoke("", raw=True)
        row = '{"rewards":[1,2],"errors":[]}\n'
        with self.assertRaises(SimulatorError):
            self.invoke(row * 2, raw=True)
        with self.assertRaises(SimulatorError):
            self.invoke("debug message\n" + row, raw=True)
        with self.assertRaises(SimulatorError):
            self.invoke(row, raw=True, expected=2)

    def test_error_excerpt_is_bounded(self):
        with self.assertRaises(SimulatorError) as raised:
            self.invoke("x" * 100000, raw=True)
        self.assertLess(len(str(raised.exception)), 3000)

    def test_start_failure_is_explicit(self):
        with patch("tools.rust_client.subprocess.run", side_effect=FileNotFoundError("missing binary")):
            with self.assertRaisesRegex(SimulatorError, "cannot start"):
                replay(Job(0, "a.json", "b.json"))

    def test_single_timeout_is_forwarded_without_accepting_partial_scores(self):
        error = subprocess.TimeoutExpired(["kg_sim"], 0.1, output=b'{"rewards":[1,2],"errors":[]}')
        with patch("tools.rust_client.subprocess.run", side_effect=error) as call:
            with self.assertRaisesRegex(SimulatorError, "no partial results"):
                replay(Job(0, "a.json", "b.json"), timeout=0.1)
            self.assertEqual(call.call_args.kwargs["timeout"], 0.1)


    def test_process_signal_cannot_be_hidden_by_an_error_row(self):
        row = {"rewards": None, "errors": ["one game failed"]}
        for code in (-9, 2, 70):
            with self.subTest(code=code):
                with self.assertRaisesRegex(SimulatorError, "process failed"):
                    self.invoke(row, code=code, allow_errors=True)

    def test_independent_hand_flags_are_forwarded_without_swapping_in_python(self):
        process = subprocess.CompletedProcess(["kg_sim"], 0, '{"rewards":[1,2],"errors":[]}\n', "")
        with patch("tools.rust_client.subprocess.run", return_value=process) as call:
            replay(Job(0, "a.json", "b.json", True), trim_hands_a=True)
            argv = call.call_args.args[0]
            self.assertIn("--reverse-seats", argv)
            self.assertIn("--trim-hands-a", argv)
            self.assertNotIn("--trim-hands-b", argv)
            self.assertNotIn("--trim-hands", argv)
            replay_many([Job(0, "a.json", "b.json", True)], trim_hands_b=True)
            argv = call.call_args.args[0]
            self.assertIn("--trim-hands-b", argv)
            self.assertNotIn("--trim-hands-a", argv)

    def test_batch_timeout_forwarded(self):
        process = subprocess.CompletedProcess(["kg_sim"], 0, '{"rewards":[1,2],"errors":[]}\n', "")
        with patch("tools.rust_client.subprocess.run", return_value=process) as call:
            replay_many([Job(0, "a.json", "b.json")], timeout=2.5)
            self.assertEqual(call.call_args.kwargs["timeout"], 2.5)


if __name__ == "__main__":
    unittest.main()
