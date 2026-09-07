"""EXPERIMENTAL terminal-day harvest/return controller, not a promoted agent.

Negative B21 discovery screen: 4/6/8-turn variants recovered no wins on the
three tested near-loss replays and slightly regressed. Retained as research
and reproducible negative evidence, NOT as a stronger submission.

Wraps a frozen baseline without changing it. Uses only the current observation,
never replay identity, opponent nickname, seed, or future observations. Outside
its short terminal window it returns the baseline action unchanged.
"""
from __future__ import annotations

TERMINAL_HORIZON = 6
_PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER")
_FIRST_YIELD = {"WHEAT": 2, "CARROT": 2, "TOMATO": 8, "STRAWBERRY": 10, "MELON": 10}
_ANIMAL_PRODUCT = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}


def _get(config, key, default):
    return config.get(key, default) if isinstance(config, dict) else getattr(config, key, default)


def _distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _move(a, b):
    if a[0] != b[0]:
        return ["EAST" if a[0] < b[0] else "WEST"]
    if a[1] != b[1]:
        return ["SOUTH" if a[1] < b[1] else "NORTH"]
    return ["PASS"]


def _liquidate(action, prices, capacity):
    # Preserve existing SELL slot positions: they interact with the other seat.
    orders = []
    seen = set()
    for order in action.get("market", [])[:capacity]:
        if isinstance(order, list) and len(order) >= 2 and order[0] == "SELL" and order[1] in _PRODUCTS:
            orders.append(["SELL", order[1], 99999])
            seen.add(order[1])
        else:
            orders.append(["PASS"])
    missing = sorted((p for p in _PRODUCTS if p not in seen), key=lambda p: (-prices.get(p, 0), p))
    free = [i for i, o in enumerate(orders) if o[0] != "SELL"]
    for product in missing:
        if free:
            orders[free.pop(0)] = ["SELL", product, 99999]
        elif len(orders) < capacity:
            orders.append(["SELL", product, 99999])
    return orders


def plan_terminal(action, obs, config, horizon=TERMINAL_HORIZON):
    last = max(0, int(_get(config, "episodeSteps", 720)) - 2)
    per_day = max(1, int(_get(config, "turnsPerDay", 24)))
    step = int(obs.get("step", 0))
    start = max(last - horizon + 1, (last // per_day) * per_day)
    if horizon <= 0 or not start <= step <= last:
        return action
    player = int(obs.get("player", 0))
    farms = obs.get("farms") or []
    if not 0 <= player < len(farms):
        return action
    farm = farms[player]
    private = obs.get("private") or {}
    prices = (obs.get("market") or {}).get("prices") or {}
    size = len(farm["tiles"])
    half = size // 2
    access = ((half-1, half-1), (half, half-1), (half-1, half), (half, half))
    positions = [farm["farmer"], *farm.get("hands", [])]
    inventories = private.get("inventories") or []
    ticks = last - step + 1
    day = step // per_day
    room = max(0, int(_get(config, "shedCapacity", 100)) - sum(private.get("shed", {}).values()))
    targets = []
    for y, row in enumerate(farm["tiles"]):
        for x, tile in enumerate(row):
            if not isinstance(tile, dict) or tile.get("yield_units", 0) <= 0:
                continue
            item = None
            if tile.get("kind") == "PLANT":
                crop = tile.get("crop")
                if crop in _FIRST_YIELD and day - tile["planted_day"] >= _FIRST_YIELD[crop]:
                    item = crop
            elif tile.get("animal") in _ANIMAL_PRODUCT:
                item = _ANIMAL_PRODUCT[tile["animal"]]
            if item:
                pos = (x, y)
                targets.append((pos, item, tile, min(_distance(pos, a) for a in access)))
    chosen = []
    reserved = set()
    for index, pos in enumerate(positions):
        inv = inventories[index] if index < len(inventories) else {}
        held = [(p, inv.get(p, 0)) for p in _PRODUCTS if inv.get(p, 0) > 0]
        home = min(access, key=lambda a: _distance(pos, a))
        return_distance = _distance(pos, home)
        # A harvest on the current tile costs one action and may be combined
        # with goods already carried, provided both return and DROP still fit.
        here = next((item for target, item, tile, back in targets
                     if target == tuple(pos) and target not in reserved
                     and back + 2 <= ticks and prices.get(item, 0) > 0), None)
        if here is not None:
            reserved.add(tuple(pos))
            chosen.append(["HARVEST"])
            continue
        if held:
            if return_distance == 0:
                total = sum(max(0, n) for n in inv.values())
                if total <= room:
                    chosen.append(["DROP"])
                    room -= total
                elif room > 0:
                    item, n = max(held, key=lambda v: min(v[1], room) * prices.get(v[0], 0))
                    n = min(n, room)
                    chosen.append(["PLACE", item, n])
                    room -= n
                else:
                    chosen.append(["PASS"])
            elif return_distance + 1 <= ticks:
                chosen.append(_move(pos, home))
            else:
                chosen.append(["PASS"])
            continue
        feasible = []
        for target, item, tile, back in targets:
            if target in reserved:
                continue
            travel = _distance(pos, target)
            cost = travel + back + 2  # move, HARVEST, return, DROP; sale is same-turn.
            if cost > ticks:
                continue
            units = tile["yield_units"]
            lifespan = tile.get("max_lifespan_step", -1)
            if tile.get("kind") == "PLANT" and lifespan >= 0:
                units -= sum(t >= lifespan and (t - lifespan) % 2 == 0 for t in range(step, step + travel))
            value = max(0, units) * prices.get(item, 0)
            if value > 0:
                feasible.append((value / cost, value, -cost, target))
        if not feasible:
            chosen.append(["PASS"])
            continue
        target = max(feasible)[-1]
        reserved.add(target)
        chosen.append(["HARVEST"] if tuple(pos) == target else _move(pos, target))
    out = dict(action)
    out["farmer"], out["hands"] = chosen[0], chosen[1:]
    out["market"] = _liquidate(action, prices, max(1, int(_get(config, "maxMarketOrdersPerTurn", 10))))
    return out


def make_agent(base_policy, horizon=TERMINAL_HORIZON):
    def agent(observation, configuration):
        return plan_terminal(base_policy(observation, configuration), observation, configuration, horizon)
    return agent


def wrap(base_policy, base_module=None):
    return make_agent(base_policy, TERMINAL_HORIZON)
