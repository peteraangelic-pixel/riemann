"""Variant wrapper: cheap-fertilizer BUYER (MARKET LAYER ONLY - SAFE).

Status: this wrapper ONLY adds BUY_PRODUCT FERTILIZER market orders when the
price is cheap. It deliberately leaves FERTILIZER_RESERVE = 0, because the closed-
loop lab proved that enabling V7's fertilizer *use* path (RESERVE > 0) currently
CRASHES the farm to ~300-500 cash:

    FERTILIZER_RESERVE = 0  (ships, V7 default):  ~51k vs base
    FERTILIZER_RESERVE = 5/10/40          :       ~304-500 vs base (loses 70k)

Root cause (agents/ref/agent_v7.py, farmer `_farm_op` ~line 750): when the shed
holds fertilizer and a premium cell is fertilizable, the farmer returns early to
walk to the shed (4,4) and PICKUP, and that detour hijacks his whole daily
schedule (water/harvest/plant starve). V7 ships RESERVE=0 precisely to keep that
broken path dormant - which is also why V7 SELLS the fertilizer its cows produce
instead of using it.

So the correct, high-value V8 work is to FIX fertilizer routing (collect/apply
opportunistically, like the animal hands already do for feed), NOT to just buy
more. This wrapper is kept safe (buy-only, use-path stays off) so it measures the
isolated effect of stocking cheap fertilizer without destroying the schedule.

Once the routing is fixed in agent_v8, set ENABLE_USE = True (and/or import the
fixed planner) to actually consume the stocked fertilizer.
"""
from __future__ import annotations

BUY_BELOW = 80
BUY_QTY_PER_TURN = 10
BUY_UNTIL_STOCK = 50
CASH_RESERVE = 1200
ENABLE_USE = False          # DO NOT enable until V7 fert routing is fixed
FERTILIZER_RESERVE = 0      # 0 keeps the broken farmer fert-path dormant
FERTILIZE_ALL_CROPS = False


def _fertilizer_stock(obs: dict, player: int) -> int:
    priv = obs.get("private", {}) or {}
    stock = int((priv.get("shed", {}) or {}).get("FERTILIZER", 0) or 0)
    for inv in priv.get("inventories", []) or []:
        stock += int((inv or {}).get("FERTILIZER", 0) or 0)
    return stock


def _accepts_two(fn) -> bool:
    try:
        return getattr(fn, "__code__", None) and fn.__code__.co_argcount >= 2
    except Exception:
        return False


def wrap(base_fn, base_mod):
    if ENABLE_USE:  # opt-in only once routing is fixed
        try:
            base_mod.FERTILIZER_RESERVE = FERTILIZER_RESERVE or 40
            base_mod.FERTILIZE_PREMIUM_ONLY = not FERTILIZE_ALL_CROPS
        except Exception:
            pass

    def agent(obs: dict, config=None):
        action = base_fn(obs, config) if _accepts_two(base_fn) else base_fn(obs)
        if not isinstance(action, dict):
            return action
        player = int(obs.get("player", 0))
        farms = obs.get("farms") or [{}]
        me = farms[player] if player < len(farms) else {}
        money = float(me.get("money", 0) or 0)
        prices = (obs.get("market", {}) or {}).get("prices", {}) or {}
        fprice = float(prices.get("FERTILIZER", 999) or 999)
        orders = action.setdefault("market", [])
        stock = _fertilizer_stock(obs, player)
        if (fprice <= BUY_BELOW and money >= CASH_RESERVE
                and stock < BUY_UNTIL_STOCK and len(orders) < 10):
            qty = min(BUY_QTY_PER_TURN, BUY_UNTIL_STOCK - stock,
                      int((money - CASH_RESERVE) / max(fprice, 1)))
            if qty > 0:
                orders.append(["BUY_PRODUCT", "FERTILIZER", int(qty)])
        return action

    agent.__variant__ = "fert_buyer_safe"
    return agent
