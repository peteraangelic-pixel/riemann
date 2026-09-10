"""Buy-stop component alone (day>=29): drop HIRE/BUY_LAND, zero all other
buys. Isolates the time component of G4's stop rule (no cash condition)."""
_BUYS = {"HIRE", "BUY_LAND", "BUY_PRODUCT", "BUY_SEED", "BUY_ANIMAL"}


def overlay(action, obs, cfg):
    step = int(obs.get("step", 0) or 0)
    turns = int(cfg.get("turnsPerDay", 24) or 24)
    if step // turns < 29:
        return action
    market = []
    for order in action.get("market", []):
        if not isinstance(order, list) or not order:
            market.append(order)
            continue
        if order[0] not in _BUYS:
            market.append(order)
        elif order[0] in {"HIRE", "BUY_LAND"}:
            market.append([])
        elif len(order) >= 3:
            order[2] = 0
            market.append(order)
    action["market"] = market
    return action
