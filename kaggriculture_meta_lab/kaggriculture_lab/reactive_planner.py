"""R1 bounded reactive planner primitives.

This module deliberately contains no simulator-specific submission wrapper yet.
It turns an observation into a small, deterministic, safe candidate-action set;
R2 will add land/building/animal planners and R3 opponent-state features.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PlannerConfig:
    cash_reserve: int = 250
    endgame_step: int = 648
    sell_price_floor: int = 1
    max_candidates: int = 12
    worker_move_limit: int = 4


@dataclass(frozen=True)
class Candidate:
    action: dict[str, Any]
    score: float
    reason: str


def _cash(obs: dict[str, Any]) -> float:
    return float(obs.get("cash", obs.get("money", 0)))


def _step(obs: dict[str, Any]) -> int:
    return int(obs.get("step", obs.get("turn", 0)))


def _products(obs: dict[str, Any]) -> dict[str, Any]:
    value = obs.get("inventory", obs.get("storage", {}))
    return value if isinstance(value, dict) else {}


def _add(out: list[Candidate], action: dict[str, Any], score: float, reason: str) -> None:
    out.append(Candidate(action, score, reason))


def generate_candidates(observation: dict[str, Any], config: PlannerConfig = PlannerConfig()) -> list[Candidate]:
    """Generate only bounded, immediately legal-looking R1 decisions.

    The simulator remains the authority on legality. This layer avoids economic
    footguns and is deterministic: identical observations produce identical
    ordering. Observation adapters can provide richer fields incrementally.
    """
    out: list[Candidate] = []
    cash, step = _cash(observation), _step(observation)
    inv = _products(observation)
    prices = observation.get("prices", {})
    if not isinstance(prices, dict):
        prices = {}

    # R1 execution priorities: finish work before opening new work.
    for action in observation.get("urgent_actions", []):
        if isinstance(action, dict):
            _add(out, action, 1000.0, "urgent observation action")

    for action in observation.get("workers", {}).get("actions", []) if isinstance(observation.get("workers"), dict) else []:
        if isinstance(action, dict):
            _add(out, action, 800.0, "worker task supplied by adapter")

    # Sell only available stock and never below the configured floor unless in
    # endgame. Quantity is left to the adapter/simulator contract.
    for product, quantity in sorted(inv.items()):
        if not isinstance(quantity, (int, float)) or quantity <= 0:
            continue
        price = float(prices.get(product, 0) or 0)
        if price >= config.sell_price_floor or step >= config.endgame_step:
            _add(out, {"type": "SELL", "product": product, "quantity": int(quantity)},
                 500.0 + price + (100.0 if step >= config.endgame_step else 0),
                 "liquidate available stock")

    # Ask the observation adapter for legal productive actions. We score them
    # by explicit economic hints, never by arbitrary dictionary ordering.
    for item in observation.get("legal_actions", []):
        if not isinstance(item, dict):
            continue
        kind = str(item.get("type", item.get("action", ""))).upper()
        if kind in {"WATER", "HARVEST", "FERTILIZE", "PLANT", "MOVE"}:
            gain = float(item.get("expected_gain", item.get("value", 0)) or 0)
            cost = float(item.get("cost", 0) or 0)
            if cash - cost >= config.cash_reserve or kind in {"WATER", "HARVEST", "MOVE"}:
                _add(out, item, 300.0 + gain - cost * 0.01, f"safe productive {kind.lower()}")

    # PASS is always available as the final safe fallback.
    _add(out, {"type": "PASS"}, 0.0, "safe fallback")
    out.sort(key=lambda c: (-c.score, str(c.action)))
    return out[: config.max_candidates]


def choose_action(observation: dict[str, Any], config: PlannerConfig = PlannerConfig()) -> dict[str, Any]:
    """Return the highest-scoring bounded action for an observation."""
    return generate_candidates(observation, config)[0].action
