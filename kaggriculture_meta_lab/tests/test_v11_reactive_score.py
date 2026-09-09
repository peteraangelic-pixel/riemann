"""Contract tests for the active reactive planner."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENT = ROOT / "agents/variants/agent_v11_reactive_score.py"


def _load():
    spec = importlib.util.spec_from_file_location("_v11_reactive_score", AGENT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class _Planner:
    def decide(self, observation):
        return {"farmer": ["PASS"], "hands": [], "market": [["PASS"]]}


def test_opening_uses_day_hour_when_player_observation_omits_step():
    module = _load()
    module._PLANNER = _Planner()
    module.SUBIN_OPENING_STEPS = 2
    config = {"turnsPerDay": 24}
    first = module.act({"day": 0, "hour": 0}, config)
    second = module.act({"day": 0, "hour": 1}, config)
    third = module.act({"day": 0, "hour": 2}, config)
    assert first["market"] == [
        ["BUY_PRODUCT", "WHEAT", 13],
        ["SELL", "WHEAT", 13],
        ["BUY_PRODUCT", "WHEAT", 13],
    ]
    assert second["market"][-2:] == [
        ["BUY_ANIMAL", "COW", 2], ["BUY_ANIMAL", "SHEEP", 2]
    ]
    assert third["market"] == [["PASS"]]


def test_explicit_step_and_opening_ablation_are_deterministic():
    module = _load()
    module._PLANNER = _Planner()
    module.SUBIN_OPENING_STEPS = 2
    assert module.act({"step": 1}, {})["market"][0] == ["SELL", "WHEAT", 13]
    module.SUBIN_OPENING_STEPS = 0
    assert module.act({"step": 0}, {})["market"] == [["PASS"]]


def test_profile_and_evolution_bounds_are_sane():
    module = _load()
    # Shipped defaults retain the closed-loop V7 control. TOP10-inspired
    # components are explicit genes, not an unvalidated bundled promotion.
    assert module.LABOR_MODE == "AUTO"
    assert module.LABOR_PROFILE == 0
    assert module.SUBIN_OPENING_STEPS == 0
    assert module.ADAPT_OPPONENT_MODE == 0
    assert module.ANIMAL_TARGETS == {"COW": 8, "SHEEP": 6, "GOOSE": 0}
    assert sum(module.ANIMAL_TARGETS.values()) == module.ANIMAL_TARGET
    assert len(module.EVOLUTION_BOUNDS) >= 18
    for name, (low, high) in module.EVOLUTION_BOUNDS.items():
        assert hasattr(module, name), name
        assert low <= getattr(module, name) <= high, name
