"""Safe hybrid wrapper around the corrected GermanJurado1 master tape.

The tape remains the preferred plan. This wrapper only applies conservative
schema/legality guards and falls back to a valid no-op action on malformed
observations or tape divergence. It is not claimed to be an adaptive champion.
"""
from __future__ import annotations

import copy
import logging
from typing import Any

try:
    from . import champion_tape_germanjurado1_v1 as _tape
except ImportError:  # direct Kaggle/file-loader execution
    import importlib.util
    from pathlib import Path
    _spec = importlib.util.spec_from_file_location(
        "champion_tape_germanjurado1_v1",
        Path(__file__).with_name("champion_tape_germanjurado1_v1.py"),
    )
    _tape = importlib.util.module_from_spec(_spec)
    assert _spec.loader is not None
    _spec.loader.exec_module(_tape)

_LOG = logging.getLogger(__name__)
_MAX_MARKET_ORDERS = 10
_MAX_TAPE_STEP = 719


def _fallback(observation: dict[str, Any]) -> dict[str, Any]:
    farms = observation.get("farms") or []
    player = int(observation.get("player", 0) or 0)
    hands = []
    if isinstance(farms, list) and 0 <= player < len(farms):
        raw = farms[player]
        if isinstance(raw, dict) and isinstance(raw.get("hands"), list):
            hands = [["PASS"] for _ in raw["hands"]]
    return {"farmer": ["PASS"], "hands": hands, "market": []}


def _valid_order(order: Any) -> bool:
    if not isinstance(order, list) or not order or not isinstance(order[0], str):
        return False
    return order[0] in {
        "BUY_PRODUCT", "SELL", "BUY_SEED", "BUY_ANIMAL", "HIRE", "BUY_LAND",
    }


def _sanitize(action: Any, observation: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(action, dict):
        raise ValueError("tape action is not an object")
    out = copy.deepcopy(action)
    if not isinstance(out.get("farmer"), list):
        out["farmer"] = ["PASS"]
    if not isinstance(out.get("hands"), list):
        out["hands"] = []
    farms = observation.get("farms") or []
    player = int(observation.get("player", 0) or 0)
    expected = 0
    if isinstance(farms, list) and 0 <= player < len(farms):
        if isinstance(farms[player], dict) and isinstance(farms[player].get("hands"), list):
            expected = len(farms[player]["hands"])
    out["hands"] = out["hands"][:expected]
    if not isinstance(out.get("market"), list):
        out["market"] = []
    out["market"] = [order for order in out["market"][:_MAX_MARKET_ORDERS] if _valid_order(order)]
    return out


def act(observation: dict[str, Any], configuration: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        step = min(max(int(observation.get("step", 0) or 0), 0), _MAX_TAPE_STEP)
        action = _tape.act(observation, configuration or {})
        return _sanitize(action, observation)
    except Exception:  # noqa: BLE001 - submission must not crash the episode
        _LOG.exception("hybrid tape fallback at step=%s", observation.get("step"))
        return _fallback(observation)


def agent(observation: dict[str, Any], configuration: dict[str, Any] | None = None) -> dict[str, Any]:
    return act(observation, configuration)
