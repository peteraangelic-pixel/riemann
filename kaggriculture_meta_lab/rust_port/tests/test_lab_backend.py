from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.agent_tape import emit_source
from tools.lab_backend import BackendError, run_report
from tools.py_reference import PythonReplay
from tools.rust_client import SimulatorError, binary_name


class LabBackendTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="kg-backend-tests-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.binary = self.root / binary_name()
        self.binary.write_text("not executed; native runner is injected")
        self.binary.chmod(0o755)
        self.exports = []
        self.native_calls = []
        self.a = self.agent("one/agent.py", [[{"market": [["BUY_SEED", "WHEAT", 1]]}], [{}]])
        self.b = self.agent("two/agent.py", [[{}], [{"market": [["BUY_SEED", "WHEAT", 4]]}]])

    def agent(self, name, data, trim=False):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(emit_source(data, trim_hands=trim))
        return str(path)

    def native(self, jobs, **options):
        self.native_calls.append((jobs, options))
        results = []
        for job in jobs:
            self.exports += [job.tape_a, job.tape_b]
            a, b = [json.loads(Path(p).read_text()) for p in (job.tape_a, job.tape_b)]
            expected = PythonReplay(a, b, job.seed, steps=options["steps"], reverse=job.reverse,
                                    trim_hands_a=options.get("trim_hands_a", False),
                                    trim_hands_b=options.get("trim_hands_b", False)).run()
            results.append({"rewards": expected, "errors": []})
        return results

    @staticmethod
    def python(jobs, workers, **options):
        return [{"tag": j[5], "seed": j[0], "seat": j[3], "opponent": j[2],
                 "self_reward": 3000.0, "opp_reward": 3000.0, "margin": 0.0,
                 "outcome": "tie", "error": None} for j in reversed(jobs)]

    def run_jobs(self, jobs, **options):
        with patch("tools.lab_backend.rust_client.replay_many", side_effect=self.native):
            return run_report(jobs, 2, binary=self.binary, progress_every=0, **options)

    def test_same_basename_does_not_overwrite_other_tape(self):
        report = self.run_jobs([(0, self.a, self.b, 0, 2, "case")])
        self.assertEqual((report.rows[0]["self_reward"], report.rows[0]["opp_reward"]), (2990, 2960))
        self.assertNotEqual(self.exports[0], self.exports[1])
        self.assertTrue(all(not Path(p).exists() for p in self.exports))

    def test_each_source_is_read_and_compiled_once_not_per_job(self):
        report = self.run_jobs([(s, self.a, self.b, 0, 2, "case") for s in range(20)])
        self.assertEqual(report.metrics["source_reads"], 2)
        self.assertEqual(report.metrics["source_compilations"], 2)
        self.assertEqual(report.metrics["rust_calls"], 1)
        self.assertEqual(report.metrics["rust_jobs"], 20)

    def test_mixed_horizons_are_separate_buckets(self):
        report = self.run_jobs([(0, self.a, self.b, 0, 2, "one"), (0, self.a, self.b, 0, 3, "two")])
        self.assertEqual([r["self_reward"] for r in report.rows], [2990, 2980])
        self.assertEqual({opts["steps"] for _, opts in self.native_calls}, {2, 3})

    def test_python_completion_order_is_joined_by_identity_not_zip(self):
        jobs = [(11, "reactive-a", "pass", 0, 2, "same-tag"),
                (12, self.a, self.b, 0, 2, "native"),
                (13, "reactive-b", "pass", 1, 3, "same-tag")]
        report = self.run_jobs(jobs, python_runner=self.python)
        self.assertEqual([r["seed"] for r in report.rows], [11, 12, 13])
        self.assertEqual([r["tag"] for r in report.rows], ["same-tag", "native", "same-tag"])
        self.assertEqual(report.metrics["python_jobs"], 2)

    def test_actions_attribute_does_not_freeze_a_reactive_policy(self):
        path = self.root / "reactive.py"
        path.write_text('ACTIONS=[[{"market":[["BUY_SEED","WHEAT",99]]}],[{}]]\ndef agent(observation, configuration):\n return {"farmer":["PASS"]}\n')
        callback = Mock(side_effect=self.python)
        report = self.run_jobs([(0, str(path), self.b, 0, 2, "reactive")], python_runner=callback)
        self.assertEqual(report.metrics["rust_jobs"], 0)
        self.assertEqual(report.rows[0]["self_reward"], 3000)
        callback.assert_called_once()

    def test_strict_mode_refuses_partial_fallback_before_any_execution(self):
        callback = Mock()
        with patch("tools.lab_backend.rust_client.replay_many") as native:
            with self.assertRaises(BackendError):
                run_report([(0, self.a, self.b, 0, 2, "ok"), (1, "pass", "pass", 0, 2, "unsupported")], 2,
                           mode="rust", binary=self.binary, python_runner=callback, progress_every=0)
            native.assert_not_called()
        callback.assert_not_called()

    def test_process_failure_is_not_silently_rerun_in_python(self):
        callback = Mock()
        def fail(jobs, **options):
            self.exports.extend([jobs[0].tape_a, jobs[0].tape_b])
            raise SimulatorError("broken response")
        with patch("tools.lab_backend.rust_client.replay_many", side_effect=fail):
            with self.assertRaisesRegex(BackendError, "no automatic Python rerun"):
                run_report([(0, self.a, self.b, 0, 2, "native"), (1, "pass", "pass", 0, 2, "python")], 2,
                           binary=self.binary, python_runner=callback, progress_every=0)
        callback.assert_not_called()
        self.assertTrue(all(not Path(p).exists() for p in self.exports))

    def test_missing_binary_falls_back_before_inspecting_sources(self):
        report = run_report([(0, self.a, self.b, 0, 2, "fallback")], 2,
                            binary=self.root / "missing", python_runner=self.python, progress_every=0)
        self.assertEqual(report.metrics["source_reads"], 0)
        self.assertEqual(report.metrics["python_jobs"], 1)
        self.assertEqual(report.rows[0]["tag"], "fallback")

    def test_snapshot_results_are_reused_without_losing_distinct_tags(self):
        alias = self.agent("alias/agent.py", [[{"market": [["BUY_SEED", "WHEAT", 1]]}], [{}]])
        report = self.run_jobs([(0, self.a, self.b, 0, 2, "first"), (0, alias, self.b, 0, 2, "second")])
        self.assertEqual(report.metrics["source_reads"], 3)
        self.assertEqual(report.metrics["source_compilations"], 2)
        self.assertEqual(report.metrics["unique_rust_games"], 1)
        self.assertEqual(report.metrics["reused_rust_results"], 1)
        self.assertEqual([r["tag"] for r in report.rows], ["first", "second"])
        self.assertEqual([r["self_reward"] for r in report.rows], [2990, 2990])

    def test_next_call_sees_changed_source_instead_of_stale_global_cache(self):
        first = self.run_jobs([(0, self.a, self.b, 0, 2, "first")])
        stamp = Path(self.a).stat().st_mtime_ns
        self.agent("one/agent.py", [[{"market": [["BUY_SEED", "WHEAT", 2]]}], [{}]])
        os.utime(self.a, ns=(stamp, stamp))
        second = self.run_jobs([(0, self.a, self.b, 0, 2, "second")])
        self.assertEqual(first.rows[0]["self_reward"], 2990)
        self.assertEqual(second.rows[0]["self_reward"], 2980)

    def test_hand_policy_moves_with_agent_and_is_not_applied_to_raw_opponent(self):
        actions = [{} for _ in range(50)]
        actions[0] = {"market": [["BUY_SEED", "WHEAT", 1]]}
        actions[1] = {"farmer": ["PLANT", "WHEAT"], "hands": [["PLANT", "WHEAT"]]}
        actions[2] = {"farmer": ["WATER"]}
        actions[24] = {"farmer": ["WATER"]}
        actions[48] = {"farmer": ["HARVEST"]}
        actions[49] = {"farmer": ["DROP"], "market": [["SELL", "WHEAT", 100]]}
        a = self.agent("clipped.py", [actions, actions], True)
        b = self.agent("raw.py", [actions, actions], False)
        report = self.run_jobs([(17, a, b, 0, 51, "p0"), (17, a, b, 1, 51, "p1")])
        self.assertEqual([(r["self_reward"], r["opp_reward"]) for r in report.rows], [(3017, 2990), (3017, 2990)])
        self.assertTrue(self.native_calls[0][1]["trim_hands_a"])
        self.assertFalse(self.native_calls[0][1]["trim_hands_b"])

    def test_bad_python_identity_and_duplicate_rows_are_errors(self):
        jobs = [(1, "pass", "pass", 0, 2, "tag"), (2, "pass", "pass", 0, 2, "tag")]
        def duplicate(tagged, workers, **kwargs):
            row = self.python(tagged, workers)[0]
            return [row, row]
        with self.assertRaisesRegex(BackendError, "duplicate"):
            self.run_jobs(jobs, python_runner=duplicate)
        def wrong(tagged, workers, **kwargs):
            rows = self.python(tagged, workers)
            rows[0]["seed"] += 100
            return rows
        with self.assertRaisesRegex(BackendError, "identity"):
            self.run_jobs(jobs, python_runner=wrong)

    def test_windows_executable_name_and_empty_batch(self):
        self.assertEqual(binary_name("nt"), "kg_sim.exe")
        self.assertEqual(binary_name("posix"), "kg_sim")
        self.assertEqual(run_report([], 1, mode="rust").rows, [])


if __name__ == "__main__":
    unittest.main()
