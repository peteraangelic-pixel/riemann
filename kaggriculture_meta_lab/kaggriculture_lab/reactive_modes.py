"""Bounded R2-R4 reactive decision layers.

These layers rank safe planner modes and emit only adapter-provided legal
candidates. They do not inspect player names or emit arbitrary simulator code.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ModeDecision:
    mode: str
    score: float
    reason: str


MODES = ("PRODUCTION", "MARKET", "ANIMALS", "EXPANSION", "RECOVERY", "ENDGAME")


def _num(obs: dict[str, Any], *keys: str, default: float = 0.0) -> float:
    for key in keys:
        value = obs.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    return default


def classify_public_pressure(observation: dict[str, Any]) -> dict[str, float]:
    """Infer public economic pressures only; no player identity features."""
    prices = observation.get("prices", {})
    demand = observation.get("demand", {})
    if not isinstance(prices, dict):
        prices = {}
    if not isinstance(demand, dict):
        demand = {}
    wheat = float(prices.get("WHEAT", 0) or 0)
    wheat_demand = float(demand.get("WHEAT", 0) or 0)
    return {
        "price_pressure": max(0.0, 100.0 - wheat),
        "production_pressure": max(0.0, wheat_demand - float(observation.get("wheat_stock", 0) or 0)),
        "cash_pressure": max(0.0, _num(observation, "cash", "money") - 250.0),
        "land_pressure": max(0.0, _num(observation, "occupied_cells") - _num(observation, "available_cells")),
    }


def choose_mode(observation: dict[str, Any]) -> ModeDecision:
    """Choose a safe high-level mode using public state and time only."""
    step = int(_num(observation, "step", "turn"))
    if step >= int(_num(observation, "endgame_step", default=648)):
        return ModeDecision("ENDGAME", 1000.0, "endgame liquidation window")
    pressure = classify_public_pressure(observation)
    if _num(observation, "cash", "money") < _num(observation, "cash_reserve", default=250):
        return ModeDecision("RECOVERY", 900.0, "cash below operating reserve")
    if _num(observation, "animals_needing_feed", "animals_needing_care") > 0:
        return ModeDecision("ANIMALS", 800.0, "animal maintenance is due")
    if _num(observation, "available_cells") <= 0:
        return ModeDecision("EXPANSION", 700.0, "field capacity is exhausted")
    if pressure["price_pressure"] > 50.0:
        return ModeDecision("MARKET", 600.0, "public price pressure")
    return ModeDecision("PRODUCTION", 500.0 + pressure["production_pressure"], "productive work available")


def r2_safe_candidates(observation: dict[str, Any]) -> list[dict[str, Any]]:
    """Return adapter-supplied R2 farm-system actions with preconditions."""
    mode = choose_mode(observation).mode
    actions = observation.get("legal_actions", [])
    if not isinstance(actions, list):
        return [{"type": "PASS"}]
    allowed = {
        "ANIMALS": {"FEED", "CARE", "BUY_ANIMAL", "MOVE_ANIMAL"},
        "EXPANSION": {"BUY_LAND", "BUILD_PASTURE", "BUILD_COOP"},
        "ENDGAME": {"SELL", "HARVEST", "PASS"},
    }.get(mode, {"WATER", "HARVEST", "FERTILIZE", "PLANT", "SELL", "PASS"})
    result = [a for a in actions if isinstance(a, dict) and str(a.get("type", "")).upper() in allowed]
    return result[:12] or [{"type": "PASS"}]
