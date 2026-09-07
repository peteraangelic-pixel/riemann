from __future__ import annotations
import csv
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.export_tape import DEFAULT_AGENT, extract, write_tape
from tools.py_reference import PythonReplay
from tools.rust_client import Job, replay_many

BINARY = Path(os.environ.get("KG_SIM_BIN", ROOT / "target/release/kg_sim")).resolve()


class ExportTests(unittest.TestCase):
    def test_example_matches_actual_python_actions_and_modifiers(self):
        # Execute only this pinned, trusted fixture in the TEST, never in the exporter.
        module = runpy.run_path(str(DEFAULT_AGENT))
        self.assertEqual(extract(), module["ACTIONS"])
        for seat in extract():
            self.assertEqual(seat[0]["market"], [["BUY_PRODUCT", "WHEAT", 21]])
            self.assertEqual(seat[1]["market"][0], ["SELL", "WHEAT", 16])

    def test_txt_extensions_and_no_code_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "agent.txt"
            source.write_text(DEFAULT_AGENT.read_text())
            self.assertEqual(extract(source), extract())
            sentinel = Path(directory) / "MUST_NOT_EXIST"
            source.write_text(f"ACTIONS=[[{{}}],[{{}}]]\nopen({str(sentinel)!r},'w').write('bad')\n")
            with self.assertRaises(ValueError):
                extract(source)
            self.assertFalse(sentinel.exists())

    def test_unknown_mutation_is_not_silently_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "agent.txt"
            source.write_text("ACTIONS=[[{}],[{}]]\nfor x in ACTIONS: x.clear()\n")
            with self.assertRaises(ValueError):
                extract(source)


@unittest.skipUnless(BINARY.is_file(), "build the release binary first (cargo build --release --locked)")
class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="kg-cli-")
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)
        self.a = self.dir / "a, seat tape.json"
        self.b = self.dir / "b.json"
        self.tape_a = [[{"market": [["BUY_SEED", "WHEAT", 1]]}], [{"market": [["BUY_SEED", "WHEAT", 3]]}]]
        self.tape_b = [[{"market": [["BUY_SEED", "WHEAT", 2]]}], [{"market": [["BUY_SEED", "WHEAT", 4]]}]]
        write_tape(self.a, self.tape_a)
        write_tape(self.b, self.tape_b)

    def call(self, *args, single=True, ok=True, env=None):
        command = [str(BINARY)]
        if single:
            command += ["--tape-a", str(self.a), "--tape-b", str(self.b), "--seed", "-17"]
        command += list(map(str, args))
        proc = subprocess.run(command, capture_output=True, text=True, env=env)
        self.assertEqual(proc.returncode == 0, ok, proc.stdout + proc.stderr)
        parsed = [json.loads(line) for line in proc.stdout.splitlines()]
        return parsed, proc

    def test_reverse_uses_opposite_seat_tapes_and_returns_a_b_order(self):
        rows, _ = self.call("--steps", 2)
        self.assertEqual(rows, [{"rewards": [2990.0, 2960.0], "errors": []}])
        rows, _ = self.call("--steps", 2, "--reverse-seats")
        self.assertEqual(rows[0]["rewards"], [2970.0, 2980.0])

    def test_horizon_and_short_tape_repeat(self):
        for steps, mode in [(1, "kaggle"), (2, "kaggle"), (3, "kaggle"), (0, "turns"), (1, "turns"), (5, "turns")]:
            rows, _ = self.call("--steps", steps, "--step-mode", mode)
            expected = PythonReplay(self.tape_a, self.tape_b, -17, steps=steps, step_mode=mode).run()
            self.assertEqual(rows[0]["rewards"], expected)

    def test_csv_quoting_relative_paths_header_and_thread_determinism(self):
        path = self.dir / "jobs.csv"
        with path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["seed", "tape_a", "tape_b", "reverse"])
            for seed, reverse in [(0, 0), (-1, 1), (2**63 - 1, "false"), (-(2**63), "true")]:
                writer.writerow([seed, self.a.name, self.b.name, reverse])
        outputs = []
        for threads in (1, 4, 16):
            rows, proc = self.call("--jobs", path, "--threads", threads, "--steps", 2, single=False)
            self.assertEqual([r["rewards"] for r in rows], [[2990, 2960], [2970, 2980], [2990, 2960], [2970, 2980]])
            outputs.append(proc.stdout)
        _, proc = self.call("--jobs", path, "--steps", 2, single=False, env={**os.environ, "RAYON_NUM_THREADS": "2"})
        self.assertEqual(outputs, [proc.stdout] * 3)

    def test_bad_batch_row_is_not_a_zero_reward_game(self):
        path = self.dir / "bad.csv"
        with path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([0, self.a.name, self.b.name, 0])
            writer.writerow([1, "missing.json", self.b.name, 0])
            writer.writerow([2, self.a.name, self.b.name, 1])
            writer.writerow(["malformed"])
        rows, _ = self.call("--jobs", path, "--steps", 2, single=False, ok=False)
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0]["rewards"], [2990, 2960])
        self.assertIsNone(rows[1]["rewards"])
        self.assertTrue(rows[1]["errors"])
        self.assertEqual(rows[2]["rewards"], [2970, 2980])
        self.assertIsNone(rows[3]["rewards"])

    def test_errors_for_bad_json_and_unsupported_board(self):
        self.a.write_text("not JSON")
        rows, _ = self.call("--steps", 2, ok=False)
        self.assertIsNone(rows[0]["rewards"])
        self.assertTrue(rows[0]["errors"])
        write_tape(self.a, self.tape_a)
        config = self.dir / "config.json"
        config.write_text('{"boardSize":8}')
        rows, _ = self.call("--config", config, "--steps", 2, ok=False)
        self.assertIn("boardSize=10", rows[0]["errors"][0])
        config.write_text('{"marketParams":{"WHEAT":{"T":0}}}')
        rows, _ = self.call("--config", config, "--steps", 2, ok=False)
        self.assertIsNone(rows[0]["rewards"])

    def test_zero_threads_rejected(self):
        jobs = self.dir / "empty.csv"
        jobs.write_text("")
        rows, _ = self.call("--jobs", jobs, "--threads", 0, single=False, ok=False)
        self.assertIn("threads", rows[0]["errors"][0])

    def test_supplied_spec_is_the_default_config(self):
        plain, _ = self.call("--steps", 25)
        supplied, _ = self.call("--steps", 25, "--config", ROOT / "reference/kaggriculture_config.json")
        self.assertEqual(plain, supplied)

    def test_explicit_trim_hands_preserves_raw_atomic_plant_rule(self):
        actions = [{"market": [["BUY_SEED", "WHEAT", 1]]}, {"farmer": ["PLANT", "WHEAT"], "hands": [["PLANT", "WHEAT"]]}]
        write_tape(self.a, [actions, actions])
        for trim in [False, True]:
            trace = self.dir / "trace.jsonl"
            extra = ["--trim-hands"] if trim else []
            self.call("--steps", 3, "--trace", trace, *extra)
            frames = [json.loads(line) for line in trace.read_text().splitlines()]
            self.assertEqual(len(frames), 3)
            tile = frames[-1]["farms"][0]["tiles"][4][4]
            self.assertEqual(tile is not None, trim)
            self.assertEqual(frames[-1]["privates"][0]["seeds"]["WHEAT"], 0 if trim else 1)

    def test_python_batch_client_preserves_order_and_refuses_errors(self):
        jobs = [Job(1, self.a, self.b), Job(-2, self.a, self.b, True)]
        self.assertEqual([v["rewards"] for v in replay_many(jobs, binary=BINARY, steps=2, threads=2)], [[2990, 2960], [2970, 2980]])
        with self.assertRaises(RuntimeError):
            replay_many([Job(0, self.dir / "missing", self.b)], binary=BINARY)
        self.assertEqual(replay_many([], binary=BINARY), [])


if __name__ == "__main__":
    unittest.main()
