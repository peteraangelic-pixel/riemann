from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.py_reference import PythonReplay, configuration


class ReferenceConfigTests(unittest.TestCase):
    def test_flat_default_product_does_not_replace_market_overrides(self):
        values = {"marketParams": {"default": {"WHEAT": {"base": 900}}, "WHEAT": {"base": 40}}}
        for document in (values, {"configuration": values}):
            with self.subTest(document=document):
                self.assertEqual(configuration(document)["marketParams"], values["marketParams"])
                replay = PythonReplay([[{}], [{}]], [[{}], [{}]], 0, config=document)
                self.assertEqual(replay.snapshot()["market"]["prices"]["WHEAT"], 40)
                self.assertNotIn("default", replay.snapshot()["market"]["params"])

    def test_unknown_override_keeps_original_snapshot_shape(self):
        replay = PythonReplay([[{}], [{}]], [[{}], [{}]], 0, config={"marketParams": {"default": {}}})
        self.assertIn("params", replay.snapshot()["market"])
        self.assertEqual(replay.snapshot()["market"]["prices"]["WHEAT"], 25)

    def test_full_spec_matches_default(self):
        document = json.loads((ROOT / "reference/kaggriculture_config.json").read_text())
        self.assertEqual(configuration(document), configuration())

    def test_reference_mixed_rules_move_with_reverse(self):
        actions = [{"market": [["BUY_SEED", "WHEAT", 1]]},
                   {"farmer": ["PLANT", "WHEAT"], "hands": [["PLANT", "WHEAT"]]}]
        tape = [actions, actions]
        for a, b in ((False, False), (True, False), (False, True), (True, True)):
            for reverse in (False, True):
                replay = PythonReplay(tape, tape, 0, steps=3, reverse=reverse, trim_hands_a=a, trim_hands_b=b)
                replay.run()
                flags = [b, a] if reverse else [a, b]
                for seat in (0, 1):
                    self.assertEqual(replay.snapshot()["farms"][seat]["tiles"][4][4] is not None, flags[seat])


if __name__ == "__main__":
    unittest.main()
