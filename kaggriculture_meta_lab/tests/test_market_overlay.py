from __future__ import annotations

import pytest

from kaggriculture_lab.market_overlay import apply_market_overlay, validate_profile


def state(day=10, money=1000):
    return {
        "day": day, "money": money,
        "shed": {"WHEAT": 20, "MILK": 7},
        "prices": {"WHEAT": 30, "CARROT": 0, "TOMATO": 0,
                   "STRAWBERRY": 0, "MELON": 0, "EGG": 0,
                   "MILK": 80, "WOOL": 0, "FERTILIZER": 0},
    }


def test_disabled_is_identity_copy():
    action = {"market": [["SELL", "WHEAT", 12]]}
    assert apply_market_overlay(action, state(), {}) == action
    assert apply_market_overlay(action, state(), {}) is not action


def test_live_inventory_reserve_fraction_and_price_gate():
    action = {"market": [["SELL", "WHEAT", 99], ["SELL", "MILK", 9]]}
    profile = {"enabled": True, "wheat_reserve": 4,
               "sell_fraction_bp": 5000, "min_milk_price": 90}
    out = apply_market_overlay(action, state(), profile)
    assert out["market"] == [["SELL", "WHEAT", 8], ["SELL", "MILK", 0]]


def test_fraction_is_a_per_product_turn_budget_not_repeated_per_order():
    action = {"market": [["SELL", "WHEAT", 9], ["SELL", "WHEAT", 9]]}
    out = apply_market_overlay(action, state(),
                               {"enabled": True, "sell_fraction_bp": 5000})
    assert out["market"] == [["SELL", "WHEAT", 9], ["SELL", "WHEAT", 1]]


def test_same_turn_drop_is_included_in_saleable_inventory():
    action = {"farmer": ["DROP"], "hands": [],
              "market": [["SELL", "WHEAT", 20]]}
    live = state()
    live["shed"] = {"WHEAT": 2}
    live["shed_capacity"] = 100
    live["units"] = [{"pos": [4, 4], "inventory": {"WHEAT": 6}}]
    out = apply_market_overlay(action, live, {"enabled": True})
    assert out["market"][0][2] == 8


def test_pickup_reduces_inventory_available_to_market():
    action = {"farmer": ["PICKUP", "WHEAT", 5],
              "market": [["SELL", "WHEAT", 20]]}
    live = state()
    live["units"] = [{"pos": [4, 4], "inventory": {}}]
    out = apply_market_overlay(action, live, {"enabled": True})
    assert out["market"][0][2] == 15


def test_endgame_fraction_and_buy_stop_are_state_dependent():
    action = {"market": [["HIRE"], ["BUY_SEED", "WHEAT", 10],
                         ["SELL", "WHEAT", 20]]}
    profile = {"enabled": True, "buy_stop_day": 27, "endgame_day": 27,
               "sell_fraction_bp": 1000, "endgame_sell_fraction_bp": 10000}
    assert apply_market_overlay(action, state(day=26), profile)["market"][2][2] == 2
    assert apply_market_overlay(action, state(day=27), profile)["market"] == [
        [], ["BUY_SEED", "WHEAT", 0], ["SELL", "WHEAT", 20]]


@pytest.mark.parametrize("profile", [
    {"unknown": 1}, {"sell_fraction_bp": 10001},
    {"wheat_reserve": -1}, {"cash_reserve": float("nan")},
])
def test_invalid_profiles_fail_closed(profile):
    with pytest.raises(ValueError):
        validate_profile(profile)
