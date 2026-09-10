"""Exact, immutable state estimator for Kaggriculture reactive policies."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

HARVEST_AGE = {"WHEAT": 3, "CARROT": 3, "TOMATO": 8, "STRAWBERRY": 10, "MELON": 10}


@dataclass(frozen=True)
class TileState:
    x: int
    y: int
    kind: str
    crop: str | None = None
    animal: str | None = None
    planted_day: int | None = None
    yield_units: int = 0
    watered: bool = False
    unwatered_days: int = 0
    fed: bool = False
    cared: bool = False
    fertilizer_ready: bool = False
    fertilized_until: int = -1

    @property
    def position(self) -> tuple[int, int]:
        return self.x, self.y

    def mature(self, day: int) -> bool:
        return bool(self.crop and self.planted_day is not None
                    and day - self.planted_day >= HARVEST_AGE.get(self.crop, 999)
                    and self.yield_units > 0)


@dataclass(frozen=True)
class UnitState:
    index: int
    role: str
    position: tuple[int, int]
    inventory: dict[str, int]

    @property
    def load(self) -> int:
        return sum(self.inventory.values())


@dataclass(frozen=True)
class FarmState:
    player: int
    cash: float
    hands: int
    unlocked: tuple[str, ...]
    seeds: dict[str, int]
    shed: dict[str, int]
    units: tuple[UnitState, ...]
    tiles: tuple[TileState, ...]
    free_cells: tuple[tuple[int, int], ...]
    locked_cells: tuple[tuple[int, int], ...]

    def crops(self, crop: str | None = None) -> tuple[TileState, ...]:
        return tuple(t for t in self.tiles if t.crop and (crop is None or t.crop == crop))

    def animals(self, animal: str | None = None) -> tuple[TileState, ...]:
        return tuple(t for t in self.tiles if t.animal and (animal is None or t.animal == animal))

    def structures(self, kind: str | None = None) -> tuple[TileState, ...]:
        return tuple(t for t in self.tiles if t.kind in {"PASTURE", "COOP"}
                     and (kind is None or t.kind == kind))


@dataclass(frozen=True)
class GameState:
    player: int
    step: int
    day: int
    hour: int
    own: FarmState
    opponent: FarmState
    prices: dict[str, float]
    market_inventory: dict[str, int]
    shops: tuple[str, ...]
    turns_per_day: int
    shed_capacity: int

    @property
    def remaining_days(self) -> int:
        return max(0, 29 - self.day)


def _int_map(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    return {str(k): int(v or 0) for k, v in value.items() if isinstance(v, (int, float))}


def _tile(x: int, y: int, raw: Any) -> TileState | None:
    if not isinstance(raw, dict):
        return None
    return TileState(
        x=x, y=y, kind=str(raw.get("kind") or "UNKNOWN"),
        crop=str(raw["crop"]) if raw.get("crop") else None,
        animal=str(raw["animal"]) if raw.get("animal") else None,
        planted_day=int(raw["planted_day"]) if isinstance(raw.get("planted_day"), (int, float)) else None,
        yield_units=int(raw.get("yield_units", 0) or 0),
        watered=bool(raw.get("watered_today")),
        unwatered_days=int(raw.get("consecutive_unwatered", 0) or 0),
        fed=bool(raw.get("fed_today")), cared=bool(raw.get("cared_today")),
        fertilizer_ready=bool(raw.get("fertilizer_available")),
        fertilized_until=(int(raw["fertilized_until_day"])
                          if isinstance(raw.get("fertilized_until_day"), (int, float)) else -1),
    )


def _farm(observation: dict[str, Any], player: int, private: dict[str, Any] | None) -> FarmState:
    farms = observation.get("farms") or []
    raw = farms[player] if player < len(farms) and isinstance(farms[player], dict) else {}
    board = raw.get("tiles") or []
    tiles: list[TileState] = []
    free: list[tuple[int, int]] = []
    locked: list[tuple[int, int]] = []
    for y, row in enumerate(board):
        if not isinstance(row, list):
            continue
        for x, value in enumerate(row):
            if value is None:
                free.append((x, y))
            elif value == "LOCKED":
                locked.append((x, y))
            else:
                parsed = _tile(x, y, value)
                if parsed:
                    tiles.append(parsed)
    private = private or {}
    inventories = private.get("inventories") or []
    positions = [raw.get("farmer", [4, 4]), *(raw.get("hands") or [])]
    units = []
    for index, position in enumerate(positions):
        if not isinstance(position, (list, tuple)) or len(position) < 2:
            continue
        inventory = inventories[index] if index < len(inventories) else {}
        units.append(UnitState(index, "farmer" if index == 0 else "hand",
                               (int(position[0]), int(position[1])), _int_map(inventory)))
    return FarmState(
        player=player, cash=float(raw.get("money", 0) or 0),
        hands=len(raw.get("hands") or []),
        unlocked=tuple(str(q) for q in (raw.get("unlocked_quadrants") or [])),
        seeds=_int_map(private.get("seeds")), shed=_int_map(private.get("shed")),
        units=tuple(units), tiles=tuple(tiles), free_cells=tuple(free), locked_cells=tuple(locked),
    )


def estimate(observation: dict[str, Any], configuration: Any = None) -> GameState:
    """Convert the exact framework observation into a stable policy state."""
    player = int(observation.get("player", 0) or 0)
    turns = int((configuration or {}).get("turnsPerDay", 24) if isinstance(configuration, dict)
                else getattr(configuration, "turnsPerDay", 24) or 24)
    step = int(observation.get("step", 0) or 0)
    day = int(observation.get("day", step // turns) or 0)
    hour = int(observation.get("hour", step % turns) or 0)
    private = observation.get("private") if isinstance(observation.get("private"), dict) else {}
    market = observation.get("market") if isinstance(observation.get("market"), dict) else {}
    town = observation.get("town") if isinstance(observation.get("town"), dict) else {}
    prices = {str(k): float(v or 0) for k, v in (market.get("prices") or {}).items()}
    capacity = int((configuration or {}).get("shedCapacity", 100) if isinstance(configuration, dict)
                   else getattr(configuration, "shedCapacity", 100) or 100)
    return GameState(
        player=player, step=step, day=day, hour=hour,
        own=_farm(observation, player, private), opponent=_farm(observation, 1 - player, None),
        prices=prices, market_inventory=_int_map(market.get("inventory")),
        shops=tuple(str(s) for s in (town.get("unlocked_shops") or [])),
        turns_per_day=turns, shed_capacity=capacity,
    )
