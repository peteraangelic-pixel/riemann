"""CPU-cheap regression tests for the pinned sweep integration patch."""
from __future__ import annotations

import argparse
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]


def load_sweep(lab, name):
    sys.path[:0] = [str(lab), str(ROOT / "kaggriculture_meta_lab")]
    spec = importlib.util.spec_from_file_location(name, lab / "scripts/sweep.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FunnelGuards(unittest.TestCase):
    sweep = None
    original = None

    @staticmethod
    def actors():
        return [("keeper", Path("/one/main.py")), ("buyer", Path("/two/main.py")), ("control", Path("/three/main.py"))]

    @staticmethod
    def runner(jobs, workers, **kwargs):
        values = {"/one/main.py": 3000, "/two/main.py": 2990, "/three/main.py": 2980}
        out = []
        for seed, a, b, seat, steps, tag in reversed(jobs):
            own, other = values[a], values[b]
            out.append({"tag": tag, "seed": seed, "seat": seat, "opponent": b,
                        "self_reward": own, "opp_reward": other, "margin": own-other,
                        "outcome": "win" if own>other else "loss" if own<other else "tie", "error": None})
        return out

    def test_prebuilt_paths_are_not_discarded_as_duplicate_parameters(self):
        config = {"variants": [{"name": n, "path": str(p), "params": {}} for n, p in self.actors()]}
        self.assertEqual(len(self.original.expand_config(config)), 1)  # reproduction on pinned source
        self.assertEqual(len(self.sweep.expand_config(config)), 3)
        for item in config["variants"]:
            item.pop("params")
        self.assertEqual(len(self.sweep.expand_config(config)), 3)

    def test_true_duplicate_specs_still_deduplicate(self):
        config = {"variants": [{"name": "a", "path": "one.py", "params": {}}, {"name": "b", "path": "one.py", "params": {}}]}
        self.assertEqual(len(self.sweep.expand_config(config)), 1)

    def test_duplicate_names_with_distinct_paths_are_rejected(self):
        config = {"variants": [{"name": "same", "path": "one.py"}, {"name": "same", "path": "two.py"}]}
        with self.assertRaises(ValueError):
            self.sweep.expand_config(config)

    def test_same_basename_finalists_keep_all_pairs_and_correct_ranking(self):
        old = self.original.stage_finals(self.actors(), 2, 7, 1, [], runner=self.runner)
        self.assertEqual(old["ranked"][0], "buyer")  # original attribution bug changes winner
        new = self.sweep.stage_finals(self.actors(), 2, 7, 1, [], runner=self.runner)
        self.assertEqual(new["ranked"], ["keeper", "buyer", "control"])
        for a, row in new["pairwise"].items():
            self.assertEqual(len(row), 2)
            for b, cell in row.items():
                self.assertNotEqual(a, b)
                self.assertEqual(cell["games"], 4)
        self.assertEqual(new["pairwise"]["keeper"]["buyer"]["score"], 1.0)
        self.assertEqual(new["pairwise"]["buyer"]["keeper"]["score"], 0.0)

    def test_two_labels_for_same_frozen_path_still_have_distinct_pairs(self):
        actors = [("first", Path("/one/main.py")), ("second", Path("/one/main.py")), ("control", Path("/three/main.py"))]
        result = self.sweep.stage_finals(actors, 2, 7, 1, [], runner=self.runner)
        self.assertEqual(result["pairwise"]["first"]["second"], {"games": 4, "score": 0.5})
        self.assertEqual(result["pairwise"]["first"]["control"]["score"], 1.0)

    def test_incomplete_duplicate_and_foreign_rows_are_rejected(self):
        jobs = self.sweep.build_jobs("/one/main.py", ["/two/main.py"], 2, 1, tag="case")
        rows = self.runner(jobs, 1)
        self.sweep._require_stage_rows(rows, jobs, "test")  # order need not be completion order
        bad = [rows[:-1], rows[:-1] + [rows[0]]]
        foreign = copy.deepcopy(rows)
        foreign[0]["tag"] = "foreign"
        bad.append(foreign)
        for value in bad:
            with self.assertRaises(RuntimeError):
                self.sweep._require_stage_rows(value, jobs, "test")

    def test_nonfinite_inconsistent_and_error_rows_are_rejected(self):
        jobs = self.sweep.build_jobs("/one/main.py", ["/two/main.py"], 1, 1, tag="case")
        rows = self.runner(jobs, 1)
        for patch in [{"margin": float("nan")}, {"margin": 999}, {"outcome": "loss"}, {"outcome": "error", "error": "failure"}]:
            bad = copy.deepcopy(rows)
            bad[0].update(patch)
            with self.assertRaises(RuntimeError):
                self.sweep._require_stage_rows(bad, jobs, "test")

    def test_pilot_budget_is_96_full_games_per_backend(self):
        self.assertEqual(self.sweep.project_game_budget(3, False, 3, 2, 10, 2, True),
                         {"screen": 12, "promote": 60, "finals": 24, "total": 96})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-lab", type=Path, required=True)
    parser.add_argument("--patched-lab", type=Path, required=True)
    args = parser.parse_args()
    FunnelGuards.original = load_sweep(args.original_lab.resolve(), "pilot_original_sweep")
    FunnelGuards.sweep = load_sweep(args.patched_lab.resolve(), "pilot_patched_sweep")
    unittest.main(argv=[sys.argv[0]], verbosity=2)
