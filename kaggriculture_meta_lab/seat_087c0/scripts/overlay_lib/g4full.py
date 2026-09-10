"""G4 overlay, faithful port of agent_v11_subin_g4_29 (day>=6).

Sell reserves (wheat 10 / fertilizer 5 / milk 1); animal/seed/stock buy caps
with opponent-herd response (5000bp); HIRE/LAND gating; full buy-stop from
day 29 or money<=200. Deobfuscated 1:1 from the minified source.
"""
_ACCESS = {(4, 4), (5, 4), (4, 5), (5, 5)}
_STRUCT = {"GOOSE": "COOP", "COW": "PASTURE", "SHEEP": "PASTURE"}
_BUYS = {"HIRE", "BUY_LAND", "BUY_PRODUCT", "BUY_SEED", "BUY_ANIMAL"}
P = {
    "start": 6, "cash": 200, "buy_stop": 29,
    "wheat_reserve": 10, "fertilizer_reserve": 5, "milk_reserve": 1,
    "hands_per_quadrant": 3, "hand_buffer": 4,
    "max_quadrants": 4, "land_min_hands": 5,
    "cow_target": 11, "sheep_target": 12, "goose_target": 3,
    "animal_response_bp": 5000,
    "wheat_seed_target": 160, "carrot_seed_target": 60,
    "tomato_seed_target": 24, "strawberry_seed_target": 60,
    "melon_seed_target": 12,
    "wheat_stock_target": 20, "fertilizer_stock_target": 6,
}


def _shed_after_units(obs, cfg, p, action):
    farm = obs["farms"][p]
    private = obs.get("private", {}) or {}
    shed = {k: int(v or 0) for k, v in (private.get("shed", {}) or {}).items()}
    total = sum(shed.values())
    capacity = int(cfg.get("shedCapacity", 100) or 100)
    hands = farm.get("hands", []) or []
    positions = [farm.get("farmer", [4, 4]), *hands]
    inventories = private.get("inventories", []) or []
    operations = [action.get("farmer", ["PASS"]), *(action.get("hands", []) or [])]
    tiles = farm.get("tiles", [])
    for pos, inventory, operation in zip(positions, inventories, operations):
        if not isinstance(pos, (list, tuple)) or len(pos) < 2 or tuple(pos) not in _ACCESS or not operation:
            continue
        inventory = inventory or {}
        op = operation[0]
        if op == "PICKUP" and len(operation) >= 3:
            item = operation[1]
            take = min(max(0, int(operation[2])), shed.get(item, 0))
            shed[item] = shed.get(item, 0) - take
            total -= take
        elif op == "PLACE" and len(operation) >= 3:
            item = operation[1]
            tile = tiles[pos[1]][pos[0]] if len(tiles) > pos[1] and len(tiles[pos[1]]) > pos[0] else None
            if item in _STRUCT and isinstance(tile, dict) and tile.get("kind") == _STRUCT[item]:
                continue
            take = min(max(0, int(operation[2])), int(inventory.get(item, 0) or 0), max(0, capacity - total))
            shed[item] = shed.get(item, 0) + take
            total += take
        elif op == "DROP":
            for item, amount in inventory.items():
                take = min(max(0, int(amount or 0)), max(0, capacity - total))
                shed[item] = shed.get(item, 0) + take
                total += take
    return shed


def _placed(farm, key, value):
    n = 0
    for row in farm.get("tiles", []) or []:
        for t in row:
            if isinstance(t, dict) and t.get(key) == value:
                n += 1
    return n


def overlay(action, obs, cfg):
    step = int(obs.get("step", 0) or 0)
    turns = int(cfg.get("turnsPerDay", 24) or 24)
    day = step // turns
    if day < P["start"]:
        return action
    p = int(obs.get("player", 0))
    own = obs["farms"][p]
    foe = obs["farms"][1 - p]
    private = obs.get("private", {}) or {}
    shed = _shed_after_units(obs, cfg, p, action)
    seeds = private.get("seeds", {}) or {}
    sell_cap = {k: max(0, shed.get(k, 0) - P[k.lower() + "_reserve"]) for k in ("WHEAT", "FERTILIZER", "MILK")}
    buy_animal = {}
    for a in ("COW", "SHEEP", "GOOSE"):
        want = P[a.lower() + "_target"] + _placed(foe, "animal", a) * P["animal_response_bp"] // 10000
        buy_animal[a] = max(0, want - shed.get(a, 0) - _placed(own, "animal", a))
    buy_seed = {}
    for c in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"):
        buy_seed[c] = max(0, P[c.lower() + "_seed_target"] - int(seeds.get(c, 0) or 0) - _placed(own, "crop", c))
    buy_stock = {"WHEAT": max(0, P["wheat_stock_target"] - shed.get("WHEAT", 0)),
                 "FERTILIZER": max(0, P["fertilizer_stock_target"] - shed.get("FERTILIZER", 0))}
    n_hands = len(own.get("hands", []) or [])
    n_quad = len(own.get("unlocked_quadrants", []) or [])
    stop = day >= P["buy_stop"] or float(own.get("money", 0) or 0) <= P["cash"]
    market = []
    for order in action.get("market", []):
        if not isinstance(order, list) or not order:
            market.append(order)
            continue
        op = order[0]
        if op == "SELL" and len(order) >= 3 and order[1] in sell_cap:
            item = order[1]
            order[2] = min(max(0, int(order[2])), sell_cap[item])
            sell_cap[item] -= order[2]
        elif op == "HIRE" and (stop or n_hands >= P["hands_per_quadrant"] * n_quad + P["hand_buffer"]):
            order = []
        elif op == "BUY_LAND" and (stop or n_quad >= P["max_quadrants"] or n_hands < P["land_min_hands"]):
            order = []
        elif op in _BUYS:
            if stop:
                if op in {"HIRE", "BUY_LAND"}:
                    order = []
                elif len(order) >= 3:
                    order[2] = 0
            elif len(order) >= 3 and op in {"BUY_ANIMAL", "BUY_SEED", "BUY_PRODUCT"}:
                caps = {"BUY_ANIMAL": buy_animal, "BUY_SEED": buy_seed, "BUY_PRODUCT": buy_stock}[op]
                if order[1] in caps:
                    order[2] = min(max(0, int(order[2])), caps[order[1]])
                    caps[order[1]] -= order[2]
        market.append(order)
    action["market"] = market
    return action
