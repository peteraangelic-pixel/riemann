from kaggriculture_lab.reactive_candidates import SafetyBudget, market_candidates, unit_candidates
from kaggriculture_lab.reactive_state import estimate
from test_reactive_state import observation


def test_urgent_water_is_bounded_top_unit_candidate():
    state = estimate(observation())
    candidates = unit_candidates(state, state.own.units[0], SafetyBudget(max_unit_candidates=4))
    assert len(candidates) <= 4
    assert candidates[0].reason in {"route to dying crop", "harvest standing mature crop"}
    assert any(c.reason == "route to dying crop" for c in candidates)


def test_standing_animal_generates_feed_care_and_collection():
    obs = observation()
    obs["farms"][0]["farmer"] = [0, 1]
    obs["private"]["inventories"][0] = {"WHEAT": 2}
    state = estimate(obs)
    actions = {c.action for c in unit_candidates(state, state.own.units[0])}
    assert ("FEED",) in actions
    assert ("CARE",) not in actions  # cared_today is already true in the fixture
    assert ("HARVEST",) in actions


def test_market_never_sells_feed_reserve_or_overspends_cash():
    state = estimate(observation())
    candidates = market_candidates(state, SafetyBudget(cash_reserve=1200, feed_days=2))
    assert all(c.action[0] != "BUY_SEED" or state.own.cash - c.cost >= 1200 for c in candidates)
    assert all(not (c.action[:2] == ("SELL", "WHEAT") and c.action[2] > state.own.shed.get("WHEAT", 0))
               for c in candidates)


def test_candidate_order_is_deterministic():
    state = estimate(observation())
    assert unit_candidates(state, state.own.units[0]) == unit_candidates(state, state.own.units[0])
    assert market_candidates(state) == market_candidates(state)
