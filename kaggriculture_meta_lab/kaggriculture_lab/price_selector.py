"""Conservative price-aware market selector for the V6b experiment.

This module only ranks legal SELL candidates. It never changes farmer/hands
schedules and defaults to the baseline action when the schema is incomplete.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class PriceDecision:
    action: dict[str, Any]
    product: str | None
    score: float
    reason: str


def _prices(obs: dict[str, Any]) -> dict[str, float]:
    raw = obs.get("prices", obs.get("market_prices", {}))
    return {str(k).upper(): float(v or 0) for k, v in raw.items()} if isinstance(raw, dict) else {}


def _inventory(obs: dict[str, Any]) -> dict[str, float]:
    raw = obs.get("inventory", obs.get("shed", {}))
    return {str(k).upper(): float(v or 0) for k, v in raw.items()} if isinstance(raw, dict) else {}


def choose_sell(observation: dict[str, Any], legal_actions: list[dict[str, Any]], baseline: dict[str, Any]) -> PriceDecision:
    """Choose a legal sell only with sufficient inventory and quote evidence.

    The selector is intentionally fail-closed: missing prices/inventory,
    unknown action schemas, low shed headroom, or no quote history return the
    unchanged baseline. ``min_premium`` and ``min_headroom`` are conservative
    optional configuration values.
    """
    if not isinstance(baseline, dict) or not isinstance(legal_actions, list):
        return PriceDecision(baseline, None, 0.0, "invalid schema")
    prices, inventory = _prices(observation), _inventory(observation)
    history = observation.get("recent_prices", {})
    if not prices or not inventory or not isinstance(history, dict):
        return PriceDecision(baseline, None, 0.0, "incomplete market fingerprint")
    capacity = float(observation.get("shed_capacity", 0) or 0)
    used = sum(inventory.values())
    headroom = capacity - used if capacity else 999999.0
    if headroom < float(observation.get("min_headroom", 1) or 1):
        return PriceDecision(baseline, None, 0.0, "protect shed headroom")
    min_premium = float(observation.get("min_premium", 0.10) or 0.10)
    candidates: list[tuple[float, str, dict[str, Any]]] = []
    for action in legal_actions:
        if not isinstance(action, dict) or str(action.get("type", "")).upper() != "SELL":
            continue
        product = str(action.get("product", action.get("item", ""))).upper()
        quantity = float(action.get("quantity", action.get("amount", 0)) or 0)
        if not product or quantity <= 0 or inventory.get(product, 0) < quantity:
            continue
        quote = prices.get(product, 0.0)
        prior = float(history.get(product, quote) or quote)
        if prior <= 0 or quote < prior * (1.0 + min_premium):
            continue
        candidates.append((quote * min(quantity, inventory[product]), product, action))
    if not candidates:
        return PriceDecision(baseline, None, 0.0, "no sufficiently premium legal sale")
    score, product, action = max(candidates, key=lambda x: x[0])
    return PriceDecision(action, product, score, "premium quote with inventory coverage")
