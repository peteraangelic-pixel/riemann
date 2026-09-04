"""Kaggriculture baseline farmer.

Deterministic, dependency-light heuristic agent (v0 "wheat belt"): a single
main farmer plants wheat on the unlocked NW quadrant, waters daily, harvests at
peak yield, drops produce into the shed and sells it every turn. Later
iterations add carrots, hands, animals and land expansion.

The module is SDK-free on purpose: the game engine only calls ``act`` with a
plain observation dict, so the policy stays pure-python and testable offline.

Submission entry points (Kaggle simulation runner loads ``main.py`` and calls
``act``): ``act(obs, config)`` and the ``agent`` alias for local ``env.run``.
"""

from __future__ import annotations

from typing import Any

# Crops the planner knows how to run (add more in later iterations).
SUPPORTED_CROPS = ("WHEAT", "CARROT")

# Harvest as soon as the crop reaches its max-yield day (with daily watering).
HARVEST_DAY = {"WHEAT": 4, "CARROT": 3}

# Maximum number of simultaneously tended plants. A single farmer walking a
# 5x5 quadrant spends ~1 move per tile, so keeping the belt small and watered
# beats planting everything and letting most of it rot.
MAX_PLANTS = 8

SEED_PRICE = {"WHEAT": 10, "CARROT": 20}

# The four shed-adjacent center tiles on a 10x10 board.
SHED_ADJACENT = {(4, 4), (5, 4), (4, 5), (5, 5)}

SHED_SPOT = (4, 4)


def _is_shed_adjacent(x: int, y: int, board_size: int) -> bool:
    """Mirror of the engine rule: shed access tiles at the quadrant corners."""
    return (x, y) in SHED_ADJACENT and 0 <= x < board_size and 0 <= y < board_size


def _unlocked(x: int, y: int, unlocked_quadrants: list[str]) -> bool:
    """Whether tile (x, y) lies in an unlocked quadrant on the 10x10 board."""
    quadrant = {0: "NW", 1: "NE"}[x // 5]
    if y // 5 == 1:
        quadrant = {0: "SW", 1: "SE"}[x // 5]
    return quadrant in unlocked_quadrants


def _walk(fx: int, fy: int, tx: int, ty: int) -> str | None:
    """One deterministic step toward (tx, ty), or None when already there."""
    if fx < tx:
        return "EAST"
    if fx > tx:
        return "WEST"
    if fy < ty:
        return "SOUTH"
    if fy > ty:
        return "NORTH"
    return None


class FarmerPlanner:
    """Keeps the farmer's short-term plan across turns.

    The engine calls us once per turn with the full observation; we answer
    with exactly one farmer op, zero hands, and market orders. All state here
    is derived from observations plus a tiny amount of episode memory (crop
    mix and whether we are carrying harvested goods back to the shed).
    """

    def __init__(self) -> None:
        self._crop: str | None = None
        self._returning = False

    def decide(self, obs: dict[str, Any]) -> dict[str, Any]:
        player = obs["player"]
        day = obs.get("day", 0)
        me = obs["farms"][player]
        private = obs["private"]
        tiles = me["tiles"]
        board = len(tiles)
        fx, fy = me["farmer"]
        money = me["money"]
        seeds = private["seeds"]
        shed = private["shed"]

        market: list[Any] = []

        # Always sell anything parked in the shed (up to the per-turn order
        # cap; a leftover is sold on a later turn).
        for item in ("WHEAT", "CARROT", "EGG", "MILK", "WOOL", "TOMATO", "STRAWBERRY", "MELON"):
            if shed.get(item, 0) > 0 and len(market) < 10:
                market.append(["SELL", item, shed[item]])

        # Pick the crop once per episode (cheapest reliable staple first).
        if self._crop is None:
            self._crop = "WHEAT"
        crop = self._crop

        # Re-stock seeds when we can afford a full belt.
        have = seeds.get(crop, 0)
        if have < MAX_PLANTS and money >= SEED_PRICE[crop] and len(market) < 10:
            market.append(["BUY_SEED", crop, MAX_PLANTS - have])

        inv = private["inventories"][0] if private.get("inventories") else {}

        # Carrier logic: after a harvest the farmer holds goods; the fastest
        # way to monetise is to deposit them in the shed (then SELL every turn
        # drains the shed automatically).
        if self._returning:
            if _is_shed_adjacent(fx, fy, board):
                op: list[Any] = ["DROP"] if inv else ["PASS"]
                if not inv:
                    self._returning = False
                return {"farmer": op, "hands": [], "market": market}
            move = _walk(fx, fy, *SHED_SPOT)
            return {
                "farmer": [move] if move is not None else ["PASS"],
                "hands": [],
                "market": market,
            }

        plant_count = 0
        best_water: tuple[Any, ...] | None = None
        best_harvest: tuple[Any, ...] | None = None
        best_plant: tuple[int, int] | None = None

        for y in range(board):
            for x in range(board):
                tile = tiles[y][x]
                if isinstance(tile, str):  # "LOCKED"
                    continue
                if tile is None:
                    if _unlocked(x, y, me["unlocked_quadrants"]) and best_plant is None:
                        best_plant = (x, y)
                    continue
                if tile.get("kind") != "PLANT" or tile.get("crop") != crop:
                    continue
                plant_count += 1
                age = day - tile["planted_day"]
                if not tile.get("watered_today") and age >= 0:
                    key = (age, x, y)
                    if best_water is None or key < best_water:
                        best_water = key
                if age >= HARVEST_DAY[crop]:
                    key = (-age, x, y)
                    if best_harvest is None or key < best_harvest:
                        best_harvest = key

        # Farmer op priority: harvest mature plants first, then water, then
        # plant on an empty unlocked tile while seeds remain.
        op: list[Any]
        if best_harvest is not None:
            _, hx, hy = best_harvest
            move = _walk(fx, fy, hx, hy)
            op = ["HARVEST"] if move is None else [move]
        elif best_water is not None:
            _, wx, wy = best_water
            move = _walk(fx, fy, wx, wy)
            op = ["WATER"] if move is None else [move]
        elif best_plant is not None and seeds.get(crop, 0) > 0 and plant_count < MAX_PLANTS:
            px, py = best_plant
            move = _walk(fx, fy, px, py)
            op = ["PLANT", crop] if move is None else [move]
        else:
            move = _walk(fx, fy, *SHED_SPOT)
            op = [move] if move is not None else ["PASS"]

        if op[0] == "HARVEST":
            # We will be carrying produce after this action.
            self._returning = True

        return {"farmer": op, "hands": [], "market": market}


# ---- engine entry points -------------------------------------------------

def act(observation: dict[str, Any], configuration: dict[str, Any]) -> dict[str, Any]:
    """Kaggle simulation-runner entry point."""
    return _PLANNER.decide(observation)


def agent(observation: dict[str, Any], configuration: dict[str, Any]) -> dict[str, Any]:
    """Alias for local ``env.run([agent, ...])``."""
    return act(observation, configuration)


_PLANNER = FarmerPlanner()
