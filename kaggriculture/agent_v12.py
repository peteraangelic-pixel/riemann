"""Kaggriculture V12 reactive agent: enhanced V2 with TOP12 patterns.

V2 foundation: hands-powered wheat/carrot/melon conveyor with reactive crop
layout and market selling.

V12 additions (reverse-engineered from Majkel1337 #1, SpaTaro #2, c0nrad #4):
1. ANIMALS: COW + SHEEP from d0 → produce FERTILIZER, MILK, WOOL, EGG
2. CROPS: +STRAWBERRY (ongoing, high-value) + TOMATO (late filler)
3. FERTILIZER: main revenue stream (sold from shed daily)
4. ENDGAME: d29 liquidation — stop planting, sell everything
5. LAND: NE earlier (d0-3), SW by d8-10

Entry points: ``act`` / ``agent`` (Kaggle simulator loads ``main.py`` and
calls ``act``; local ``env.run`` calls either).
"""

from __future__ import annotations

from typing import Any

# Crops: WHEAT (age3, 3u), CARROT (age3, 3u), MELON (age10, 6u),
#        STRAWBERRY (ongoing, regrows), TOMATO (ongoing, regrows)
SUPPORTED = ("WHEAT", "CARROT", "MELON", "STRAWBERRY", "TOMATO")
SEED_COST = {"WHEAT": 10, "CARROT": 20, "MELON": 80, "STRAWBERRY": 40, "TOMATO": 30}
# Ongoing crops regrow after harvest — don't replant them
ONGOING_CROPS = {"STRAWBERRY", "TOMATO"}
# First harvestable age per crop.
HARVEST_AGE_BY_CROP = {"WHEAT": 3, "CARROT": 3, "MELON": 10, "STRAWBERRY": 4, "TOMATO": 4}

# ── animal constants ──────────────────────────────────────────────────
ANIMAL_COST = {"COW": 500, "SHEEP": 500, "GOOSE": 200}
# Animals we want to buy by day (cumulative targets)
# V12: delay animals until d3+ (after first wheat harvest provides cash)
ANIMAL_BUY_PLAN = {
    3: {"COW": 1, "SHEEP": 1},   # d3 (wheat harvest money arrives)
    6: {"COW": 1, "SHEEP": 1},   # d6 (melon money + more wheat)
    9: {"COW": 1, "SHEEP": 1},   # d9
    12: {"COW": 1, "SHEEP": 1},  # d12
}
# Same plan for both seats — the difference is timing (low-money seat
# may not afford d3 animals, agent handles this naturally via est_money check)
ANIMAL_BUY_PLAN_SEAT1 = ANIMAL_BUY_PLAN

QUAD_ORDER = ("NW", "NE", "SW", "SE")
LAND_COST = {"NE": 1000, "SW": 2000, "SE": 4000}
# Cumulative daily cost of hiring 1..10 hands (fib 1,1,2,3,5,8,13,21,34,55).
FIB_SUM = (1, 2, 4, 7, 12, 20, 33, 54, 88, 143)

# Hands roughly sustain ~10 cells/day each (water + tour + occasional
# harvest/replant); we also count the farmer as one waterer.
CELLS_PER_HAND = 10
HANDS_EXTRA = 1
HANDS_MAX = 12

# Never queue more than this many market orders per turn.
MAX_MARKET_ORDERS = 14   # V12: more orders needed for animals+fertilizer

# Selling below this would mean a crashed market.
SELL_PRICE_FLOOR = 8    # V12: slightly lower floor to sell more fertilizer

# Land purchase triggers — V12: earlier NE, earlier SW
LAND_NE_MIN_PLANTED = 4       # V12: buy NE sooner (was 6)
LAND_SW_MIN_PLANTED = 25      # V12: buy SW sooner (was 40)
LAND_SW_MAX_DAY = 15          # V12: earlier deadline (was 18)
LAND_RESERVE = 400            # V12: lower reserve (was 700)
SELL_BUY = False              # SE quadrant purchase disabled

# Carrot belt sizing
CARROT_KAPPA = 0.70
CARROT_MAX_FRAC = 0.25        # V12: smaller carrot belt (was 0.40)
CARROT_MIN_PRICE_RATIO = 1.15

TICKS_PER_DAY = 6.0
CARROT_SHOP_MULT = {"PET_CAFE": 2, "FARMERS_MARKET": 1}
CARROT_UNITS_PER_CELL_DAY = 0.75

# V12: Strawberry target — high-value ongoing crop
STRAWBERRY_TARGET = 20        # ~20 cells of strawberry
STRAWBERRY_MAX_DAY = 15       # stop planting after d15
TOMATO_TARGET = 6             # small tomato area
TOMATO_MAX_DAY = 20           # stop planting after d20

# Melon cells — V12: more melons (12 instead of 4)
MELON_CELLS = [(x, 0) for x in range(12)]  # NW top row
MELON_LAST_PLANT_DAY = 5      # V12: tighter window (was 19)
MELON_MAX_CELLS = 12


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
    """One deterministic step toward (tx, ty)."""
    if fx < tx:
        return "EAST"
    if fx > tx:
        return "WEST"
    if fy < ty:
        return "SOUTH"
    if fy > ty:
        return "NORTH"
    return "PASS"


def _near(cells: list[tuple[int, int]], fx: int, fy: int) -> tuple[int, int] | None:
    """Nearest cell by Manhattan distance; ties by canonical order."""
    if not cells:
        return None
    return min(cells, key=lambda c: (abs(c[0] - fx) + abs(c[1] - fy), c[1], c[0]))


class FarmerPlanner:
    """Deterministic, stateless planner shared by farmer and hired hands.

    No episode memory: every decision is a pure function of the observation
    (plan = currently unlocked quadrants, crop = cell rank + town demand).
    """

    def decide(self, obs: dict[str, Any]) -> dict[str, Any]:
        player = obs["player"]
        me = obs["farms"][player]
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
        rank_map = {cell: i for i, cell in enumerate(plan)}

        # ---- crop layout ----------------------------------------------------
        carrot_demand_per_day = sum(
            TICKS_PER_DAY * CARROT_SHOP_MULT.get(s, 0) for s in shops
        )
        carrot_cells_max = min(len(plan), int(len(plan) * CARROT_MAX_FRAC))
        carrot_target = min(
            carrot_cells_max,
            int(CARROT_KAPPA * carrot_demand_per_day / CARROT_UNITS_PER_CELL_DAY),
        )
        # Replant gate: carrot only while its price still beats wheat clearly.
        wp = int(prices.get("WHEAT", 0) or 0)
        cp = int(prices.get("CARROT", 0) or 0)
        carrot_ok = cp >= max(SELL_PRICE_FLOOR, CARROT_MIN_PRICE_RATIO * max(wp, 1))

        def _crop_of_cell(x: int, y: int, rank: int | None) -> str:
            """V12 crop assignment: MELON → STRAWBERRY → CARROT → TOMATO → WHEAT."""
            # Melon: first MELON_MAX_CELLS cells in NW top row, only until d5
            if (x, y) in MELON_CELLS and day <= MELON_LAST_PLANT_DAY:
                if planted_per_crop.get("MELON", 0) < MELON_MAX_CELLS:
                    return "MELON"
            # Strawberry: high-value ongoing crop, target ~20 cells
            if (planted_per_crop.get("STRAWBERRY", 0) +
                planted_per_crop.get("TOMATO", 0)) < STRAWBERRY_TARGET and day <= STRAWBERRY_MAX_DAY:
                return "STRAWBERRY"
            # Carrot: if price justifies
            if rank is not None and carrot_ok and rank < carrot_target:
                return "CARROT"
            # Tomato: small filler area
            if planted_per_crop.get("TOMATO", 0) < TOMATO_TARGET and day <= TOMATO_MAX_DAY:
                return "TOMATO"
            # Default: wheat
            return "WHEAT"

        def _rank_of(x: int, y: int) -> int | None:
            return rank_map.get((x, y))

        # ---- single board scan: collect what every unit needs -------------
        mature: list[tuple[int, int]] = []      # plants at/over harvest age
        urgent: list[tuple[int, int]] = []      # unwatered, will die tonight
        unwatered: list[tuple[int, int]] = []   # any unwatered supported plant
        empty_cells: dict[str, list[tuple[int, int]]] = {c: [] for c in SUPPORTED}
        weeds: list[tuple[int, int]] = []
        planted_per_crop = {c: 0 for c in SUPPORTED}
        for y in range(board):
            for x in range(board):
                t = tiles[y][x]
                if isinstance(t, str):
                    continue
                if t is None:
                    if (x, y) in plan_set:
                        r = _rank_of(x, y)
                        crop = _crop_of_cell(x, y, r)
                        empty_cells[crop].append((x, y))
                    continue
                if t.get("kind") == "WEED":
                    weeds.append((x, y))
                    continue
                crop = t.get("crop")
                if t.get("kind") != "PLANT" or crop not in SUPPORTED:
                    continue
                planted_per_crop[crop] += 1
                age = day - t["planted_day"]
                if age < 0 or t.get("yield_units", 0) <= 0:
                    continue
                if not t.get("watered_today"):
                    unwatered.append((x, y))
                    if t.get("consecutive_unwatered", 0) >= 1:
                        urgent.append((x, y))
                if age >= HARVEST_AGE_BY_CROP.get(crop, HARVEST_AGE_BY_CROP["WHEAT"]):
                    mature.append((x, y))

        # ---- market orders -------------------------------------------------
        orders: list[list[Any]] = []
        shed_value = 0
        for item in sorted(shed):
            qty = shed[item]
            if qty <= 0:
                continue
            price = int(prices.get(item, 0) or 0)
            if price >= SELL_PRICE_FLOOR:
                orders.append(["SELL", item, qty])
                shed_value += qty * max(price, 1)

        est_money = money + shed_value

        # Land: buy the next quadrant when the current one is mostly planted.
        if hour == 0 and len(unlocked) < len(QUAD_ORDER):
            nxt = QUAD_ORDER[len(unlocked)]
            cost = LAND_COST[nxt]
            ok = False
            if nxt == "NE":
                ok = sum(planted_per_crop.values()) >= LAND_NE_MIN_PLANTED
            elif nxt == "SW":
                ok = sum(planted_per_crop.values()) >= LAND_SW_MIN_PLANTED and day <= LAND_SW_MAX_DAY
            elif nxt == "SE":
                ok = SELL_BUY  # disabled by default (module docstring)
            if ok and est_money >= cost + LAND_RESERVE:
                orders.append(["BUY_LAND"])

        # Hands: hire at hour 0 up to a zone-size-derived target.
        h_target = min(HANDS_MAX, max(2, (len(plan) + CELLS_PER_HAND - 1) // CELLS_PER_HAND + HANDS_EXTRA))
        to_hire = max(0, h_target - len(hands_now))
        for h in range(min(to_hire, len(FIB_SUM))):
            if est_money >= FIB_SUM[h] + 120:
                orders.append(["HIRE"])
            else:
                break

        # V12: Animals — buy according to plan (seat-aware)
        is_endgame = day >= 29
        if not is_endgame and hour == 0:
            # Detect seat: P0 starts with ~2464, P1 with ~191-424
            is_high_money = money > 1000 or (money > 800 and day == 0)
            animal_plan = ANIMAL_BUY_PLAN if is_high_money else ANIMAL_BUY_PLAN_SEAT1
            day_target = animal_plan.get(day, {})
            if day_target:
                # Count current animals on board
                board_animals: dict[str, int] = {}
                for yy in range(board):
                    for xx in range(board):
                        tt = tiles[yy][xx]
                        if isinstance(tt, dict) and tt.get("kind") == "ANIMAL":
                            aa = tt.get("animal", "?")
                            board_animals[aa] = board_animals.get(aa, 0) + 1
                for animal, want in day_target.items():
                    have = board_animals.get(animal, 0)
                    to_buy = max(0, want - have)
                    for _ in range(min(to_buy, 3)):
                        cost = ANIMAL_COST.get(animal, 500)
                        if est_money >= cost + LAND_RESERVE and len(orders) < MAX_MARKET_ORDERS:
                            orders.append(["BUY_ANIMAL", animal, 1])
                            est_money -= cost

        # V12: Endgame — stop buying seeds/animals, just sell everything
        if is_endgame:
            # Don't buy new seeds in endgame
            pass  # seeds section below will be skipped

        # Seeds per crop: enough for every planned empty cell plus a reserve.
        for crop in SUPPORTED:
            # V12: skip seed buying in endgame
            if is_endgame:
                continue
            have = int(seeds.get(crop, 0))
            # For ongoing crops, only buy if we have fewer seeds than target
            if crop in ONGOING_CROPS:
                target_cells = STRAWBERRY_TARGET if crop == "STRAWBERRY" else TOMATO_TARGET
                seed_need = max(0, target_cells - planted_per_crop.get(crop, 0) - have)
            else:
                seed_need = len(empty_cells[crop]) + 4
            buy_n = min(seed_need - have if crop not in ONGOING_CROPS else seed_need, 25)
            if buy_n > 0 and est_money >= buy_n * SEED_COST[crop] + 30 and len(orders) < MAX_MARKET_ORDERS:
                orders.append(["BUY_SEED", crop, buy_n])

        # ---- decide ops for every unit --------------------------------------
        # Cap on simultaneous plants and per-crop seed budget (the engine drops
        # ALL plant ops of a crop if requests exceed that crop's seeds).
        waterers = 1 + len(hands_now)
        plant_cap = min(len(plan), waterers * CELLS_PER_HAND)
        plants_total = sum(planted_per_crop.values())
        plants_assigned = {c: 0 for c in SUPPORTED}

        def _plant_ok(crop: str) -> bool:
            if is_endgame:
                return False
            if plants_total + sum(plants_assigned.values()) >= plant_cap:
                return False
            # V12: ongoing crops don't need seeds (they regrow)
            if crop not in ONGOING_CROPS:
                if plants_assigned[crop] >= int(seeds.get(crop, 0)):
                    return False
            if hour > 22:
                return False
            return True

        def _standing_op(tile: Any, zone_set: set[tuple[int, int]], fx: int, fy: int) -> list[str] | None:
            """Action on the tile we stand on, or None if nothing to do here."""
            if isinstance(tile, dict) and tile.get("kind") == "WEED":
                return ["DIG"]
            if isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("crop") in SUPPORTED:
                age = day - tile["planted_day"]
                yld = tile.get("yield_units", 0)
                hage = HARVEST_AGE_BY_CROP.get(tile["crop"], HARVEST_AGE_BY_CROP["WHEAT"])
                if age >= hage and yld > 0:
                    if age == hage and not tile.get("watered_today"):
                        # Watering on the first harvestable day adds a unit.
                        return ["WATER"]
                    return ["HARVEST"]
                if not tile.get("watered_today"):
                    return ["WATER"]
                return None
            # V12: care for animals when standing on them
            if isinstance(tile, dict) and tile.get("kind") == "ANIMAL":
                if not tile.get("cared_today", False):
                    return ["CARE"]
                return None
            if tile is None and (fx, fy) in zone_set:
                # V12: don't replant ongoing crop cells (they regrow)
                r = _rank_of(fx, fy)
                crop = _crop_of_cell(fx, fy, r)
                if _plant_ok(crop):
                    plants_assigned[crop] += 1
                    return ["PLANT", crop]
            return None

        def _farm_op(fx: int, fy: int, zone: list[tuple[int, int]]) -> list[str]:
            """Farmer: harvest/plant across the whole plan."""
            zone_set = set(zone)
            op = _standing_op(tiles[fy][fx], zone_set, fx, fy)
            if op is not None:
                return op
            z_mature = [c for c in mature if c in zone_set]
            z_plant = [c for c in empty_cells["WHEAT"] + empty_cells["CARROT"] + empty_cells["STRAWBERRY"] + empty_cells["TOMATO"] if c in zone_set]
            z_urgent = [c for c in urgent if c in zone_set]
            z_wet = [c for c in unwatered if c in zone_set]
            target = _near(z_mature, fx, fy)
            if target is None:
                target = _near(z_plant, fx, fy)
            if target is None:
                target = _near(z_urgent, fx, fy)
            if target is None:
                target = _near(z_wet, fx, fy)
            if target is None:
                target = _near([c for c in weeds if c in zone_set], fx, fy)
            if target is not None:
                mv = _walk(fx, fy, *target)
                if mv != "PASS":
                    return [mv]
            return ["PASS"]

        def _hand_op(fx: int, fy: int, zone: list[tuple[int, int]]) -> list[str]:
            """Hand: watering-first daily sweep of its chunk."""
            zone_set = set(zone)
            op = _standing_op(tiles[fy][fx], zone_set, fx, fy)
            if op is not None:
                return op
            z_urgent = [c for c in urgent if c in zone_set]
            z_wet = [c for c in unwatered if c in zone_set]
            z_mature = [c for c in mature if c in zone_set]
            z_plant = [c for c in empty_cells["WHEAT"] + empty_cells["CARROT"] + empty_cells["STRAWBERRY"] + empty_cells["TOMATO"] if c in zone_set]
            target = _near(z_urgent, fx, fy)
            if target is None:
                target = _near(z_wet, fx, fy)
            if target is None:
                target = _near(z_mature, fx, fy)
            if target is None:
                target = _near(z_plant, fx, fy)
            if target is not None:
                mv = _walk(fx, fy, *target)
                if mv != "PASS":
                    return [mv]
            return ["PASS"]

        farmer_op = _farm_op(me["farmer"][0], me["farmer"][1], plan)

        hands_ops: list[list[str]] = []
        n = len(hands_now)
        if n:
            for i, (hx, hy) in enumerate(hands_now):
                lo = i * len(plan) // n
                hi = (i + 1) * len(plan) // n
                hands_ops.append(_hand_op(hx, hy, plan[lo:hi] if plan else []))

        return {"farmer": farmer_op, "hands": hands_ops, "market": orders}


# ---- engine entry points -------------------------------------------------

def act(observation: dict[str, Any], configuration: dict[str, Any]) -> dict[str, Any]:
    """Kaggle simulation-runner entry point."""
    return _PLANNER.decide(observation)


def agent(observation: dict[str, Any], configuration: dict[str, Any]) -> dict[str, Any]:
    """Alias for local ``env.run([agent, ...])``."""
    return act(observation, configuration)


_PLANNER = FarmerPlanner()
