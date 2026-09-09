from kaggriculture_lab.reactive_planner import PlannerConfig, choose_action, generate_candidates


def test_inventory_is_sold_when_price_is_safe():
    action = choose_action({"cash": 500, "inventory": {"WHEAT": 3}, "prices": {"WHEAT": 25}})
    assert action["type"] == "SELL"
    assert action["product"] == "WHEAT"


def test_endgame_ignores_price_floor():
    action = choose_action(
        {"step": 700, "cash": 0, "inventory": {"WHEAT": 3}, "prices": {"WHEAT": 0}},
        PlannerConfig(endgame_step=648),
    )
    assert action["type"] == "SELL"


def test_cash_reserve_blocks_expensive_productive_action():
    obs = {
        "cash": 100,
        "legal_actions": [
            {"type": "PLANT", "cost": 90, "expected_gain": 1000},
            {"type": "WATER", "cost": 90, "expected_gain": 1},
        ],
    }
    actions = generate_candidates(obs, PlannerConfig(cash_reserve=250))
    assert all(a.action["type"] != "PLANT" for a in actions)
    assert any(a.action["type"] == "WATER" for a in actions)


def test_candidate_order_is_deterministic_and_bounded():
    obs = {"cash": 1000, "legal_actions": [
        {"type": "WATER", "expected_gain": 5},
        {"type": "HARVEST", "expected_gain": 10},
    ]}
    a = generate_candidates(obs, PlannerConfig(max_candidates=2))
    b = generate_candidates(obs, PlannerConfig(max_candidates=2))
    assert a == b
    assert len(a) == 2
