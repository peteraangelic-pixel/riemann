"""Kaggriculture v5 candidate: mixed premium crops and livestock.

v1 (all wheat) verified the machinery: hired hands run daily watering-first
sweeps of their plan chunks, the farmer harvests/plants overflow, land NE+SW
is bought when the current area fills, wheat is harvested at age 3, and the
SE quadrant is never bought (its $4k cannot pay back late in the season).
Local results: ~20.0k vs passive / ~19.2k self-play (720-turn episodes).

v2 adds a second crop (CARROT) that uses the same 4-day, 3-unit rhythm as
wheat.  Wheat's price curve is log-shaped above equilibrium so it can absorb
unlimited supply without crashing, whereas carrot (sqrt above) crashes once
the market is flooded - but carrot also pays 35 base vs wheat's 25 and its
price *rises* when the town drains it and nobody supplies it.

The town's demand is fully public: every unlocked shop instance consumes a
fixed number of units per day of the products it demands.  We therefore size
the carrot belt to (a share of) the current town carrot demand, cap it as a
fraction of the plan, and only plant carrots while their market price still
justifies the more expensive seed.  Cells are assigned a crop by their rank
in the canonical plan (carrots get the lowest ranks); because a crop switch
only happens when a cell is replanted after harvest, the assignment adapts
smoothly as shops unlock.

v3 added a compact goose subsystem learned from public-match telemetry. V3.1
then retained home-grown wheat as feed and fixed overcommitted market queues.
V4 generalizes the machinery and selects five cows: dedicated hands build
pastures, carry animals and feed wheat from the shed, then harvest milk, CARE
for the next yield, and collect daily fertilizer. Across 18 real replay action
streams cow5 averaged 55.3k with 16 wins, versus 40.5k/9 wins for goose5.

Everything stays deterministic and stateless; ``act`` is a pure function of
the observation plus the module constants below (tunable for offline sweeps).

Entry points: ``act`` / ``agent`` (Kaggle simulator loads ``main.py`` and
calls ``act``; local ``env.run`` calls either).
"""

from __future__ import annotations

from typing import Any

# Crops we can run.  Both are one-time crops with the same age-3 rhythm:
#   WHEAT  seed 10, base 25, 3u/4 tile-days
#   CARROT seed 20, base 35, 3u/4 tile-days (same watering needs)
SUPPORTED = ("WHEAT", "CARROT", "MELON", "STRAWBERRY")
SEED_COST = {"WHEAT": 10, "CARROT": 20, "MELON": 80, "STRAWBERRY": 100}
# First harvestable age per crop.  Wheat/carrot are picked at 3 units on age 3
# (watered through the bonus window); melon pays 6 units on age 10.
HARVEST_AGE_BY_CROP = {"WHEAT": 3, "CARROT": 3, "MELON": 10, "STRAWBERRY": 10}

QUAD_ORDER = ("NW", "NE", "SW", "SE")
LAND_COST = {"NE": 1000, "SW": 2000, "SE": 4000}
# Cumulative daily cost of hiring 1..10 hands (fib 1,1,2,3,5,8,13,21,34,55).
FIB_SUM = (1, 2, 4, 7, 12, 20, 33, 54, 88, 143)
FIB_COST = (1, 1, 2, 3, 5, 8, 13, 21, 34, 55)
# Keep enough liquid cash for the next day's hands and market volatility.
OPERATING_RESERVE = 300

# Hands roughly sustain ~10 cells/day each (water + tour + occasional
# harvest/replant); we also count the farmer as one waterer.
CELLS_PER_HAND = 10
HANDS_EXTRA = 1
HANDS_MAX = 12
# Replay-driven V6 controls. Defaults retain the selected V5 behavior; Actions
# sweeps change one family at a time before any interaction profile is built.
HAND_TASK_MODE = "WATER_FIRST"
# Unlike the rejected fully-global router, idle stealing preserves each hand's
# deterministic zone and crosses a boundary only when that zone has no work.
IDLE_WORK_STEAL = False
LATE_CROP_HAND_BONUS = 0
# Optional replay-derived staffing curves. AUTO retains capacity-based hiring.
LABOR_MODE = "AUTO"

# Never queue more than this many market orders per turn.
MAX_MARKET_ORDERS = 10

# Selling below this would mean a crashed market.
SELL_PRICE_FLOOR = 1
# Liquidate everything late: inventory has zero terminal value.
ENDGAME_SELL_DAY = 28
# Empty means sell whenever stock reaches the shed. Non-empty tuples allow
# measured batching immediately after town-consumption ticks.
SALE_HOURS: tuple[int, ...] = ()

# Land purchase triggers.
LAND_NE_MIN_PLANTED = 3       # unlock early for pasture/field throughput
LAND_SW_MIN_PLANTED = 30      # measured best over all public replay streams
LAND_SW_MAX_DAY = 18          # late purchases cannot pay back
LAND_RESERVE = 700            # cash kept after the purchase for seeds+wages
SELL_BUY = False              # SE quadrant purchase disabled (see module docs)
# Across 32 public replay streams, day-8/day-10 timed expansion improved the
# finalist from 93,615.0 to 94,409.0 without losing a game.
LAND_MODE = "TIMED"
LAND_NE_BUY_DAY = 8
LAND_SW_BUY_DAY = 10

# Carrot belt sizing: cells = clamp(share of town carrot demand that we want
# to serve, 0..CARROT_MAX_FRAC * plan).  CARROT_KAPPA tunes how aggressively
# we chase the town's carrot consumption.
CARROT_KAPPA = 0.70
CARROT_MAX_FRAC = 0.40
# Only plant carrots while their price is at least this multiple of the wheat
# price (carrot seed is twice as expensive).
CARROT_MIN_PRICE_RATIO = 1.15

# Product demand per day for one shop instance (6 ticks/day; single-product
# shops consume 2x per tick).
TICKS_PER_DAY = 6.0
CARROT_SHOP_MULT = {"PET_CAFE": 2, "FARMERS_MARKET": 1}

# Carrot production per cell per day at the age-3 rhythm (3 units / 4 days).
CARROT_UNITS_PER_CELL_DAY = 0.75

# Melon cells (explicit NW coordinates).  Melon needs ~11 tile-days per crop
# (6 units); town-center melon demand is 1/day regardless of shop draws, so a
# couple of melon cells earn far more per tile-day than wheat/carrot while the
# market is anywhere near equilibrium.  Number of cells = len(MELON_CELLS).
MELON_CELLS = [(0, 0), (1, 0), (2, 0), (3, 0), (0, 1), (1, 1)]
# Melon needs 10 days to mature; a plant started after this day cannot be
# harvested before the season ends.
MELON_LAST_PLANT_DAY = 18
# V5 reserves premium ongoing crops in deterministic rank bands. These are
# deliberately profile constants so Actions can sweep broad economies.
STRAWBERRY_TARGET = 0
STRAWBERRY_START_DAY = 0
STRAWBERRY_LAST_PLANT_DAY = 13
FERTILIZER_RESERVE = 0
FERTILIZE_PREMIUM_ONLY = True

# v4 defaults to five cows; GH matrix jobs can switch the same logistics
# machinery to geese or sheep for controlled comparisons.
ANIMAL_KIND = "COW"
ANIMAL_TARGET = 14  # compatibility: sum of ANIMAL_TARGETS is authoritative in V5
ANIMAL_TARGETS = {"COW": 8, "SHEEP": 6}
ANIMAL_COST = {"GOOSE": 300, "COW": 400, "SHEEP": 500}
ANIMAL_STRUCTURE = {"GOOSE": "COOP", "COW": "PASTURE", "SHEEP": "PASTURE"}
ANIMAL_BUILD_OP = {"GOOSE": "BUILD_COOP", "COW": "BUILD_PASTURE", "SHEEP": "BUILD_PASTURE"}
# Ordered compact capacity around all four shed entrances. Locked coordinates
# activate naturally after land purchase; only the first ANIMAL_TARGET matter.
ANIMAL_CELLS = [
    (4, 4), (4, 3), (3, 4), (4, 2), (2, 4), (4, 1),
    (5, 4), (5, 3), (6, 4), (5, 2),
    (4, 5), (3, 5), (4, 6), (2, 5),
    (5, 1), (6, 3), (7, 4),
    (1, 5), (3, 6), (4, 7),
]
ANIMALS_PER_WORKER = 3
ANIMAL_BUY_BATCH = 3
PREMIUM_SEED_BATCH = 8
FEED_STOCK_DAYS = 3
ADAPT_SHEEP_THRESHOLD = 10
ADAPT_COW_TARGET = 8
# Optional mirror response to a cow-heavy opponent. Disabled in V5; V6 sweeps
# test whether moving exposure from milk to wool helps in the shared market.
ADAPT_COW_THRESHOLD = 999
ADAPT_COW_RESPONSE_COWS = 6
ADAPT_COW_RESPONSE_SHEEP = 8
# Service ordering is sweepable. Feeding first is safer; harvesting first
# reduces held-cap losses. Both are measured rather than assumed.
ANIMAL_SERVICE_MODE = "HARVEST_FEED_CARE_FERT"


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
        # Stable cell-to-species mapping. Cows come first for earlier milk ROI;
        # sheep add independent wool demand and reduce single-market exposure.
        # A very sheep-heavy visible opponent is the one measured failure of
        # the mixed profile: shared wool supply crashes both sellers. Because
        # cows are bought first in batches, switch to eight cows before buying
        # sheep once that strategy is observable on the board.
        animal_targets = dict(ANIMAL_TARGETS)
        opponent_tiles = obs["farms"][1 - player]["tiles"]
        opponent_sheep = sum(
            isinstance(t, dict) and t.get("animal") == "SHEEP"
            for row in opponent_tiles for t in row
        )
        opponent_cows = sum(
            isinstance(t, dict) and t.get("animal") == "COW"
            for row in opponent_tiles for t in row
        )
        if opponent_sheep >= ADAPT_SHEEP_THRESHOLD and animal_targets.get("SHEEP", 0) > 0:
            animal_targets = {
                "COW": max(ADAPT_COW_TARGET, animal_targets.get("COW", 0)),
                "SHEEP": 0,
            }
        elif opponent_cows >= ADAPT_COW_THRESHOLD:
            animal_targets = {
                "COW": ADAPT_COW_RESPONSE_COWS,
                "SHEEP": ADAPT_COW_RESPONSE_SHEEP,
            }

        animal_specs: list[tuple[tuple[int, int], str]] = []
        for kind in ("COW", "SHEEP", "GOOSE"):
            animal_specs.extend((cell, kind) for cell in ANIMAL_CELLS[len(animal_specs):len(animal_specs) + animal_targets.get(kind, 0)])
        animal_plan = [cell for cell, _ in animal_specs]
        kind_at = dict(animal_specs)
        service_animal_plan = [c for c in animal_plan if tiles[c[1]][c[0]] != "LOCKED"]
        step = int(obs.get("step", 0))
        day = obs.get("day", step // 24)
        hour = obs.get("hour", step % 24)
        money = me["money"]
        unlocked = list(me.get("unlocked_quadrants", ["NW"]))
        hands_now = me.get("hands", []) or []
        seeds = private.get("seeds", {}) or {}
        shed = private.get("shed", {}) or {}
        inventories = private.get("inventories", []) or []
        prices = (obs.get("market", {}) or {}).get("prices", {}) or {}
        shops = (obs.get("town", {}) or {}).get("unlocked_shops", []) or []

        # Animal structures are permanent reservations and never enter the
        # crop conveyor.
        plan = [c for c in _plan_cells(unlocked, board) if c not in animal_plan]
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
            if (x, y) in MELON_CELLS and day <= MELON_LAST_PLANT_DAY:
                return "MELON"
            # Ongoing strawberries produce four premium harvests. Keep their
            # band compact and start early enough for the final age-16 tick.
            if rank is not None and STRAWBERRY_START_DAY <= day <= STRAWBERRY_LAST_PLANT_DAY:
                premium_rank = rank - len(MELON_CELLS)
                if 0 <= premium_rank < STRAWBERRY_TARGET:
                    return "STRAWBERRY"
            if rank is not None and carrot_ok and rank < carrot_target + len(MELON_CELLS) + STRAWBERRY_TARGET:
                return "CARROT"
            return "WHEAT"

        def _rank_of(x: int, y: int) -> int | None:
            return rank_map.get((x, y))

        # ---- single board scan: collect what every unit needs -------------
        mature: list[tuple[int, int]] = []      # plants at/over harvest age
        urgent: list[tuple[int, int]] = []      # unwatered, will die tonight
        unwatered: list[tuple[int, int]] = []   # any unwatered supported plant
        fertilizable: list[tuple[int, int]] = []
        empty_cells: dict[str, list[tuple[int, int]]] = {c: [] for c in SUPPORTED}
        weeds: list[tuple[int, int]] = []
        animal_cells: list[tuple[int, int]] = []
        animal_cells_by_kind: dict[str, list[tuple[int, int]]] = {k: [] for k in animal_targets}
        empty_structures: list[tuple[int, int]] = []
        unbuilt_animal_cells: list[tuple[int, int]] = []
        planted_per_crop = {c: 0 for c in SUPPORTED}
        for y in range(board):
            for x in range(board):
                t = tiles[y][x]
                cell = (x, y)
                if isinstance(t, str):
                    continue
                if t is None:
                    if cell in animal_plan:
                        unbuilt_animal_cells.append(cell)
                    elif cell in plan_set:
                        r = _rank_of(x, y)
                        crop = _crop_of_cell(x, y, r)
                        empty_cells[crop].append(cell)
                    continue
                if t.get("kind") == "WEED":
                    weeds.append(cell)
                    continue
                desired_kind = kind_at.get(cell)
                if desired_kind and t.get("kind") == ANIMAL_STRUCTURE[desired_kind]:
                    if t.get("animal") == desired_kind:
                        animal_cells.append(cell)
                        animal_cells_by_kind[desired_kind].append(cell)
                    elif not t.get("animal"):
                        empty_structures.append(cell)
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
                if (
                    int(t.get("fertilized_until_day", -1)) < day
                    and (not FERTILIZE_PREMIUM_ONLY or crop in ("MELON", "STRAWBERRY"))
                ):
                    fertilizable.append((x, y))
                if age >= HARVEST_AGE_BY_CROP.get(crop, HARVEST_AGE_BY_CROP["WHEAT"]):
                    mature.append((x, y))

        # ---- market orders -------------------------------------------------
        orders: list[list[Any]] = []
        shed_value = 0
        # Different products have independent price curves, but high-value
        # stock goes first so the ten-order cap cannot strand it.
        sale_items = sorted(
            shed,
            key=lambda item: (-int(prices.get(item, 0) or 0), item),
        )
        for item in sale_items:
            if len(orders) >= MAX_MARKET_ORDERS:
                break
            if day < ENDGAME_SELL_DAY and SALE_HOURS and hour not in SALE_HOURS:
                continue
            qty = shed[item]
            if qty <= 0:
                continue
            # Never sell tomorrow's animal feed only to buy it back from a
            # scarcity market. Strong online opponents aggressively consume
            # market wheat, making that round trip both fragile and costly.
            sell_qty = qty
            if day < ENDGAME_SELL_DAY and item == "WHEAT":
                feed_reserve = sum(animal_targets.values()) * FEED_STOCK_DAYS
                sell_qty = max(0, qty - feed_reserve)
            elif day < ENDGAME_SELL_DAY and item == "FERTILIZER":
                # Fertilizer is worth more when converted into extra premium
                # harvest than as a raw sale only in fertilizing profiles.
                sell_qty = max(0, qty - FERTILIZER_RESERVE)
            if sell_qty <= 0:
                continue
            price = int(prices.get(item, 0) or 0)
            if price >= (1 if day >= ENDGAME_SELL_DAY else SELL_PRICE_FLOOR):
                orders.append(["SELL", item, sell_qty])
                shed_value += sell_qty * max(price, 1)

        est_money = money + shed_value
        # Purchases in one market queue are processed sequentially. Track the
        # remaining cash instead of checking every order against the same
        # pre-order balance (which used to overcommit the opening bankroll).
        available_money = est_money

        # Land: AUTO uses measured fill thresholds. TIMED reproduces the
        # industrial opponents that unlock NE and SW in rapid succession even
        # while premium fields are still being converted.
        if len(unlocked) < len(QUAD_ORDER):
            nxt = QUAD_ORDER[len(unlocked)]
            cost = LAND_COST[nxt]
            ok = False
            if LAND_MODE == "TIMED":
                if nxt == "NE":
                    ok = day >= LAND_NE_BUY_DAY
                elif nxt == "SW":
                    ok = day >= LAND_SW_BUY_DAY
                elif nxt == "SE":
                    ok = SELL_BUY
            elif hour == 0:
                if nxt == "NE":
                    ok = sum(planted_per_crop.values()) >= LAND_NE_MIN_PLANTED
                elif nxt == "SW":
                    ok = sum(planted_per_crop.values()) >= LAND_SW_MIN_PLANTED and day <= LAND_SW_MAX_DAY
                elif nxt == "SE":
                    ok = SELL_BUY
            if ok and available_money >= cost + LAND_RESERVE:
                orders.append(["BUY_LAND"])
                available_money -= cost

        # Hands: stage livestock setup instead of assigning nearly the whole
        # opening workforce to structures for animals we cannot yet afford.
        present_animals = len(animal_cells) + sum(
            int(shed.get(k, 0)) + sum(int(inv.get(k, 0)) for inv in inventories)
            for k in animal_targets
        )
        active_animal_capacity = min(len(service_animal_plan), max(2, present_animals + ANIMAL_BUY_BATCH))
        animal_workers_target = (
            active_animal_capacity + ANIMALS_PER_WORKER - 1
        ) // ANIMALS_PER_WORKER
        crop_workers_target = max(2, (len(plan) + CELLS_PER_HAND - 1) // CELLS_PER_HAND + HANDS_EXTRA)
        if "SW" in unlocked:
            crop_workers_target += LATE_CROP_HAND_BONUS
        h_target = min(HANDS_MAX, crop_workers_target + animal_workers_target)
        if LABOR_MODE == "DMITRI":
            if day <= 7:
                h_target = 3
            elif day <= 9:
                h_target = 6
            elif day == 10:
                h_target = 7
            elif day == 18:
                h_target = 11
            elif day <= 27:
                h_target = 10
            else:
                h_target = 3
        elif LABOR_MODE == "INDUSTRIAL":
            h_target = 5 if day <= 6 else (8 if day <= 9 else (12 if day <= 27 else 4))
        h_target = min(HANDS_MAX, h_target)
        to_hire = max(0, h_target - len(hands_now))
        hires_today = int(me.get("hires_today", len(hands_now)) or 0)
        for h in range(to_hire):
            hire_index = hires_today + h
            if hire_index >= len(FIB_COST) or len(orders) >= MAX_MARKET_ORDERS:
                break
            hire_cost = FIB_COST[hire_index]
            if available_money >= hire_cost + OPERATING_RESERVE:
                orders.append(["HIRE"])
                available_money -= hire_cost
            else:
                break

        # Fund the long-lived premium crop before livestock can consume the
        # whole opening bankroll. Generic seed purchasing below skips it.
        if STRAWBERRY_TARGET > 0:
            have_strawberry = int(seeds.get("STRAWBERRY", 0))
            need_strawberry = min(
                PREMIUM_SEED_BATCH,
                max(0, len(empty_cells["STRAWBERRY"]) + 2 - have_strawberry),
            )
            cost_strawberry = need_strawberry * SEED_COST["STRAWBERRY"]
            if (
                need_strawberry > 0
                and available_money >= cost_strawberry + OPERATING_RESERVE
                and len(orders) < MAX_MARKET_ORDERS
            ):
                orders.append(["BUY_SEED", "STRAWBERRY", need_strawberry])
                available_money -= cost_strawberry

        # Buy each species independently. Sequential accounting prevents a
        # mixed herd from promising the same cash to cows and sheep.
        animal_owned = 0
        animal_buy_budget = ANIMAL_BUY_BATCH
        for kind in ("COW", "SHEEP", "GOOSE"):
            target = min(
                animal_targets.get(kind, 0),
                sum(kind_at[c] == kind for c in service_animal_plan),
            )
            carried = sum(int(inv.get(kind, 0)) for inv in inventories)
            owned = len(animal_cells_by_kind.get(kind, [])) + int(shed.get(kind, 0)) + carried
            animal_owned += owned
            missing = max(0, target - owned)
            affordable = max(0, int((available_money - OPERATING_RESERVE) // ANIMAL_COST[kind]))
            buy_n = min(missing, affordable, animal_buy_budget)
            if buy_n > 0 and day <= 18 and len(orders) < MAX_MARKET_ORDERS:
                orders.append(["BUY_ANIMAL", kind, buy_n])
                available_money -= buy_n * ANIMAL_COST[kind]
                animal_owned += buy_n
                animal_buy_budget -= buy_n

        # Feed is ordinary WHEAT product in the shed, separate from seeds.
        carried_wheat = sum(int(inv.get("WHEAT", 0)) for inv in inventories)
        feed_stock = int(shed.get("WHEAT", 0)) + carried_wheat
        feed_target = max(1, animal_owned) * FEED_STOCK_DAYS
        buy_feed = min(20, max(0, feed_target - feed_stock))
        wheat_price = int(prices.get("WHEAT", 25) or 25)
        feed_cost = buy_feed * wheat_price
        if (
            buy_feed > 0
            and available_money >= feed_cost + OPERATING_RESERVE
            and len(orders) < MAX_MARKET_ORDERS
        ):
            orders.append(["BUY_PRODUCT", "WHEAT", buy_feed])
            available_money -= feed_cost

        # Seeds per crop: enough for every planned empty cell plus a reserve.
        for crop in SUPPORTED:
            if crop == "STRAWBERRY":
                continue
            have = int(seeds.get(crop, 0))
            seed_need = len(empty_cells[crop]) + 4
            buy_n = min(seed_need - have, 25)
            seed_cost = buy_n * SEED_COST[crop]
            if (
                buy_n > 0
                and available_money >= seed_cost + OPERATING_RESERVE
                and len(orders) < MAX_MARKET_ORDERS
            ):
                orders.append(["BUY_SEED", crop, buy_n])
                available_money -= seed_cost

        # ---- decide ops for every unit --------------------------------------
        # Cap on simultaneous plants and per-crop seed budget (the engine drops
        # ALL plant ops of a crop if requests exceed that crop's seeds).
        waterers = 1 + len(hands_now)
        plant_cap = min(len(plan), waterers * CELLS_PER_HAND)
        plants_total = sum(planted_per_crop.values())
        plants_assigned = {c: 0 for c in SUPPORTED}
        def _plant_ok(crop: str) -> bool:
            if plants_total + sum(plants_assigned.values()) >= plant_cap:
                return False
            if plants_assigned[crop] >= int(seeds.get(crop, 0)):
                return False
            if hour > 22:
                return False
            return True

        def _standing_op(
            tile: Any,
            zone_set: set[tuple[int, int]],
            fx: int,
            fy: int,
            inventory: dict[str, int],
        ) -> list[str] | None:
            """Action on the tile we stand on, or None if nothing to do here."""
            if isinstance(tile, dict) and tile.get("kind") == "WEED":
                return ["DIG"]
            if isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("crop") in SUPPORTED:
                age = day - tile["planted_day"]
                yld = tile.get("yield_units", 0)
                hage = HARVEST_AGE_BY_CROP.get(tile["crop"], HARVEST_AGE_BY_CROP["WHEAT"])
                if (fx, fy) in fertilizable and int(inventory.get("FERTILIZER", 0)) > 0:
                    return ["FERTILIZE"]
                if age >= hage and yld > 0:
                    if age == hage and not tile.get("watered_today"):
                        # Watering on the first harvestable day adds a unit.
                        return ["WATER"]
                    return ["HARVEST"]
                if not tile.get("watered_today"):
                    return ["WATER"]
                return None
            if tile is None and (fx, fy) in zone_set:
                r = _rank_of(fx, fy)
                crop = _crop_of_cell(fx, fy, r)
                if _plant_ok(crop):
                    plants_assigned[crop] += 1
                    return ["PLANT", crop]
            return None

        def _animal_op(
            fx: int,
            fy: int,
            zone: list[tuple[int, int]],
            inventory: dict[str, int],
        ) -> list[Any]:
            """Build, stock and service one compact mixed-species chunk."""
            zone_set = set(zone)
            cell = (fx, fy)
            tile = tiles[fy][fx]
            wheat_carried = int(inventory.get("WHEAT", 0))
            desired_here = kind_at.get(cell)

            if cell in zone_set:
                if isinstance(tile, dict) and tile.get("kind") == "WEED":
                    return ["DIG"]
                if tile is None and desired_here:
                    return [ANIMAL_BUILD_OP[desired_here]]
                if desired_here and isinstance(tile, dict) and tile.get("kind") == ANIMAL_STRUCTURE[desired_here]:
                    if not tile.get("animal"):
                        if int(inventory.get(desired_here, 0)) > 0:
                            return ["PLACE", desired_here, 1]
                    elif tile.get("animal") == desired_here:
                        available = {
                            "HARVEST": tile.get("yield_units", 0) > 0,
                            "FEED": not tile.get("fed_today") and wheat_carried > 0,
                            "CARE": not tile.get("cared_today"),
                            "COLLECT_FERTILIZER": tile.get("fertilizer_available"),
                        }
                        modes = {
                            "HARVEST_FEED_CARE_FERT": ("HARVEST", "FEED", "CARE", "COLLECT_FERTILIZER"),
                            "FEED_HARVEST_FERT_CARE": ("FEED", "HARVEST", "COLLECT_FERTILIZER", "CARE"),
                            "FEED_FERT_HARVEST_CARE": ("FEED", "COLLECT_FERTILIZER", "HARVEST", "CARE"),
                            "FEED_CARE_HARVEST_FERT": ("FEED", "CARE", "HARVEST", "COLLECT_FERTILIZER"),
                        }
                        for op in modes.get(ANIMAL_SERVICE_MODE, modes["HARVEST_FEED_CARE_FERT"]):
                            if available[op]:
                                return [op]

            zone_empty_structures = [c for c in empty_structures if c in zone_set]
            zone_unbuilt = [c for c in unbuilt_animal_cells if c in zone_set]
            zone_animals = [c for c in animal_cells if c in zone_set]

            # Carry the correct purchased species to its reserved structure.
            if zone_empty_structures:
                target = _near(zone_empty_structures, fx, fy)
                target_kind = kind_at[target]
                if int(inventory.get(target_kind, 0)) <= 0 and int(shed.get(target_kind, 0)) > 0:
                    if cell == (4, 4):
                        return ["PICKUP", target_kind, 1]
                    return [_walk(fx, fy, 4, 4)]
                if int(inventory.get(target_kind, 0)) > 0:
                    return [_walk(fx, fy, *target)]

            if zone_unbuilt:
                target = _near(zone_unbuilt, fx, fy)
                return [_walk(fx, fy, *target)]

            hungry = [
                c for c in zone_animals
                if not tiles[c[1]][c[0]].get("fed_today")
            ]
            if hungry and wheat_carried <= 0:
                if int(shed.get("WHEAT", 0)) > 0 and cell == (4, 4):
                    return ["PICKUP", "WHEAT", max(2, len(zone_animals) * 2)]
                return [_walk(fx, fy, 4, 4)]

            service = [
                c for c in zone_animals
                if (
                    tiles[c[1]][c[0]].get("yield_units", 0) > 0
                    or not tiles[c[1]][c[0]].get("fed_today")
                    or not tiles[c[1]][c[0]].get("cared_today")
                    or tiles[c[1]][c[0]].get("fertilizer_available")
                )
            ]
            target = _near(service, fx, fy)
            if target is not None:
                move = _walk(fx, fy, *target)
                if move != "PASS":
                    return [move]
            return ["PASS"]

        def _farm_op(
            fx: int,
            fy: int,
            zone: list[tuple[int, int]],
            inventory: dict[str, int],
        ) -> list[str]:
            """Farmer: fertilize premium cells, then harvest/plant."""
            zone_set = set(zone)
            op = _standing_op(tiles[fy][fx], zone_set, fx, fy, inventory)
            if op is not None:
                return op
            z_mature = [c for c in mature if c in zone_set]
            z_plant = [c for crop in SUPPORTED for c in empty_cells[crop] if c in zone_set]
            z_urgent = [c for c in urgent if c in zone_set]
            z_wet = [c for c in unwatered if c in zone_set]
            z_fertilize = [c for c in fertilizable if c in zone_set]
            if z_fertilize and int(inventory.get("FERTILIZER", 0)) <= 0 and int(shed.get("FERTILIZER", 0)) > 0:
                if (fx, fy) == (4, 4):
                    return ["PICKUP", "FERTILIZER", min(FERTILIZER_RESERVE, int(shed["FERTILIZER"]))]
                return [_walk(fx, fy, 4, 4)]
            target = _near(z_fertilize, fx, fy) if int(inventory.get("FERTILIZER", 0)) > 0 else None
            if target is None:
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

        def _hand_op(
            fx: int,
            fy: int,
            zone: list[tuple[int, int]],
            inventory: dict[str, int],
        ) -> list[str]:
            """Hand: watering-first daily sweep of its chunk."""
            zone_set = set(zone)
            op = _standing_op(tiles[fy][fx], zone_set, fx, fy, inventory)
            if op is not None:
                return op
            z_urgent = [c for c in urgent if c in zone_set]
            z_wet = [c for c in unwatered if c in zone_set]
            z_mature = [c for c in mature if c in zone_set]
            z_plant = [c for crop in SUPPORTED for c in empty_cells[crop] if c in zone_set]
            task_sets = {
                "WATER_FIRST": (z_urgent, z_wet, z_mature, z_plant),
                "HARVEST_FIRST": (z_mature, z_urgent, z_wet, z_plant),
                "PLANT_FIRST": (z_urgent, z_plant, z_wet, z_mature),
                "VALUE_FIRST": (z_urgent, z_mature, z_plant, z_wet),
            }.get(HAND_TASK_MODE, (z_urgent, z_wet, z_mature, z_plant))
            target = None
            for candidates in task_sets:
                target = _near(candidates, fx, fy)
                if target is not None:
                    break
            if target is None and IDLE_WORK_STEAL:
                # Preserve the local-zone priority above; only genuinely idle
                # hands help the nearest outstanding task elsewhere.
                for candidates in (urgent, unwatered, mature):
                    target = _near(candidates, fx, fy)
                    if target is not None:
                        break
            if target is not None:
                mv = _walk(fx, fy, *target)
                if mv != "PASS":
                    return [mv]
            return ["PASS"]

        farmer_inventory = inventories[0] if inventories else {}
        farmer_op = _farm_op(me["farmer"][0], me["farmer"][1], plan, farmer_inventory)

        hands_ops: list[list[Any]] = []
        n = len(hands_now)
        animal_n = min(n, animal_workers_target)
        crop_n = n - animal_n
        if n:
            for i, (hx, hy) in enumerate(hands_now):
                inventory = inventories[i + 1] if i + 1 < len(inventories) else {}
                if i < animal_n:
                    lo = i * len(service_animal_plan) // animal_n
                    hi = (i + 1) * len(service_animal_plan) // animal_n
                    hands_ops.append(_animal_op(hx, hy, service_animal_plan[lo:hi], inventory))
                else:
                    crop_i = i - animal_n
                    lo = crop_i * len(plan) // max(crop_n, 1)
                    hi = (crop_i + 1) * len(plan) // max(crop_n, 1)
                    hands_ops.append(_hand_op(hx, hy, plan[lo:hi] if plan else [], inventory))

        return {"farmer": farmer_op, "hands": hands_ops, "market": orders}


# ---- engine entry points -------------------------------------------------

def act(observation: dict[str, Any], configuration: dict[str, Any]) -> dict[str, Any]:
    """Kaggle simulation-runner entry point."""
    return _PLANNER.decide(observation)


def agent(observation: dict[str, Any], configuration: dict[str, Any]) -> dict[str, Any]:
    """Alias for local ``env.run([agent, ...])``."""
    return act(observation, configuration)


_PLANNER = FarmerPlanner()
