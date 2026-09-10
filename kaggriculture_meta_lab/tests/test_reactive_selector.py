from kaggriculture_lab.reactive_candidates import SEED_COST, SafetyBudget
from kaggriculture_lab.reactive_selector import decide, select_action
from kaggriculture_lab.reactive_state import estimate
from test_reactive_state import observation


def test_selector_emits_exact_shape_and_avoids_unit_collision():
    action = decide(observation())
    assert set(action) == {"farmer", "hands", "market"}
    assert action["farmer"] == ["PLANT", "WHEAT"]
    assert action["hands"] == [["WEST"]]
    # The stationary farmer at (4,4) and moving hand ending at (2,4) remain distinct.
    assert action["market"] == [["SELL", "MILK", 3]]


def test_market_selection_accounts_for_orders_sequentially():
    obs = observation()
    obs["farms"][0]["money"] = 270
    obs["market"]["prices"].update({"CARROT": 100, "TOMATO": 1000,
                                      "STRAWBERRY": 1000, "MELON": 1000})
    budget = SafetyBudget(cash_reserve=250)
    action = select_action(estimate(obs), budget)
    cash = 270.0
    shed = dict(obs["private"]["shed"])
    for order in action["market"]:
        op, item, qty = order
        if op == "SELL":
            assert 0 < qty <= shed.get(item, 0)
            shed[item] -= qty
            cash += qty * obs["market"]["prices"].get(item, 0)
        elif op == "BUY_SEED":
            cash -= qty * SEED_COST[item]
            assert cash >= budget.cash_reserve
    assert cash >= budget.cash_reserve


def test_selector_is_deterministic():
    state = estimate(observation())
    assert select_action(state) == select_action(state)
