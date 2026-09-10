"""Safety wrapper for the real-schema reactive FarmerPlanner.

This is an independent reliability layer, not a copied tape or strategy. It
keeps the existing planner's decisions when valid and records/contains planner
failures instead of silently converting them into an unexplained season loss.
"""
from __future__ import annotations

import copy
import logging
from typing import Any

try:
    from . import agent_v10_reactive_subin as _base
except ImportError:
    import importlib.util
    from pathlib import Path
    _spec = importlib.util.spec_from_file_location(
        "agent_v10_reactive_subin", Path(__file__).with_name("agent_v10_reactive_subin.py")
    )
    _base = importlib.util.module_from_spec(_spec)
    assert _spec.loader is not None
    _spec.loader.exec_module(_base)

_LOG = logging.getLogger(__name__)


def _pass_action(observation: dict[str, Any]) -> dict[str, Any]:
    farms = observation.get("farms") or []
    player = int(observation.get("player", 0) or 0)
    hands = []
    if isinstance(farms, list) and 0 <= player < len(farms):
        farm = farms[player]
        if isinstance(farm, dict):
            hands = [["PASS"] for _ in (farm.get("hands") or [])]
    return {"farmer": ["PASS"], "hands": hands, "market": []}


def _sanitize(action: Any, observation: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(action, dict):
        raise ValueError("planner returned non-dict action")
    out = copy.deepcopy(action)
    if not isinstance(out.get("farmer"), list):
        out["farmer"] = ["PASS"]
    if not isinstance(out.get("hands"), list):
        out["hands"] = []
    if not isinstance(out.get("market"), list):
        out["market"] = []
    farms = observation.get("farms") or []
    player = int(observation.get("player", 0) or 0)
    if isinstance(farms, list) and 0 <= player < len(farms):
        farm = farms[player]
        if isinstance(farm, dict) and isinstance(farm.get("hands"), list):
            out["hands"] = out["hands"][:len(farm["hands"])]
    return out


def act(observation: dict[str, Any], configuration: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        action = _base.act(observation, configuration or {})
        return _sanitize(action, observation)
    except Exception:  # noqa: BLE001 - never let one observation kill a season
        _LOG.exception("reactive planner failure at step=%s", observation.get("step"))
        return _pass_action(observation)


def agent(observation: dict[str, Any], configuration: dict[str, Any] | None = None) -> dict[str, Any]:
    return act(observation, configuration)
