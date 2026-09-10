from kaggriculture_lab.price_selector import choose_sell


def test_fail_closed_on_incomplete_schema():
    baseline = {"type": "PASS"}
    result = choose_sell({}, [], baseline)
    assert result.action == baseline


def test_selects_covered_premium_sale():
    obs = {
        "prices": {"MILK": 120, "STRAWBERRY": 100},
        "recent_prices": {"MILK": 90, "STRAWBERRY": 100},
        "inventory": {"MILK": 3, "STRAWBERRY": 4},
        "shed_capacity": 20,
    }
    actions = [
        {"type": "SELL", "product": "MILK", "quantity": 2},
        {"type": "SELL", "product": "STRAWBERRY", "quantity": 4},
    ]
    result = choose_sell(obs, actions, {"type": "PASS"})
    assert result.product == "MILK"
    assert result.action == actions[0]


def test_does_not_sell_uncovered_inventory():
    obs = {
        "prices": {"MILK": 120},
        "recent_prices": {"MILK": 90},
        "inventory": {"MILK": 1},
        "shed_capacity": 20,
    }
    action = {"type": "SELL", "product": "MILK", "quantity": 2}
    assert choose_sell(obs, [action], {"type": "PASS"}).product is None
