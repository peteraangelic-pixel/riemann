"""Cash-gate component alone (day>=6): if money<=250, drop HIRE/BUY_LAND,
zero other buys. No sell-reserve logic."""
_BUYS = {"HIRE", "BUY_LAND", "BUY_PRODUCT", "BUY_SEED", "BUY_ANIMAL"}


def overlay(action, obs, cfg):
    step = int(obs.get("step", 0) or 0)
    turns = int(cfg.get("turnsPerDay", 24) or 24)
    if step // turns < 6:
        return action
    p = int(obs.get("player", 0))
    farm = obs["farms"][p]
    if float(farm.get("money", 0) or 0) > 250:
        return action
    market = []
    for order in action.get("market", []):
        if not isinstance(order, list):
            continue
        if not order:
            market.append([])
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
