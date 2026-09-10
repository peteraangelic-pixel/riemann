"""Bounded legal-looking candidate generation and material scoring."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .reactive_state import GameState, TileState, UnitState

SEED_COST = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}
ANIMAL_COST = {"GOOSE": 300, "COW": 400, "SHEEP": 500}


@dataclass(frozen=True)
class SafetyBudget:
    cash_reserve: int = 250
    feed_days: int = 2
    max_unit_candidates: int = 8
    max_market_candidates: int = 10
    inventory_soft_limit: int = 90


@dataclass(frozen=True)
class Candidate:
    scope: str
    action: tuple[Any, ...]
    score: float
    reason: str
    actor: int | None = None
    target: tuple[int, int] | None = None
    cost: float = 0.0
    immediate_gain: float = 0.0
    future_gain: float = 0.0
    risk: float = 0.0


def distance(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def move_toward(a: tuple[int, int], b: tuple[int, int]) -> tuple[str, ...]:
    if a[0] < b[0]: return ("EAST",)
    if a[0] > b[0]: return ("WEST",)
    if a[1] < b[1]: return ("SOUTH",)
    if a[1] > b[1]: return ("NORTH",)
    return ("PASS",)


def score(*, immediate: float = 0, future: float = 0, cost: float = 0,
          travel: int = 0, risk: float = 0, urgency: float = 0) -> float:
    return immediate + 0.45 * future + urgency - cost - 12 * travel - risk


def _tile_map(state: GameState) -> dict[tuple[int, int], TileState]:
    return {tile.position: tile for tile in state.own.tiles}


def _nearest_candidates(unit: UnitState, task: str, tiles: list[TileState], state: GameState,
                        base: float, reason: str, limit: int = 2) -> list[Candidate]:
    out = []
    for tile in sorted(tiles, key=lambda t: (distance(unit.position, t.position), t.y, t.x))[:limit]:
        travel = distance(unit.position, tile.position)
        value = tile.yield_units * state.prices.get(tile.crop or "", 0)
        out.append(Candidate("unit", move_toward(unit.position, tile.position),
                             score(immediate=value if task == "harvest" else 0,
                                   future=base, travel=travel,
                                   urgency=1200 if task == "urgent_water" else 0),
                             reason, unit.index, tile.position,
                             immediate_gain=value if task == "harvest" else 0,
                             future_gain=base))
    return out


def unit_candidates(state: GameState, unit: UnitState,
                    budget: SafetyBudget = SafetyBudget()) -> list[Candidate]:
    """Generate a bounded pool for one unit from exact visible preconditions."""
    tile_at = _tile_map(state).get(unit.position)
    out: list[Candidate] = []
    if tile_at:
        if tile_at.kind == "WEED":
            out.append(Candidate("unit", ("DIG",), 900, "dig standing weed", unit.index, unit.position))
        if tile_at.crop:
            if tile_at.mature(state.day):
                gain = tile_at.yield_units * state.prices.get(tile_at.crop, 0)
                out.append(Candidate("unit", ("HARVEST",), score(immediate=gain, urgency=800 if state.day >= 28 else 0),
                                     "harvest standing mature crop", unit.index, unit.position,
                                     immediate_gain=gain))
            if not tile_at.watered:
                urgency = 1400 if tile_at.unwatered_days else (600 if state.hour >= 17 else 250)
                out.append(Candidate("unit", ("WATER",), urgency, "water standing crop", unit.index, unit.position))
            if (tile_at.watered and unit.inventory.get("FERTILIZER", 0) > 0
                    and tile_at.fertilized_until < state.day):
                future = 2 * state.prices.get(tile_at.crop, 0)
                out.append(Candidate("unit", ("FERTILIZE",), score(future=future),
                                     "fertilize watered crop", unit.index, unit.position,
                                     future_gain=future))
        if tile_at.animal:
            if tile_at.yield_units:
                out.append(Candidate("unit", ("HARVEST",), 850, "collect animal product", unit.index, unit.position))
            if not tile_at.fed and unit.inventory.get("WHEAT", 0) > 0:
                out.append(Candidate("unit", ("FEED",), 1300, "prevent animal escape", unit.index, unit.position))
            if not tile_at.cared:
                out.append(Candidate("unit", ("CARE",), 620, "maintain animal yield", unit.index, unit.position))
            if tile_at.fertilizer_ready:
                out.append(Candidate("unit", ("COLLECT_FERTILIZER",), 500,
                                     "collect fertilizer", unit.index, unit.position))
    elif unit.position in state.own.free_cells:
        affordable = [crop for crop, qty in state.own.seeds.items() if qty > 0]
        if affordable:
            crop = max(affordable, key=lambda c: (state.prices.get(c, 0) - SEED_COST.get(c, 0), c))
            future = max(0, state.prices.get(crop, 0) * 3 - SEED_COST.get(crop, 0))
            out.append(Candidate("unit", ("PLANT", crop), score(future=future),
                                 "plant available seed on free tile", unit.index, unit.position,
                                 future_gain=future))

    urgent = [t for t in state.own.crops() if not t.watered and t.unwatered_days >= 1]
    mature = [t for t in state.own.crops() if t.mature(state.day)]
    out.extend(_nearest_candidates(unit, "urgent_water", urgent, state, 500, "route to dying crop"))
    out.extend(_nearest_candidates(unit, "harvest", mature, state, 0, "route to mature crop"))
    out.append(Candidate("unit", ("PASS",), 0, "safe fallback", unit.index, unit.position))
    out.sort(key=lambda c: (-c.score, c.action, c.target or (-1, -1)))
    return out[:budget.max_unit_candidates]


def market_candidates(state: GameState, budget: SafetyBudget = SafetyBudget()) -> list[Candidate]:
    """Generate bounded market actions with hard cash/feed/capacity guards."""
    out: list[Candidate] = []
    animal_count = len(state.own.animals())
    wheat_reserve = animal_count * budget.feed_days
    for product, qty in state.own.shed.items():
        reserve = wheat_reserve if product == "WHEAT" and state.day < 28 else 0
        sell = max(0, qty - reserve)
        if sell:
            gain = sell * state.prices.get(product, 0)
            out.append(Candidate("market", ("SELL", product, sell), score(immediate=gain),
                                 "sell bounded shed surplus", immediate_gain=gain))
    # Candidate only: selector still decides whether future production can use it.
    if state.own.cash >= budget.cash_reserve + 10:
        for crop, cost in SEED_COST.items():
            if not state.own.free_cells or state.own.seeds.get(crop, 0) >= 4:
                continue
            future = 3 * state.prices.get(crop, 0)
            if future > cost:
                out.append(Candidate("market", ("BUY_SEED", crop, 1),
                                     score(future=future, cost=cost), "profitable seed with reserve",
                                     cost=cost, future_gain=future))
    out.sort(key=lambda c: (-c.score, c.action))
    return out[:budget.max_market_candidates]
