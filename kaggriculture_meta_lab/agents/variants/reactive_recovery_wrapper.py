"""Fail-closed reactive recovery layer for a strong structural base policy.

The wrapper preserves the base action unless the live board proves a local
operation is safer: rescue a dying crop, finish animal care while standing on
it, or use an otherwise idle unit for urgent/endgame work. It is deliberately
small; strategic candidate generation follows only after this identity anchor
clears paired closed-loop gates.
"""
from __future__ import annotations

from typing import Any, Callable

HARVEST_AGE = {"WHEAT": 3, "CARROT": 3, "MELON": 10, "STRAWBERRY": 10, "TOMATO": 8}
ACCESS = {(4, 4), (5, 4), (4, 5), (5, 5)}
EVENING_WATER_HOUR = 17
ENDGAME_DAY = 28
RECOVER_URGENT = True
RECOVER_ENDGAME = True
RECOVER_ANIMALS = True
RECOVER_DROP = True


def _walk(pos: tuple[int, int], target: tuple[int, int]) -> list[str]:
    x, y = pos
    tx, ty = target
    if x < tx:
        return ["EAST"]
    if x > tx:
        return ["WEST"]
    if y < ty:
        return ["SOUTH"]
    if y > ty:
        return ["NORTH"]
    return ["PASS"]


def _near(cells: list[tuple[int, int]], pos: tuple[int, int], claimed: set[tuple[int, int]]) -> tuple[int, int] | None:
    available = [cell for cell in cells if cell not in claimed]
    if not available:
        return None
    target = min(available, key=lambda c: (abs(c[0] - pos[0]) + abs(c[1] - pos[1]), c[1], c[0]))
    claimed.add(target)
    return target


def _local_safe_action(tile: Any, inventory: dict[str, int], day: int, hour: int) -> list[Any] | None:
    """Return only enabled actions with fully visible local preconditions."""
    if not isinstance(tile, dict):
        return None
    if tile.get("kind") == "WEED":
        return ["DIG"] if RECOVER_URGENT else None
    if tile.get("kind") == "PLANT":
        crop = tile.get("crop")
        age = day - int(tile.get("planted_day", day))
        mature = age >= HARVEST_AGE.get(crop, 999) and int(tile.get("yield_units", 0) or 0) > 0
        unwatered = not tile.get("watered_today")
        urgent = int(tile.get("consecutive_unwatered", 0) or 0) >= 1
        if RECOVER_ENDGAME and mature and day >= ENDGAME_DAY:
            return ["HARVEST"]
        if RECOVER_URGENT and unwatered and (urgent or hour >= EVENING_WATER_HOUR):
            return ["WATER"]
        return None
    animal = tile.get("animal")
    if animal and RECOVER_ANIMALS:
        if int(tile.get("yield_units", 0) or 0) > 0:
            return ["HARVEST"]
        if not tile.get("fed_today") and int(inventory.get("WHEAT", 0) or 0) > 0:
            return ["FEED"]
        if not tile.get("cared_today"):
            return ["CARE"]
        if tile.get("fertilizer_available"):
            return ["COLLECT_FERTILIZER"]
    return None


def recover(observation: dict[str, Any], base_action: dict[str, Any]) -> dict[str, Any]:
    """Apply deterministic local safety repairs without changing market orders."""
    player = int(observation.get("player", 0) or 0)
    farms = observation.get("farms") or []
    if player >= len(farms):
        return base_action
    farm = farms[player]
    tiles = farm.get("tiles") or []
    if not tiles:
        return base_action
    day = int(observation.get("day", int(observation.get("step", 0) or 0) // 24) or 0)
    hour = int(observation.get("hour", int(observation.get("step", 0) or 0) % 24) or 0)
    private = observation.get("private") or {}
    inventories = private.get("inventories") or []
    positions = [farm.get("farmer", [4, 4]), *(farm.get("hands") or [])]
    operations = [list(base_action.get("farmer") or ["PASS"])]
    operations.extend(list(op) for op in (base_action.get("hands") or []))
    operations = operations[: len(positions)]
    operations.extend([["PASS"]] * (len(positions) - len(operations)))

    urgent: list[tuple[int, int]] = []
    mature_endgame: list[tuple[int, int]] = []
    for y, row in enumerate(tiles):
        for x, tile in enumerate(row):
            if not isinstance(tile, dict) or tile.get("kind") != "PLANT":
                continue
            if not tile.get("watered_today") and int(tile.get("consecutive_unwatered", 0) or 0) >= 1:
                urgent.append((x, y))
            crop = tile.get("crop")
            age = day - int(tile.get("planted_day", day))
            if day >= ENDGAME_DAY and age >= HARVEST_AGE.get(crop, 999) and int(tile.get("yield_units", 0) or 0) > 0:
                mature_endgame.append((x, y))

    claimed: set[tuple[int, int]] = set()
    for index, raw_pos in enumerate(positions):
        if not isinstance(raw_pos, (list, tuple)) or len(raw_pos) < 2:
            continue
        pos = (int(raw_pos[0]), int(raw_pos[1]))
        x, y = pos
        if y < 0 or y >= len(tiles) or x < 0 or x >= len(tiles[y]):
            continue
        inventory = inventories[index] if index < len(inventories) and isinstance(inventories[index], dict) else {}
        # A locally attractive operation is not automatically safe: replacing
        # one scheduled movement broke the whole structural tape in the first
        # holdout. Recovery therefore owns only genuinely idle units. Invalid
        # base operations are left untouched for now until the exact legality
        # adapter can prove a replacement preserves downstream scheduling.
        if not operations[index] or operations[index][0] != "PASS":
            continue
        local = _local_safe_action(tiles[y][x], inventory, day, hour)
        if local is not None:
            operations[index] = local
            claimed.add(pos)
            continue
        targets = (mature_endgame if RECOVER_ENDGAME else []) if day >= ENDGAME_DAY else (urgent if RECOVER_URGENT else [])
        target = _near(targets, pos, claimed)
        if target is not None:
            operations[index] = _walk(pos, target)
        elif RECOVER_DROP and pos in ACCESS and sum(int(v or 0) for v in inventory.values()) >= 90:
            operations[index] = ["DROP"]

    return {
        "farmer": operations[0] if operations else ["PASS"],
        "hands": operations[1:],
        "market": list(base_action.get("market") or []),
    }


def wrap(base_policy: Callable[..., dict[str, Any]], base_module: Any = None) -> Callable[..., dict[str, Any]]:
    def policy(observation: dict[str, Any], configuration: Any = None) -> dict[str, Any]:
        try:
            base = base_policy(observation, configuration)
        except TypeError:
            base = base_policy(observation)
        return recover(observation, base)

    return policy
