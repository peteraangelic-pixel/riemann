"""Deterministic selector and exact Kaggriculture action adapter.

This completes the estimator -> candidates -> selector -> action path used for
closed-loop experiments.  It is deliberately a lab component, not a promoted
submission version: promotion still requires packaging and control/holdout tests.
"""
from __future__ import annotations

from typing import Any

from .reactive_candidates import Candidate, SafetyBudget, SEED_COST, market_candidates, unit_candidates
from .reactive_state import GameState, estimate

PASS = ("PASS",)
_MOVE = {"NORTH": (0, -1), "SOUTH": (0, 1), "WEST": (-1, 0), "EAST": (1, 0)}


def _destination(position: tuple[int, int], action: tuple[Any, ...]) -> tuple[int, int]:
    delta = _MOVE.get(action[0] if action else "")
    return (position[0] + delta[0], position[1] + delta[1]) if delta else position


def _unit_actions(state: GameState, budget: SafetyBudget) -> list[list[Any]]:
    """Greedily assign one bounded candidate per unit without move collisions."""
    chosen: list[tuple[Any, ...]] = []
    destinations: set[tuple[int, int]] = set()
    origins = {unit.position for unit in state.own.units}
    vacated: set[tuple[int, int]] = set()
    for unit in state.own.units:
        action = PASS
        for candidate in unit_candidates(state, unit, budget):
            proposed = candidate.action
            if candidate.score <= 0 and proposed != PASS:
                continue
            destination = _destination(unit.position, proposed)
            moving = destination != unit.position
            # Do not send two own units to one square or move into an own unit
            # whose departure has not already been selected.
            if destination in destinations or (moving and destination in origins and destination not in vacated):
                continue
            action = proposed
            break
        destination = _destination(unit.position, action)
        destinations.add(destination)
        if destination != unit.position:
            vacated.add(unit.position)
        chosen.append(action)
    return [list(action) for action in chosen]


def _market_actions(state: GameState, budget: SafetyBudget) -> list[list[Any]]:
    """Select orders while accounting for cash and inventory sequentially."""
    cash = float(state.own.cash)
    shed = dict(state.own.shed)
    seeds = dict(state.own.seeds)
    selected: list[list[Any]] = []
    candidates = market_candidates(state, budget)

    # Realize bounded sales first; their proceeds may finance later purchases.
    for candidate in (c for c in candidates if c.action and c.action[0] == "SELL"):
        _, item, raw_qty = candidate.action
        qty = min(max(0, int(raw_qty)), max(0, int(shed.get(item, 0))))
        if not qty:
            continue
        shed[item] = int(shed.get(item, 0)) - qty
        cash += qty * state.prices.get(item, 0)
        selected.append(["SELL", item, qty])

    for candidate in (c for c in candidates if c.action and c.action[0] != "SELL"):
        op = candidate.action[0]
        if op != "BUY_SEED" or len(candidate.action) != 3:
            continue
        _, crop, raw_qty = candidate.action
        qty = max(0, int(raw_qty)); cost = SEED_COST.get(str(crop), 10**9) * qty
        if not qty or cash - cost < budget.cash_reserve:
            continue
        cash -= cost
        seeds[str(crop)] = int(seeds.get(str(crop), 0)) + qty
        selected.append(["BUY_SEED", str(crop), qty])
    return selected[:budget.max_market_candidates]


def select_action(state: GameState, budget: SafetyBudget = SafetyBudget()) -> dict[str, list]:
    """Return a legal-shaped action object for one estimated state."""
    units = _unit_actions(state, budget)
    return {
        "farmer": units[0] if units else ["PASS"],
        "hands": units[1:] if len(units) > 1 else [],
        "market": _market_actions(state, budget),
    }


def decide(observation: dict[str, Any], configuration: Any = None,
           budget: SafetyBudget = SafetyBudget()) -> dict[str, list]:
    """Submission-schema adapter for closed-loop experiments.

    Exceptions intentionally remain visible in the lab.  A future compact
    submission wrapper may fail safe to PASS, while audited evaluation must
    still record any internal failure instead of scoring it as a normal game.
    """
    return select_action(estimate(observation, configuration), budget)
