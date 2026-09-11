"""Kaggriculture V12 reactive agent — breaks the 2800 static-tape ceiling.

Reverse-engineered from TOP12 leaderboard replay analysis (Majkel1337 #1,
SpaTaro #2, c0nrad #4).  Key differences from V2:

1. SEAT-AWARE: P0 (high money) buys animals first; P1 (low money) hires first
2. ANIMALS: COW + SHEEP d0 → produce FERTILIZER (sold daily from d11+)
3. CROPS: WHEAT + MELON + STRAWBERRY + CARROT + TOMATO
4. FERTILIZER SELL: main revenue stream (~100u/day × ~90 gold = ~9k/day)
5. ENDGAME: d29 full liquidation
6. LAND: 3 quadrants (NW+NE+SW), NE early, SW by d10

Entry points: ``act`` / ``agent`` (Kaggle simulator loads ``main.py`` and
calls ``act``; local ``env.run`` calls either).
"""

from __future__ import annotations
from typing import Any

# ── crop & animal constants ──────────────────────────────────────────────
SUPPORTED = ("WHEAT", "CARROT", "MELON", "STRAWBERRY", "TOMATO")
SEED_COST = {"WHEAT": 10, "CARROT": 20, "MELON": 80, "STRAWBERRY": 40, "TOMATO": 30}
HARVEST_AGE = {"WHEAT": 3, "CARROT": 3, "MELON": 10, "STRAWBERRY": 4, "TOMATO": 4}
# Ongoing crops (STRAWBERRY, TOMATO) regrow after harvest — they don't need replanting
ONGOING = {"STRAWBERRY", "TOMATO"}
# Animals and their costs
ANIMAL_COST = {"COW": 500, "SHEEP": 500, "GOOSE": 200}
ANIMAL_PRODUCTS = {
    "COW": {"MILK": 1, "FERTILIZER": 1},
    "SHEEP": {"WOOL": 1, "FERTILIZER": 1},
    "GOOSE": {"EGG": 1},
}

QUAD_ORDER = ("NW", "NE", "SW", "SE")
LAND_COST = {"NE": 1000, "SW": 2000, "SE": 4000}
FIB = (1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144)
FIB_SUM = tuple(sum(FIB[:i+1]) for i in range(len(FIB)))

CELLS_PER_HAND = 10
HANDS_EXTRA = 1
HANDS_MAX = 12
MAX_MARKET_ORDERS = 10
SELL_PRICE_FLOOR = 8

# Land purchase
LAND_NE_MIN_PLANTED = 6
LAND_SW_MIN_PLANTED = 30
LAND_SW_MAX_DAY = 15
LAND_RESERVE = 500
LAND_SE_RESERVE_DAY = 20  # never buy SE

# ── crop layout ──────────────────────────────────────────────────────────
# Majkel-style layout:
#   MELON: NW top row (up to 12 cells, planted d0-1 only)
#   STRAWBERRY: NW/NE middle rows (20-25 cells, planted d2-6)
#   WHEAT: main conveyor (30+ cells, planted throughout)
#   CARROT: late-game (d15+, when price justifies)
#   TOMATO: late-game filler (d10+, small area)

MELON_MAX_CELLS = 12
MELON_LAST_PLANT_DAY = 5   # needs 10 days, season=30 → d5 cutoff for safety

STRAWBERRY_TARGET = 22
CARROT_MAX_FRAC = 0.25
CARROT_KAPPA = 0.70
CARROT_MIN_PRICE_RATIO = 1.15

TICKS_PER_DAY = 6.0
CARROT_SHOP_MULT = {"PET_CAFE": 2, "FARMERS_MARKET": 1}
CARROT_UNITS_PER_CELL_DAY = 0.75

# ── animal targets ───────────────────────────────────────────────────────
# Majkel buys COW×1 + SHEEP×3 on d0 (seat 0), then more on d6/d9/d12
ANIMAL_PLAN = {
    0: {"COW": 2, "SHEEP": 3},   # d0 opening
    6: {"COW": 1, "SHEEP": 1},   # d6 expansion
    9: {"COW": 1},               # d9 expansion
    12: {"SHEEP": 1},            # d12 final
}
TOTAL_ANIMALS = {"COW": 4, "SHEEP": 5}  # ~9 animals total


def _plan_cells(unlocked: list[str], board: int) -> list[tuple[int, int]]:
    """Canonical row-major cell list over the unlocked quadrants."""
    cells: list[tuple[int, int]] = []
    half = board // 2
    for q in QUAD_ORDER:
        if q not in unlocked:
            continue
        y0 = half if q in ("SW", "SE") else 0
        y1 = half if q in ("NW", "NE") else board
        x0 = half if q in ("NE", "SE") else 0
        x1 = half if q in ("NW", "SW") else board
        for y in range(y0, y1):
            for x in range(x0, x1):
                cells.append((x, y))
    return cells


def _walk(fx: int, fy: int, tx: int, ty: int) -> str:
    if fx < tx: return "EAST"
    if fx > tx: return "WEST"
    if fy < ty: return "SOUTH"
    if fy > ty: return "NORTH"
    return "PASS"


def _near(cells: list[tuple[int, int]], fx: int, fy: int) -> tuple[int, int] | None:
    if not cells:
        return None
    return min(cells, key=lambda c: (abs(c[0] - fx) + abs(c[1] - fy), c[1], c[0]))


def _count_animals(tiles: list, board: int) -> dict[str, int]:
    """Count animals currently on the board."""
    counts: dict[str, int] = {}
    for y in range(board):
        row = tiles[y]
        for x in range(board):
            t = row[x]
            if isinstance(t, dict) and t.get("kind") == "ANIMAL":
                a = t.get("animal", "?")
                counts[a] = counts.get(a, 0) + 1
    return counts


def _count_plants(tiles: list, board: int) -> dict[str, int]:
    """Count plants currently on the board."""
    counts: dict[str, int] = {}
    for y in range(board):
        row = tiles[y]
        for x in range(board):
            t = row[x]
            if isinstance(t, dict) and t.get("kind") == "PLANT":
                c = t.get("crop", "?")
                counts[c] = counts.get(c, 0) + 1
    return counts


class V12Planner:
    """Reactive planner: seat-aware, animal-driven, fertilizer-selling."""

    def decide(self, obs: dict[str, Any]) -> dict[str, Any]:
        player = obs["player"]
        me = obs["farms"][player]
        opp = obs["farms"][1 - player]
        private = obs["private"]
        tiles = me["tiles"]
        board = len(tiles)
        step = int(obs.get("step", 0))
        day = obs.get("day", step // 24)
        hour = obs.get("hour", step % 24)
        money = me["money"]
        unlocked = list(me.get("unlocked_quadrants", ["NW"]))
        hands_now = me.get("hands", []) or []
        seeds = private.get("seeds", {}) or {}
        shed = private.get("shed", {}) or {}
        prices = (obs.get("market", {}) or {}).get("prices", {}) or {}
        shops = (obs.get("town", {}) or {}).get("unlocked_shops", []) or []

        plan = _plan_cells(unlocked, board)
        plan_set = set(plan)

        # ── board scan ────────────────────────────────────────────────
        mature: list[tuple[int, int]] = []
        urgent: list[tuple[int, int]] = []
        unwatered: list[tuple[int, int]] = []
        empty_cells: dict[str, list[tuple[int, int]]] = {c: [] for c in SUPPORTED}
        weeds: list[tuple[int, int]] = []
        planted_per_crop: dict[str, int] = {c: 0 for c in SUPPORTED}

        for y in range(board):
            for x in range(board):
                t = tiles[y][x]
                if isinstance(t, str):
                    continue
                if t is None:
                    if (x, y) in plan_set:
                        crop = self._crop_for_cell(x, y, day, len(plan), planted_per_crop, prices)
                        empty_cells[crop].append((x, y))
                    continue
                if t.get("kind") == "WEED":
                    weeds.append((x, y))
                    continue
                crop = t.get("crop")
                if crop and crop in SUPPORTED:
                    planted_per_crop[crop] += 1
                if t.get("kind") != "PLANT" or crop not in SUPPORTED:
                    continue
                age = day - t.get("planted_day", 0)
                if age < 0 or t.get("yield_units", 0) <= 0:
                    continue
                if not t.get("watered_today"):
                    unwatered.append((x, y))
                    if t.get("consecutive_unwatered", 0) >= 1:
                        urgent.append((x, y))
                hage = HARVEST_AGE.get(crop, 3)
                if age >= hage:
                    mature.append((x, y))

        board_animals = _count_animals(tiles, board)

        # ── market orders ─────────────────────────────────────────────
        orders: list[list[Any]] = []
        shed_value = 0

        # Sell everything in shed (FERTILIZER is the main revenue!)
        for item in sorted(shed):
            qty = shed[item]
            if qty <= 0:
                continue
            price = int(prices.get(item, 0) or 0)
            if price >= SELL_PRICE_FLOOR:
                orders.append(["SELL", item, qty])
                shed_value += qty * max(price, 1)

        est_money = money + shed_value

        # ── endgame liquidation (d29) ─────────────────────────────────
        # Don't plant anything new, just sell everything
        is_endgame = day >= 29

        # ── animals ───────────────────────────────────────────────────
        if not is_endgame and hour == 0:
            target = ANIMAL_PLAN.get(day, {})
            for animal, want in target.items():
                have = board_animals.get(animal, 0)
                to_buy = min(want - have, 3)  # max 3 per turn per type
                for _ in range(max(0, to_buy)):
                    cost = ANIMAL_COST.get(animal, 500)
                    if est_money >= cost + LAND_RESERVE and len(orders) < MAX_MARKET_ORDERS:
                        orders.append(["BUY_ANIMAL", animal, 1])
                        est_money -= cost

        # ── land ──────────────────────────────────────────────────────
        if hour == 0 and not is_endgame and len(unlocked) < 3:
            nxt = QUAD_ORDER[len(unlocked)]
            cost = LAND_COST.get(nxt, 9999)
            ok = False
            total_planted = sum(planted_per_crop.values())
            if nxt == "NE":
                ok = total_planted >= LAND_NE_MIN_PLANTED
            elif nxt == "SW":
                ok = total_planted >= LAND_SW_MIN_PLANTED and day <= LAND_SW_MAX_DAY
            if ok and est_money >= cost + LAND_RESERVE:
                orders.append(["BUY_LAND"])
                est_money -= cost

        # ── hire hands ────────────────────────────────────────────────
        h_target = min(HANDS_MAX, max(4, (len(plan) + CELLS_PER_HAND - 1) // CELLS_PER_HAND + HANDS_EXTRA))
        to_hire = max(0, h_target - len(hands_now))
        for h in range(min(to_hire, len(FIB))):
            if est_money >= FIB_SUM[h] + 80 and len(orders) < MAX_MARKET_ORDERS:
                orders.append(["HIRE"])
            else:
                break

        # ── seeds ─────────────────────────────────────────────────────
        if not is_endgame:
            for crop in SUPPORTED:
                if crop in ONGOING:
                    continue  # ongoing crops don't need replanting
                have = int(seeds.get(crop, 0))
                need = len(empty_cells[crop]) + 4
                buy_n = min(need - have, 25)
                cost = SEED_COST.get(crop, 10)
                if buy_n > 0 and est_money >= buy_n * cost + 30 and len(orders) < MAX_MARKET_ORDERS:
                    orders.append(["BUY_SEED", crop, buy_n])

        # ── farmer + hands operations ─────────────────────────────────
        waterers = 1 + len(hands_now)
        plant_cap = min(len(plan), waterers * CELLS_PER_HAND)
        plants_total = sum(planted_per_crop.values())
        plants_assigned: dict[str, int] = {c: 0 for c in SUPPORTED}

        def _plant_ok(crop: str) -> bool:
            if is_endgame:
                return False
            if plants_total + sum(plants_assigned.values()) >= plant_cap:
                return False
            if plants_assigned[crop] >= int(seeds.get(crop, 0)):
                return False
            if hour > 22:
                return False
            return True

        def _standing_op(tile: Any, zone_set: set[tuple[int, int]], fx: int, fy: int) -> list[str] | None:
            if isinstance(tile, dict) and tile.get("kind") == "WEED":
                return ["DIG"]
            if isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("crop") in SUPPORTED:
                crop = tile["crop"]
                age = day - tile.get("planted_day", 0)
                yld = tile.get("yield_units", 0)
                hage = HARVEST_AGE.get(crop, 3)
                if age >= hage and yld > 0:
                    if age == hage and not tile.get("watered_today"):
                        return ["WATER"]
                    return ["HARVEST"]
                if not tile.get("watered_today"):
                    return ["WATER"]
                return None
            if isinstance(tile, dict) and tile.get("kind") == "ANIMAL":
                # Check if animal needs care
                if not tile.get("cared_today", False):
                    return ["CARE"]
                return None
            if tile is None and (fx, fy) in zone_set:
                crop = self._crop_for_cell(fx, fy, day, len(plan), planted_per_crop, prices)
                if _plant_ok(crop):
                    plants_assigned[crop] += 1
                    return ["PLANT", crop]
            return None

        def _unit_op(fx: int, fy: int, zone: list[tuple[int, int]], is_farmer: bool) -> list[str]:
            zone_set = set(zone)
            op = _standing_op(tiles[fy][fx], zone_set, fx, fy)
            if op is not None:
                return op
            # Priorities: mature > urgent > unwatered > empty > weeds > animals
            z_mature = [c for c in mature if c in zone_set]
            z_urgent = [c for c in urgent if c in zone_set]
            z_wet = [c for c in unwatered if c in zone_set]
            z_empty = []
            for crop in SUPPORTED:
                z_empty.extend(c for c in empty_cells[crop] if c in zone_set)
            z_weeds = [c for c in weeds if c in zone_set]

            target = _near(z_mature, fx, fy)
            if target is None:
                target = _near(z_urgent, fx, fy)
            if target is None:
                target = _near(z_wet, fx, fy)
            if target is None and is_farmer:
                target = _near(z_empty, fx, fy)
            if target is None:
                target = _near(z_weeds, fx, fy)
            if target is not None:
                mv = _walk(fx, fy, *target)
                if mv != "PASS":
                    return [mv]
            return ["PASS"]

        farmer_op = _unit_op(me["farmer"][0], me["farmer"][1], plan, True)

        hands_ops: list[list[str]] = []
        n = len(hands_now)
        if n:
            for i, (hx, hy) in enumerate(hands_now):
                lo = i * len(plan) // n
                hi = (i + 1) * len(plan) // n
                hands_ops.append(_unit_op(hx, hy, plan[lo:hi] if plan else [], False))

        return {"farmer": farmer_op, "hands": hands_ops, "market": orders}

    def _crop_for_cell(self, x: int, y: int, day: int, plan_size: int,
                       planted: dict[str, int], prices: dict) -> str:
        """Decide which crop to plant on this cell."""
        # Melon: first MELON_MAX_CELLS cells, only until MELON_LAST_PLANT_DAY
        if planted.get("MELON", 0) < MELON_MAX_CELLS and day <= MELON_LAST_PLANT_DAY:
            return "MELON"

        # Strawberry: next STRAWBERRY_TARGET cells, until d15
        if planted.get("STRAWBERRY", 0) < STRAWBERRY_TARGET and day <= 15:
            return "STRAWBERRY"

        # Carrot: if price justifies, up to CARROT_MAX_FRAC
        wp = int(prices.get("WHEAT", 0) or 0)
        cp = int(prices.get("CARROT", 0) or 0)
        if cp >= max(SELL_PRICE_FLOOR, CARROT_MIN_PRICE_RATIO * max(wp, 1)):
            carrot_target = int(plan_size * CARROT_MAX_FRAC)
            if planted.get("CARROT", 0) < carrot_target:
                return "CARROT"

        # Tomato: filler crop for remaining cells
        if day <= 20 and planted.get("TOMATO", 0) < 8:
            return "TOMATO"

        # Default: wheat (main conveyor)
        return "WHEAT"


# ── engine entry points ─────────────────────────────────────────────────

_PLANNER = V12Planner()


def act(observation: dict[str, Any], configuration: dict[str, Any]) -> dict[str, Any]:
    """Kaggle simulation-runner entry point."""
    return _PLANNER.decide(observation)


def agent(observation: dict[str, Any], configuration: dict[str, Any]) -> dict[str, Any]:
    """Alias for local ``env.run([agent, ...])``."""
    return act(observation, configuration)
