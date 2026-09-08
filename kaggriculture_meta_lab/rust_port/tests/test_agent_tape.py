from __future__ import annotations

import ast
import copy
from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import runpy
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.agent_tape import UnsupportedAgent, compile_file, compile_source, emit_source
from tools.export_tape import DEFAULT_AGENT, extract


class StaticTapeCompilerTests(unittest.TestCase):
    def test_frozen_b21_matches_executed_reference_data(self):
        compiled = compile_file(DEFAULT_AGENT)
        self.assertEqual(json.loads(compiled.payload), extract())
        self.assertTrue(compiled.trim_hands)
        self.assertEqual(compiled.family, "b21")
        self.assertIsInstance(compiled.payload, bytes)
        with self.assertRaises(FrozenInstanceError):
            compiled.payload = b"[]"

    def test_standard_templates_round_trip_and_keep_hand_rule_in_identity(self):
        data = [[{"market": [["BUY_SEED", "WHEAT", 1]]}, {}], [{}]]
        raw = compile_source(emit_source(data, trim_hands=False))
        clipped = compile_source(emit_source(data, trim_hands=True))
        self.assertEqual(json.loads(raw.payload), data)
        self.assertEqual(raw.payload, clipped.payload)
        self.assertNotEqual(raw.fingerprint, clipped.fingerprint)
        self.assertFalse(raw.trim_hands)
        self.assertTrue(clipped.trim_hands)

    def test_emitted_policy_matches_compiled_actions(self):
        actions = [[{"farmer": ["PLANT", "WHEAT"], "hands": [["PLANT", "WHEAT"]]}], [{}]]
        with tempfile.TemporaryDirectory() as directory:
            for trim in (False, True):
                path = Path(directory) / "agent.py"
                path.write_text(emit_source(actions, trim_hands=trim))
                # Execute only the test-generated known template, not arbitrary input.
                module = runpy.run_path(str(path))
                compiled = compile_file(path)
                for seat in (0, 1):
                    obs = {"player": seat, "step": 999, "farms": [{"hands": []}, {"hands": []}]}
                    expected = copy.deepcopy(json.loads(compiled.payload)[seat][-1])
                    if trim:
                        expected["hands"] = expected.get("hands", [])[:0]
                    self.assertEqual(module["agent"](obs, {}), expected)

    def test_reactive_agent_is_not_a_tape_just_because_actions_exists(self):
        text = 'import base64,copy,json,zlib\nACTIONS=[[{}],[{}]]\ndef agent(observation, configuration):\n return {"market": [["BUY_SEED", "WHEAT", int(observation["farms"][0]["money"])]]}\n'
        with self.assertRaisesRegex(UnsupportedAgent, "reactive"):
            compile_source(text)

    def test_no_side_effects_during_classification(self):
        with tempfile.TemporaryDirectory() as directory:
            sentinel = Path(directory) / "must-not-exist"
            text = emit_source([[{}], [{}]]) + f"\nopen({str(sentinel)!r}, 'w').write('bad')\n"
            with self.assertRaises(UnsupportedAgent):
                compile_source(text)
            self.assertFalse(sentinel.exists())

    def test_hidden_shadowing_decorators_defaults_and_duplicates_are_rejected(self):
        original = emit_source([[{}], [{}]])
        variants = [
            original + "\ncopy = ACTIONS\n",
            original.replace("def agent(", "@evil()\ndef agent("),
            original.replace("configuration):", "configuration=evil()):"),
            original + "\ndef agent(observation, configuration):\n return {}\n",
            original.replace("import base64, copy, json, zlib\n", ""),
            "act = agent\n" + original,
        ]
        for text in variants:
            with self.subTest(text=text[:50]):
                with self.assertRaises(UnsupportedAgent):
                    compile_source(text)

    def test_formatting_does_not_change_template_classification(self):
        source = emit_source([[{}], [{}]], trim_hands=False)
        formatted = ast.unparse(ast.parse(source))
        self.assertEqual(compile_source(source).fingerprint, compile_source(formatted).fingerprint)

    def test_invalid_data_does_not_silently_become_pass(self):
        source = emit_source([[{}], [{}]])
        for bad in ([1, 2], [[], []], [[], [{}]], {"steps": []}):
            tree = ast.parse(source)
            for node in tree.body:
                if isinstance(node, ast.Assign) and node.targets[0].id == "ACTIONS":
                    node.value = ast.parse(repr(bad), mode="eval").body
            with self.assertRaises(UnsupportedAgent):
                compile_source(ast.unparse(tree))


if __name__ == "__main__":
    unittest.main()
