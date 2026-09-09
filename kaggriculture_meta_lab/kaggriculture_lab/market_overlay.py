"""Python reference for the bounded Rust market overlay.

The function is intentionally pure: callers provide the live day, cash, shed,
and current sell quotes. This makes Python/Rust parity vectors straightforward.
"""
from __future__ import annotations

import copy
import math
from typing import Any

PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
            "EGG", "MILK", "WOOL", "FERTILIZER")
BUY_OPS = {"HIRE", "BUY_LAND", "BUY_PRODUCT", "BUY_SEED", "BUY_ANIMAL"}

DEFAULT_PROFILE: dict[str, Any] = {
    "enabled": False, "start_day": 0, "buy_stop_day": 30,
    "endgame_day": 27, "cash_reserve": 0.0,
    "sell_fraction_bp": 10_000, "endgame_sell_fraction_bp": 10_000,
    **{f"{p.lower()}_reserve": 0 for p in PRODUCTS},
    **{f"min_{p.lower()}_price": 0.0 for p in PRODUCTS},
}


def validate_profile(raw: dict[str, Any]) -> dict[str, Any]:
    unknown = set(raw) - set(DEFAULT_PROFILE)
    if unknown:
        raise ValueError(f"unknown overlay keys: {sorted(unknown)}")
    p = DEFAULT_PROFILE | raw
    for key in ("start_day", "buy_stop_day", "endgame_day"):
        if not isinstance(p[key], int) or isinstance(p[key], bool) or p[key] < 0:
            raise ValueError(f"{key} must be a non-negative integer")
    for key in ("sell_fraction_bp", "endgame_sell_fraction_bp"):
        if not isinstance(p[key], int) or isinstance(p[key], bool) or not 0 <= p[key] <= 10_000:
            raise ValueError(f"{key} must be an integer in 0..10000")
    for product in PRODUCTS:
        key = f"{product.lower()}_reserve"
        if not isinstance(p[key], int) or isinstance(p[key], bool) or p[key] < 0:
            raise ValueError(f"{key} must be a non-negative integer")
    for key in ("cash_reserve", *(f"min_{p.lower()}_price" for p in PRODUCTS)):
        if isinstance(p[key], bool) or not isinstance(p[key], (int, float)):
            raise ValueError(f"{key} must be numeric")
        p[key] = float(p[key])
        if not math.isfinite(p[key]) or p[key] < 0:
            raise ValueError(f"{key} must be finite and non-negative")
    if not isinstance(p["enabled"], bool):
        raise ValueError("enabled must be boolean")
    return p


def apply_market_overlay(action: dict[str, Any], state: dict[str, Any],
                         profile: dict[str, Any]) -> dict[str, Any]:
    """Return a copied action with exactly the Rust overlay's market edits."""
    p = validate_profile(profile)
    out = copy.deepcopy(action)
    day = int(state["day"])
    if not p["enabled"] or day < p["start_day"]:
        return out
    fraction = p["endgame_sell_fraction_bp"] if day >= p["endgame_day"] else p["sell_fraction_bp"]
    shed, prices = state["shed"], state["prices"]
    money = float(state["money"])
    for order in out.get("market", []):
        if not isinstance(order, list) or not order:
            continue
        op = order[0]
        if op == "SELL" and len(order) >= 3 and order[1] in PRODUCTS:
            product = order[1]
            available = max(0, int(shed.get(product, 0)) - p[f"{product.lower()}_reserve"])
            allowed = available * fraction // 10_000
            order[2] = min(max(0, int(order[2])), allowed)
            if float(prices[product]) < p[f"min_{product.lower()}_price"]:
                order[2] = 0
        elif op in BUY_OPS and (day >= p["buy_stop_day"] or money <= p["cash_reserve"]):
            if op in {"HIRE", "BUY_LAND"}:
                order[:] = []
            elif len(order) >= 3:
                order[2] = 0
    return out
