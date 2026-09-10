"""MILK sell-reserve component alone (day>=6): cap SELL MILK to
(shed MILK after unit ops) - 1. No cash gating."""
_ACCESS = {(4, 4), (5, 4), (4, 5), (5, 5)}
_STRUCT = {"GOOSE": "COOP", "COW": "PASTURE", "SHEEP": "PASTURE"}


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


def overlay(action, obs, cfg):
    step = int(obs.get("step", 0) or 0)
    turns = int(cfg.get("turnsPerDay", 24) or 24)
    if step // turns < 6:
        return action
    p = int(obs.get("player", 0))
    shed = _shed_after_units(obs, cfg, p, action)
    milk = max(0, shed.get("MILK", 0) - 1)
    market = []
    for order in action.get("market", []):
        if not isinstance(order, list):
            continue
        if not order:
            market.append([])
            continue
        if order[0] == "SELL" and len(order) >= 3 and order[1] == "MILK":
            order[2] = min(max(0, int(order[2])), milk)
            milk -= order[2]
        market.append(order)
    action["market"] = market
    return action
