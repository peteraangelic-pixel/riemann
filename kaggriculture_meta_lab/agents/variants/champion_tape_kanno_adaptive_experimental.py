"""Experimental Kanno V3 + real-schema reactive fallback.

The Kanno tape owns normal execution and its late-game market timing. The
fallback is entered only when cheap public/private consistency checks indicate
that the fixed trajectory is unsafe. This is deliberately an experiment, not
a promoted champion.
"""
from __future__ import annotations

import copy
import importlib.util
import logging
from pathlib import Path
from typing import Any

_HERE = Path(__file__).parent

def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, _HERE / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

_tape = _load("kanno_v3_tape", "champion_tape_kanno_ep107381285_v1.py")
_reactive = _load("v10_reactive", "agent_v10_reactive_subin.py")
_LOG = logging.getLogger(__name__)


def _pass_action(observation: dict[str, Any]) -> dict[str, Any]:
    farms = observation.get("farms") or []
    p = int(observation.get("player", 0) or 0)
    hands = []
    if isinstance(farms, list) and 0 <= p < len(farms) and isinstance(farms[p], dict):
        hands = [["PASS"] for _ in (farms[p].get("hands") or [])]
    return {"farmer": ["PASS"], "hands": hands, "market": []}


def _state_is_unsafe(observation: dict[str, Any], tape_action: dict[str, Any]) -> bool:
    """Conservative divergence gate using real Kaggriculture fields.

    We only divert when the tape requests a purchase that the currently visible
    farm cannot afford. This avoids inventing a fake observation schema and
    leaves the valuable Kanno endgame timing untouched.
    """
    farms = observation.get("farms") or []
    p = int(observation.get("player", 0) or 0)
    money = None
    if isinstance(farms, list) and 0 <= p < len(farms) and isinstance(farms[p], dict):
        money = farms[p].get("money")
    if not isinstance(money, (int, float)):
        return False
    for order in tape_action.get("market", []) if isinstance(tape_action, dict) else []:
        if not isinstance(order, list) or not order:
            continue
        kind = order[0]
        if kind in {"BUY_PRODUCT", "BUY_SEED", "BUY_ANIMAL", "BUY_LAND", "HIRE"}:
            # Exact price is engine-owned; a clearly empty cash account is a
            # reliable divergence signal without approximating market prices.
            if money <= 0:
                return True
    return False


def act(observation: dict[str, Any], configuration: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = configuration or {}
    try:
        tape_action = _tape.act(observation, cfg)
        if _state_is_unsafe(observation, tape_action):
            try:
                return _reactive.act(observation, cfg)
            except Exception:  # noqa: BLE001
                _LOG.exception("reactive fallback failed")
                return _pass_action(observation)
        return copy.deepcopy(tape_action)
    except Exception:  # noqa: BLE001
        _LOG.exception("Kanno tape failed; entering reactive fallback")
        try:
            return _reactive.act(observation, cfg)
        except Exception:  # noqa: BLE001
            return _pass_action(observation)


def agent(observation: dict[str, Any], configuration: dict[str, Any] | None = None) -> dict[str, Any]:
    return act(observation, configuration)
