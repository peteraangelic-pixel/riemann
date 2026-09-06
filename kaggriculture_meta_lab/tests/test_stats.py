from kaggriculture_lab.stats import (
    wilson, aggregate, promotion_gate, bradley_terry,
)


def _rows(wins, losses, ties=0, margin=100.0):
    rows = []
    for _ in range(wins):
        rows.append({"outcome": "win", "margin": margin, "self_reward": 2, "opp_reward": 1})
    for _ in range(losses):
        rows.append({"outcome": "loss", "margin": -margin, "self_reward": 1, "opp_reward": 2})
    for _ in range(ties):
        rows.append({"outcome": "tie", "margin": 0.0, "self_reward": 1, "opp_reward": 1})
    return rows


def test_wilson_bounds():
    lo, hi = wilson(5, 10)
    assert 0 < lo < 0.5 < hi < 1
    assert wilson(0, 10)[0] == 0.0
    assert abs(wilson(10, 10)[1] - 1.0) < 1e-9


def test_aggregate():
    a = aggregate(_rows(60, 40))
    assert a.games == 100 and abs(a.win_rate - 0.6) < 1e-9
    assert a.ci_low < 0.6 < a.ci_high and a.errors == 0


def test_aggregate_excludes_errors():
    a = aggregate(_rows(10, 0) + [{"outcome": "error"}] * 2)
    assert a.games == 10 and a.errors == 2


def test_gate():
    strong = aggregate(_rows(160, 40))
    ok, _ = promotion_gate(strong, min_games=200)
    assert ok
    weak = aggregate(_rows(90, 110))
    ok2, reasons = promotion_gate(weak, min_games=200)
    assert not ok2 and reasons


def test_bradley_terry_ordering():
    labels = ["strong", "weak"]
    # strong beats weak 90% of the time, both seats
    wins = {("strong", "weak"): 18.0, ("weak", "strong"): 2.0}
    games = {("strong", "weak"): 20, ("weak", "strong"): 20}
    bt = bradley_terry(wins, games, labels)
    assert bt["strong"] > bt["weak"]
