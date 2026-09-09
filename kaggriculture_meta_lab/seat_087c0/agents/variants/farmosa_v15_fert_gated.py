"""FarmOS v1 (seat 087c0) - Kaggriculture policy, v8 rewrite.

Engine facts (kaggle-environments kaggriculture, verified in source):
  * Market orders run EVERY hour (per-step), per-unit lockstep; an order list
    longer than maxMarketOrdersPerTurn (10) is truncated.
  * Hands are reset to [] at every end of day - they must be re-hired each
    morning (cost = fib sequence starting over).  Farmer is permanent.
  * PLANT consumes private seeds; if total PLANT requests for a crop in one
    turn exceed available seeds, ALL PLANT requests for that crop are
    dropped - so plant requests must be budgeted against seeds.
  * PICKUP / DROP / animal-drop only work while standing on one of the four
    shed-access tiles around (4,4): (4,4),(5,4),(4,5),(5,5).
  * Watering: non-ongoing crops gain +1 yield per watered day inside
    [ceil(max_yield_day/2), max_yield_day] (MELON d6..12, WHEAT d2..4);
    EVERY plant must be watered every calendar day (2 consecutive unwatered
    -> weed; planting day itself counts as 1 unwatered if not watered after
    planting).  Fertilized plants gain +2 per watered day.
  * Animals placed day P produce at end-of-day rollovers when
    next_day - P - first_yield_day >= 0 and % interval == 0 (COW first 8,
    every 2nd day; SHEEP 6/3; GOOSE 4/1).  Fed daily or they escape after 2
    unfed days.  fertilizer_available=True at every rollover (+1/day/animal
    collectible, ~$100 each) - the manure economy is the main engine.
  * Shed capacity 100 shared by produce and unpurchased/unplaced animals.
    EOD auto-drops hand inventories into the shed and DISCARDS overflow.
  * Town shops eat market stock every 4 hours => WHEAT feed drifts up in
    price over the season.

Season plan (measured seed-100 prices: fert ~100, milk 160-210, wool 200+,
melon 230-270, egg ~55, strawberry 120-290, wheat feed 25->50):
  * d0:      5 hands, 12 MELON seeds + 2 cows, feed buffer.  Melons watered
             daily d0-12 => 6 units each; ~72 units sold d10-12 (~16k).
  * d1-9:    cows -> 4 (d3-4) -> 6 (d6-7) -> 8 (d9-10); sell manure daily;
             NE land as soon as cash allows (d8-10).
  * d8-13:   strawberry seeds (20) into NE; harvest d18+.
  * d10-23:  wheat conveyor on freed melon rows + SW (goal feed_need+8,
             capped 28) to offset feed purchases.
  * d12-14:  sheep x5, geese x3, SW land, cows 8th; herd complete: 8 cows +
             5 sheep + 3 geese => 16 fert/day + milk/wool/eggs.
  * d24-27:  carrots sweep cells as wheat is harvested.
  * d29:     harvest + liquidate.

Worker architecture:
  * Every worker (farmer + hands) owns a private zone (balanced row-major
    chunk of usable cells).  MORNING (hour<8) is crop time INSIDE THE OWN
    ZONE only, so two workers never fight over the same plant.  Workers whose
    zone has no crop chores become feeders/transporters from early morning.
  * Same-turn claims: each target cell can be chosen by only one worker per
    turn, which kills the herding that previously stacked 3+ workers on one
    plant/animal.  Animal flags (fed/cared/fert_available/watered) dedupe
    across turns anyway.
  * Wheat carriers feed animals before anything else; feeders fetch 8 wheat
    per shed trip and feed on the way.  Feeding runs from hour 4 for
    zone-idle workers, from hour 8 for everyone.
  * Afternoon (hour>=8): feed duty -> shed drops -> animal transport
    (placement) -> crop leftovers -> care/fert collection.
"""

CROPS = {
    "WHEAT":      {"seed": 10, "first": 2, "max_day": 4, "max_yield": 6, "ongoing": False, "interval": 0},
    "CARROT":     {"seed": 20, "first": 2, "max_day": 3, "max_yield": 4, "ongoing": False, "interval": 0},
    "TOMATO":     {"seed": 50, "first": 8, "max_day": 8, "max_yield": 4, "ongoing": True, "interval": 1},
    "STRAWBERRY": {"seed": 100, "first": 10, "max_day": 10, "max_yield": 4, "ongoing": True, "interval": 2},
    "MELON":      {"seed": 80, "first": 10, "max_day": 12, "max_yield": 6, "ongoing": False, "interval": 0},
}
ANIMALS = {
    "GOOSE": {"cost": 300, "structure": "COOP", "first": 4, "interval": 1, "max_held": 4, "product": "EGG"},
    "COW":   {"cost": 400, "structure": "PASTURE", "first": 8, "interval": 2, "max_held": 6, "product": "MILK"},
    "SHEEP": {"cost": 500, "structure": "PASTURE", "first": 6, "interval": 3, "max_held": 6, "product": "WOOL"},
}

# 13 pasture slots (9 NW + 4 NE col 9) + 3 coops.
PASTURE_SITES = [(x, 3) for x in range(5)] + [(x, 4) for x in range(4)] \
    + [(9, y) for y in range(4)]
COOP_SITES = [(9, 4), (8, 3), (8, 4)]
SHED_TILES = [(4, 4), (5, 4), (4, 5), (5, 5)]
MELON_CELLS = [(x, y) for y in range(3) for x in range(5)]
CROP_NE = [(x, y) for y in range(5) for x in range(5, 9)
           if (x, y) not in COOP_SITES]
SW_CELLS = [(x, y) for y in range(5, 10) for x in range(10)]
ALL_CELLS = [(x, y) for y in range(10) for x in range(10)]
PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
            "EGG", "MILK", "WOOL", "FERTILIZER")
SITE_CELLS = set(PASTURE_SITES) | set(COOP_SITES) | set(SHED_TILES)

SELL_CAP = {"WHEAT": 8, "CARROT": 8, "TOMATO": 2, "STRAWBERRY": 5, "MELON": 8,
            "EGG": 4, "MILK": 5, "WOOL": 3, "FERTILIZER": 8}
SELL_FLOOR = {"WHEAT": 5, "CARROT": 5, "TOMATO": 5, "STRAWBERRY": 20, "MELON": 60,
              "EGG": 8, "MILK": 20, "WOOL": 15, "FERTILIZER": 60}

HERD = {"COW": [(0, 2), (3, 4), (6, 6), (9, 8)],
        "SHEEP": [(10, 2), (13, 5)],
        "GOOSE": [(12, 3)]}
BUY_WINDOW = {"COW": 12, "SHEEP": 14, "GOOSE": 15}
STRAW_CAP = 20
CARROT_CAP = 26
MELON_TARGET = 12


def _hands_target(day):
    if day <= 0:
        return 5
    if day <= 2:
        return 6
    if day <= 4:
        return 7
    if day <= 7:
        return 8
    if day <= 10:
        return 9
    if day <= 13:
        return 10
    if day <= 19:
        return 11
    return 12


def _dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _move(pos, t):
    x, y = pos
    tx, ty = t
    if x < tx:
        return ["EAST"]
    if x > tx:
        return ["WEST"]
    if y < ty:
        return ["SOUTH"]
    if y > ty:
        return ["NORTH"]
    return ["PASS"]


def _count(tiles):
    plants, animals, structs = {}, {}, {}
    for row in tiles:
        for t in row:
            if not isinstance(t, dict):
                continue
            k = t.get("kind")
            if k == "PLANT":
                plants[t["crop"]] = plants.get(t["crop"], 0) + 1
            elif "animal" in t:
                animals[t["animal"]] = animals.get(t["animal"], 0) + 1
            elif k in ("COOP", "PASTURE"):
                structs[k] = structs.get(k, 0) + 1
    return plants, animals, structs


def _feed_need(animals):
    return sum(animals.get(k, 0) for k in ("COW", "SHEEP", "GOOSE"))


class Mem:
    def __init__(self):
        self.day = -1
        self.bands = {}
        self.farmer_band = []
        self.n_hands = -1
        self.feed_bought = 0


def _usable(tiles):
    return [c for c in ALL_CELLS if tiles[c[1]][c[0]] != "LOCKED"]


def _make_bands(tiles, n):
    """Balanced row-major chunks of usable cells (workers only)."""
    usable = _usable(tiles)
    m = len(usable)
    per = max(1, m // n) if n else m
    extra = max(0, m - per * n)
    bands = {}
    i = 0
    for w in range(n):
        take = per + (1 if w < extra else 0)
        bands[w] = usable[i:i + take]
        i += take
    for w in range(n):
        if not bands[w]:
            bands[w] = usable[-1:] if usable else []
    return bands


def _decide(obs, mem):
    player = int(obs["player"])
    farm = obs["farms"][player]
    private = obs["private"]
    market = obs["market"]
    day = int(obs["day"])
    hour = int(obs["hour"])
    tiles = farm["tiles"]
    plants, animals, structs = _count(tiles)
    money = float(farm["money"])
    shed = private["shed"]
    seeds = private["seeds"]
    invs = list(private.get("inventories") or [])
    prices = market["prices"]
    unlocked = set(farm["unlocked_quadrants"])
    n_hands = len(farm["hands"])
    feed_need = _feed_need(animals)

    if mem.day != day:
        mem.feed_bought = 0
        mem.day = day
        mem.bands = {}
        mem.farmer_band = []
        mem.n_hands = -1
    if mem.n_hands != n_hands or not mem.bands:
        nb = n_hands + 1  # hands + farmer
        b = _make_bands(tiles, nb)
        mem.bands = {i: b[i] for i in range(n_hands)}
        mem.farmer_band = b[nb - 1]
        mem.n_hands = n_hands

    room = 100 - sum(shed.values())

    animal_cells = []
    for (x, y) in ALL_CELLS:
        t = tiles[y][x]
        if isinstance(t, dict) and "animal" in t:
            animal_cells.append((x, y))
    unfed_all = [c for c in animal_cells if not tiles[c[1]][c[0]].get("fed_today")]
    uncared_all = [c for c in animal_cells if not tiles[c[1]][c[0]].get("cared_today")]
    fert_ready = [c for c in animal_cells if tiles[c[1]][c[0]].get("fertilizer_available")]

    def floor():
        if day <= 1:
            return 150.0
        if day <= 3:
            return 300.0
        if "NE" not in unlocked:
            return 250.0 if day <= 10 else 60.0
        if day <= 10:
            return 80.0
        if day <= 20:
            return 80.0
        return 50.0

    def carried(kind):
        return sum(inv.get(kind, 0) for inv in invs)

    def have_animals(kind):
        return animals.get(kind, 0) + shed.get(kind, 0) + carried(kind)

    orders = []
    est_spend = 0.0

    def afford(cost):
        nonlocal est_spend
        if money - est_spend - cost < floor():
            return False
        est_spend += cost
        return True

    # ============================ MARKET ==================================
    # Sells first (fund the buys that follow in the same list).
    if day < 30:
        wheat_keep = 0 if day >= 29 else max(feed_need + 8, 10)
        fert_keep = 0 if day >= 28 else (0 if day < 8 else 4)
        shed_used = sum(shed.values())
        for item in ("FERTILIZER", "EGG", "MILK", "WOOL", "MELON",
                     "STRAWBERRY", "CARROT", "WHEAT"):
            if len(orders) >= 9:
                break
            stock = shed.get(item, 0)
            if item == "WHEAT":
                # wheat surplus is the feed reserve: only liquidate late or
                # when the shed is under real pressure
                if day < 26 and shed_used < 90:
                    continue
                keep = wheat_keep
                if stock <= keep:
                    continue
            elif item == "MELON":
                if day < 9:
                    continue
                keep = 0
                if stock <= 0:
                    continue
            elif item == "FERTILIZER":
                keep = fert_keep
                if stock <= keep:
                    continue
            else:
                keep = 0
                if stock <= 0:
                    continue
            price = prices.get(item, 0)
            if price < SELL_FLOOR[item]:
                continue
            q = min(stock - keep, SELL_CAP[item])
            if q > 0:
                orders.append(["SELL", item, q])

    # Hiring: hands reset each morning, so hire up to target (cost is fib).
    if n_hands < _hands_target(day) and len(orders) < 10:
        k = 0
        cum = 0.0
        ft = farm["hires_today"]
        while len(orders) < 10 and n_hands + k < _hands_target(day):
            nxt = _fib(ft + k)
            if money - est_spend - cum - nxt < floor():
                break
            orders.append(["HIRE"])
            cum += nxt
            k += 1

    if "NE" not in unlocked and day >= 6 and money - est_spend >= 1000 + 60:
        orders.append(["BUY_LAND"])
        est_spend += 1000
    elif "NE" in unlocked and "SW" not in unlocked and day >= 12 \
            and money - est_spend >= 2000 + 150:
        orders.append(["BUY_LAND"])
        est_spend += 2000

    # --- seeds ------------------------------------------------------------
    if day <= 2:
        have = seeds.get("MELON", 0) + plants.get("MELON", 0)
        q = min(MELON_TARGET - have, 6)
        if q > 0 and len(orders) < 9 and afford(80 * q):
            orders.append(["BUY_SEED", "MELON", q])

    straw_total = plants.get("STRAWBERRY", 0) + seeds.get("STRAWBERRY", 0)
    if "NE" in unlocked and 8 <= day <= 13 and straw_total < STRAW_CAP \
            and len(orders) < 9:
        q = min(6, STRAW_CAP - straw_total)
        if q > 0 and afford(100 * q):
            orders.append(["BUY_SEED", "STRAWBERRY", q])

    if 9 <= day <= 23:
        wg = min(28, max(0, feed_need + 8))
        have = seeds.get("WHEAT", 0) + plants.get("WHEAT", 0)
        q = min(8, wg - have)
        if q > 0 and len(orders) < 9 and afford(10 * q):
            orders.append(["BUY_SEED", "WHEAT", q])

    if 24 <= day <= 27:
        have = seeds.get("CARROT", 0) + plants.get("CARROT", 0)
        q = min(8, CARROT_CAP - have)
        if q > 0 and len(orders) < 9 and afford(20 * q):
            orders.append(["BUY_SEED", "CARROT", q])

    # --- animals ----------------------------------------------------------
    for kind, schedule in HERD.items():
        target = max((n for (dd, n) in schedule if day >= dd), default=0)
        if target <= 0 or day > BUY_WINDOW[kind] or have_animals(kind) >= target:
            continue
        want = min(2, target - have_animals(kind))
        cost = ANIMALS[kind]["cost"] * want
        while want > 1 and money - est_spend - cost < floor():
            want -= 1
            cost = ANIMALS[kind]["cost"] * want
        if want >= 1 and room >= want and len(orders) < 9 and afford(cost):
            orders.append(["BUY_ANIMAL", kind, want])

    # --- feed ---------------------------------------------------------------
    if day < 29 and len(orders) < 9:
        # shed-only basis: wheat in hands is already committed to feeding.
        need = feed_need + 8
        q = min(16, need - shed.get("WHEAT", 0) - mem.feed_bought)
        px = prices.get("WHEAT", 99)
        if q > 0 and px <= 120:
            q = min(q, max(0, int((money - est_spend - floor()) // px)))
            if q > 0:
                orders.append(["BUY_PRODUCT", "WHEAT", q])
                mem.feed_bought += q

    # ============================ WORKERS =================================
    wheat_goal = min(28, max(0, feed_need + 8)) if day >= 10 else 0
    plant_budget = {c: n for c, n in seeds.items() if n > 0}

    def _crop_here(x, y):
        """Which crop (if any) should be planted on this empty cell."""
        if (x, y) in SITE_CELLS:
            return None
        if (x, y) in MELON_CELLS:
            if day <= 2 and plants.get("MELON", 0) < MELON_TARGET:
                return "MELON"
            if day >= 24 and plants.get("CARROT", 0) < CARROT_CAP:
                return "CARROT"
            if 10 <= day <= 23 and plants.get("WHEAT", 0) < wheat_goal:
                return "WHEAT"
            return None
        if (x, y) in CROP_NE:
            if 8 <= day <= 15 and plants.get("STRAWBERRY", 0) < STRAW_CAP \
                    and "NE" in unlocked:
                return "STRAWBERRY"
            if day >= 24 and plants.get("CARROT", 0) < CARROT_CAP:
                return "CARROT"
            if 10 <= day <= 23 and plants.get("WHEAT", 0) < wheat_goal:
                return "WHEAT"
            return None
        # SW or other free land
        if day >= 24 and plants.get("CARROT", 0) < CARROT_CAP:
            return "CARROT"
        if 10 <= day <= 23 and plants.get("WHEAT", 0) < wheat_goal \
                and "SW" in unlocked and (x, y) in SW_CELLS:
            return "WHEAT"
        return None

    plant_left = dict(plant_budget)

    def cell_ops(x, y, inv):
        t = tiles[y][x]
        if isinstance(t, dict) and t.get("kind") == "PLANT":
            c = t["crop"]
            cd = CROPS[c]
            age = day - t["planted_day"]
            yld = t.get("yield_units", 0)
            if cd["ongoing"]:
                if yld > 0 and age >= cd["first"]:
                    return ["HARVEST"]
                if not t.get("watered_today"):
                    return ["WATER"]
                return None
            if yld > 0 and age >= cd["first"] and (
                    yld >= cd["max_yield"] or age >= cd["max_day"] or day >= 29):
                return ["HARVEST"]
            if not t.get("watered_today"):
                return ["WATER"]
            return None
        if isinstance(t, dict) and t.get("kind") == "WEED":
            return ["DIG"]
        if isinstance(t, dict) and "animal" in t:
            if not t.get("fed_today"):
                if inv.get("WHEAT", 0) > 0:
                    return ["FEED"]
                return None
            if not t.get("cared_today"):
                return ["CARE"]
            if t.get("fertilizer_available"):
                return ["COLLECT_FERTILIZER"]
            if t.get("yield_units", 0) > 0:
                return ["HARVEST"]
            return None
        if t is None:
            crop = _crop_here(x, y)
            if crop and plant_left.get(crop, 0) > 0:
                return ["PLANT", crop]
            return None
        return None

    def commit_plant(op):
        if op and op[0] == "PLANT" and len(op) >= 2:
            c = op[1]
            if plant_left.get(c, 0) > 0:
                plant_left[c] -= 1
                return True
            return False
        return True

    claimed = set()

    def _nearest_op(cells, pos, inv, want=None, allow_claimed=False):
        """Nearest cell in `cells` with a wanted op; claims it for this turn."""
        best, bd, bop = None, 10 ** 9, None
        for c in cells:
            if c in claimed and not allow_claimed:
                continue
            op = cell_ops(c[0], c[1], inv)
            if op is None:
                continue
            if want is not None and op[0] not in want:
                continue
            d = _dist(pos, c)
            if d < bd:
                best, bd, bop = c, d, op
        if best is not None:
            claimed.add(best)
        return best, bop

    PLANT_OPS = ("WATER", "HARVEST", "DIG", "PLANT")
    ANIMAL_NEED_OPS = ("CARE", "COLLECT_FERTILIZER", "HARVEST")

    def _ready_site(kind):
        st = ANIMALS[kind]["structure"]
        sites = PASTURE_SITES if st == "PASTURE" else COOP_SITES
        for s in sites:
            if s in claimed:
                continue
            t = tiles[s[1]][s[0]]
            if isinstance(t, dict) and t.get("kind") == st and "animal" not in t:
                return s
        return None

    def _empty_site(kind):
        st = ANIMALS[kind]["structure"]
        sites = PASTURE_SITES if st == "PASTURE" else COOP_SITES
        for s in sites:
            if s in claimed:
                continue
            if tiles[s[1]][s[0]] is None:
                return s
        return None

    def farmer_special(pos, inv):
        """Animal transport. Returns (action, claim_cell)."""
        x, y = pos
        kinds = sorted(("COW", "SHEEP", "GOOSE"),
                       key=lambda k: -(shed.get(k, 0) + inv.get(k, 0)))
        for kind in kinds:
            if inv.get(kind, 0) <= 0 and shed.get(kind, 0) <= 0:
                continue
            if inv.get(kind, 0) > 0:
                site = _ready_site(kind)
                if site is None:
                    site = _empty_site(kind)
                if site is None:
                    continue
                claimed.add(site)
                if site == (x, y):
                    t = tiles[y][x]
                    if isinstance(t, dict) and t.get("kind") == ANIMALS[kind]["structure"]:
                        return ["PLACE", kind], site
                    if t is None:
                        return ["BUILD_" + ANIMALS[kind]["structure"]], site
                    if isinstance(t, dict) and t.get("kind") in ("PLANT", "WEED"):
                        return ["DIG"], site
                    return ["PASS"], None
                return _move(pos, site), site
            site = _ready_site(kind)
            if site is None:
                site = _empty_site(kind)
            if site is None:
                continue
            claimed.add(site)
            target = min(SHED_TILES, key=lambda s: _dist(pos, s))
            if (x, y) == tuple(target):
                return ["PICKUP", kind, 1], None
            return _move(pos, target), None
        return None, None


    def _fert_target(zone, pos):
        best, best_key = None, None
        for (x, y) in zone:
            if (x, y) in claimed:
                continue
            t = tiles[y][x]
            if not (isinstance(t, dict) and t.get("kind") == "PLANT"):
                continue
            if t.get("fertilized_until_day", -1) >= day:
                continue
            c = t["crop"]
            yld = t.get("yield_units", 0)
            age = day - t["planted_day"]
            if c == "STRAWBERRY":
                if yld >= CROPS[c]["max_yield"] or age < 9:
                    continue
                prio = 2
            elif c == "WHEAT":
                if yld >= 6 or age < 0 or age > 3:
                    continue
                prio = 1
            elif c == "CARROT":
                if yld >= 4 or age < 0 or age > 2:
                    continue
                prio = 0
            else:
                continue
            key = (prio, -_dist(pos, (x, y)))
            if best_key is None or key > best_key:
                best, best_key = (x, y), key
        return best

    def _feed_action(pos, inv):
        """Returns action or None (no claim bookkeeping needed; fed flag)."""
        if not unfed_all:
            return None
        x, y = pos
        if (x, y) in unfed_all:
            if inv.get("WHEAT", 0) > 0:
                return ["FEED"]
            if shed.get("WHEAT", 0) > 0:
                tgt = min(SHED_TILES, key=lambda s: _dist(pos, s))
                if (x, y) == tuple(tgt):
                    return ["PICKUP", "WHEAT", min(8, shed.get("WHEAT", 0))]
                return _move(pos, tgt)
            return None
        if inv.get("WHEAT", 0) > 0:
            cand = [c for c in unfed_all if c not in claimed]
            if not cand:
                cand = unfed_all
            # endangered animals first (2 unfed days = escape), then nearest
            def feed_key(c):
                cu = tiles[c[1]][c[0]].get("consecutive_unfed", 0)
                return (-cu, _dist(pos, c))
            tgt = min(cand, key=feed_key)
            claimed.add(tgt)
            return _move(pos, tgt)
        if shed.get("WHEAT", 0) > 0:
            tgt = min(SHED_TILES, key=lambda s: _dist(pos, s))
            if (x, y) == tuple(tgt):
                return ["PICKUP", "WHEAT", min(8, shed.get("WHEAT", 0))]
            return _move(pos, tgt)
        return None

    def _produce_on(inv):
        return sum(v for k, v in inv.items() if k in PRODUCTS and v > 0)

    def _shed_drop(pos, inv):
        if pos in SHED_TILES and _produce_on(inv) > 0:
            return ["DROP"]
        return None

    # ---- worker decision flows -------------------------------------------
    def worker_step_hand(hid, pos, inv):
        x, y = pos
        zone = mem.bands.get(hid) or []
        carrying_animal = any(inv.get(k, 0) > 0 for k in ANIMALS)
        has_wheat = inv.get("WHEAT", 0) > 0
        # 0. carrying an animal: place it (rare, brief)
        if carrying_animal:
            op, _ = farmer_special(pos, inv)
            if op is not None:
                return op
        # 1. a wheat carrier's mission is feeding - feed before any local op
        if has_wheat and not carrying_animal:
            fa = _feed_action(pos, inv)
            if fa is not None:
                return fa
        # 2. underfoot job
        if (x, y) not in claimed:
            local = cell_ops(x, y, inv)
            if local is not None and commit_plant(local):
                claimed.add((x, y))
                return local
        # 2b. late day: guarantee every plant was watered today, then
        # feed anything still unfed (fresh placements included)
        if hour >= 17 and not carrying_animal:
            best, bop = _nearest_op(ALL_CELLS, pos, inv, ("WATER",))
            if best is not None:
                if tuple(pos) == tuple(best):
                    return ["WATER"]
                return _move(pos, best)
            fa = _feed_action(pos, inv)
            if fa is not None:
                return fa
        # 3. morning: crop ops in own zone only
        if hour < 8:
            best, bop = _nearest_op(zone, pos, inv, PLANT_OPS)
            if best is not None:
                if tuple(pos) == tuple(best):
                    op = cell_ops(best[0], best[1], inv)
                    if op is not None and commit_plant(op):
                        return op
                    return ["PASS"]
                return _move(pos, best)
            # zone clear: act as feeder/transporter (animals don't need crops)
        # 4. feed duty (morning for zone-idle workers too, afternoon for all)
        if hour >= 4 or not has_wheat:
            fa = _feed_action(pos, inv)
            if fa is not None:
                return fa
        # 4b2. fertilizer use: only after the evening water sweep has cleared
        if hour >= 21 and inv.get("FERTILIZER", 0) > 0 and not carrying_animal:
            uw = any(isinstance(tiles[y][x], dict)
                     and tiles[y][x].get("kind") == "PLANT"
                     and not tiles[y][x].get("watered_today")
                     for y in range(10) for x in range(10))
            if not uw:
                tgt = _fert_target(zone, pos)
                if tgt is None:
                    tgt = _fert_target(ALL_CELLS, pos)
                if tgt is not None:
                    claimed.add(tgt)
                    if tuple(pos) == tuple(tgt):
                        return ["FERTILIZE"]
                    return _move(pos, tgt)
        # 4b. heavy produce carriers shuttle to the shed (melons, milk, ...)
        if hour >= 9:
            produce = {k: v for k, v in inv.items()
                       if k in PRODUCTS and k != "WHEAT" and v > 0}
            if sum(produce.values()) >= 5:
                tgt = min(SHED_TILES, key=lambda s: _dist(pos, s))
                if (x, y) == tuple(tgt):
                    return ["DROP"]
                return _move(pos, tgt)
        # 5. drop produce while at the shed
        fa = _shed_drop(pos, inv)
        if fa is not None:
            return fa
        # 6. transport shed animals (unlock production)
        op, _ = farmer_special(pos, inv)
        if op is not None:
            return op
        # 7. afternoon/evening: crop leftovers, then animal ops
        best, bop = _nearest_op(zone, pos, inv, PLANT_OPS)
        if best is None and hour >= 8:
            best, bop = _nearest_op(ALL_CELLS, pos, inv, PLANT_OPS)
        if best is None and hour >= 8:
            best, bop = _nearest_op(ALL_CELLS, pos, inv, ANIMAL_NEED_OPS)
        if best is None and hour >= 10:
            best, bop = _nearest_op(ALL_CELLS, pos, inv, None)
        if best is not None:
            if tuple(pos) == tuple(best):
                op = cell_ops(best[0], best[1], inv)
                if op is not None and commit_plant(op):
                    return op
                return ["PASS"]
            return _move(pos, best)
        return ["PASS"]

    def farmer_step(pos, inv):
        x, y = pos
        zone = mem.farmer_band or []
        carrying_animal = any(inv.get(k, 0) > 0 for k in ANIMALS)
        has_wheat = inv.get("WHEAT", 0) > 0
        if carrying_animal:
            op, _ = farmer_special(pos, inv)
            if op is not None:
                return op
            return ["PASS"]
        if has_wheat:
            fa = _feed_action(pos, inv)
            if fa is not None:
                return fa
        if (x, y) not in claimed:
            local = cell_ops(x, y, inv)
            if local is not None and commit_plant(local):
                claimed.add((x, y))
                return local
        # 2b. late day: guarantee every plant was watered today
        if hour >= 17:
            best, bop = _nearest_op(ALL_CELLS, pos, inv, ("WATER",))
            if best is not None:
                if tuple(pos) == tuple(best):
                    return ["WATER"]
                return _move(pos, best)
        if hour < 8:
            best, bop = _nearest_op(zone, pos, inv, PLANT_OPS)
            if best is not None:
                if tuple(pos) == tuple(best):
                    op = cell_ops(best[0], best[1], inv)
                    if op is not None and commit_plant(op):
                        return op
                    return ["PASS"]
                return _move(pos, best)
        # 4. feed duty
        fa = _feed_action(pos, inv)
        if fa is not None:
            return fa
        # 4b2. fertilizer use (farmer): late evening after water cleared
        if hour >= 21 and inv.get("FERTILIZER", 0) > 0:
            uw = any(isinstance(tiles[y][x], dict)
                     and tiles[y][x].get("kind") == "PLANT"
                     and not tiles[y][x].get("watered_today")
                     for y in range(10) for x in range(10))
            if not uw:
                tgt = _fert_target(ALL_CELLS, pos)
                if tgt is not None:
                    claimed.add(tgt)
                    if tuple(pos) == tuple(tgt):
                        return ["FERTILIZE"]
                    return _move(pos, tgt)
        # 5. drop while at shed
        fa = _shed_drop(pos, inv)
        if fa is not None:
            return fa
        # 6. transport shed animals
        op, _ = farmer_special(pos, inv)
        if op is not None:
            return op
        # 7. crop + animal leftovers
        best, bop = _nearest_op(ALL_CELLS, pos, inv, PLANT_OPS)
        if best is None:
            best, bop = _nearest_op(ALL_CELLS, pos, inv, ANIMAL_NEED_OPS)
        if best is None:
            best, bop = _nearest_op(ALL_CELLS, pos, inv, None)
        if best is not None:
            if tuple(pos) == tuple(best):
                op = cell_ops(best[0], best[1], inv)
                if op is not None and commit_plant(op):
                    return op
                return ["PASS"]
            return _move(pos, best)
        return ["PASS"]

    farmer_action = farmer_step(tuple(farm["farmer"]), invs[0])
    hands_actions = []
    for i, pos in enumerate(farm["hands"]):
        hands_actions.append(worker_step_hand(i, tuple(pos), invs[i + 1]))
    return {"farmer": farmer_action, "hands": hands_actions, "market": orders}


def _fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


class FarmOS:
    def __init__(self):
        self._mem = Mem()

    def __call__(self, obs, config=None):
        try:
            return _decide(obs, self._mem)
        except Exception:
            return {"farmer": ["PASS"], "hands": [], "market": []}


_MEM = Mem()


def act(obs):
    try:
        return _decide(obs, _MEM)
    except Exception:
        return {"farmer": ["PASS"], "hands": [], "market": []}


def agent(observation, configuration=None):
    return act(observation)


ACT = act
