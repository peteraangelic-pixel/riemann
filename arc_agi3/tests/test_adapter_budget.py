"""SDK-free contract test for the adapter's exact action-budget guard."""
from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
AGENT_FILE = ROOT / "agent" / "my_agent.py"
sys.path.insert(0, str(ROOT / "agent"))


class AdapterBudgetTests(unittest.TestCase):
    def _load_adapter_with_sdk_stubs(self):
        class FakeGameState:
            WIN = object()
            NOT_FINISHED = object()

        fake_arcengine = types.ModuleType("arcengine")
        fake_arcengine.FrameData = object
        fake_arcengine.GameAction = object
        fake_arcengine.GameState = FakeGameState

        fake_agents = types.ModuleType("agents")
        fake_agents.__path__ = []
        fake_agent_module = types.ModuleType("agents.agent")
        fake_agent_module.Agent = type("Agent", (), {})

        module_name = "arc_agi3_budget_adapter"
        spec = importlib.util.spec_from_file_location(module_name, AGENT_FILE)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        with patch.dict(
            sys.modules,
            {
                "arcengine": fake_arcengine,
                "agents": fake_agents,
                "agents.agent": fake_agent_module,
                module_name: module,
            },
        ):
            spec.loader.exec_module(module)
        return module, FakeGameState

    def test_is_done_enforces_budget_before_reference_loop_off_by_one(self) -> None:
        adapter, game_state = self._load_adapter_with_sdk_stubs()
        agent = object.__new__(adapter.MyAgent)
        agent.ACTION_BUDGET = 50
        latest = types.SimpleNamespace(state=game_state.NOT_FINISHED)

        agent.action_counter = 49
        self.assertFalse(agent.is_done([], latest))
        agent.action_counter = 50
        self.assertTrue(agent.is_done([], latest))

    def test_is_done_always_stops_on_win(self) -> None:
        adapter, game_state = self._load_adapter_with_sdk_stubs()
        agent = object.__new__(adapter.MyAgent)
        agent.ACTION_BUDGET = 50
        agent.action_counter = 0
        self.assertTrue(agent.is_done([], types.SimpleNamespace(state=game_state.WIN)))


if __name__ == "__main__":
    unittest.main()
