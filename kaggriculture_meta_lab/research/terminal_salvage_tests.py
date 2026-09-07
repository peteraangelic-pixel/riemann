"""Logic tests for a research prototype; NOT evidence of stronger play."""
import copy
from types import SimpleNamespace

from terminal_salvage import plan_terminal


def observation(step=716):
    tiles = [[None for _ in range(10)] for _ in range(10)]
    return {"step": step, "player": 0, "farms": [{"tiles": tiles, "farmer": [4, 4], "hands": []}],
            "private": {"shed": {}, "inventories": [{}]}, "market": {"prices": {"WHEAT": 25, "MILK": 160}}}


def test_untouched_baseline_outside_window():
    action = {"farmer": ["NORTH"], "hands": [], "market": [["HIRE"]]}
    assert plan_terminal(action, observation(10), {}, 4) is action


def test_no_control_before_last_day_boundary():
    action = {"farmer": ["NORTH"], "hands": [], "market": [["HIRE"]]}
    assert plan_terminal(action, observation(23), {"episodeSteps": 26}, 8) is action


def test_move_harvest_drop_fits_exactly_three_ticks_and_does_not_mutate_input():
    obs = observation()
    obs["farms"][0]["tiles"][5][4] = {"kind": "PLANT", "crop": "WHEAT", "yield_units": 3, "planted_day": 20, "max_lifespan_step": -1}
    original = copy.deepcopy(obs)
    action = {"farmer": ["PASS"], "hands": [], "market": []}
    assert plan_terminal(action, obs, {}, 4)["farmer"] == ["SOUTH"]
    assert obs == original
    obs["step"] = 717
    obs["farms"][0]["farmer"] = [4, 5]
    assert plan_terminal(action, obs, {}, 4)["farmer"] == ["HARVEST"]
    obs["step"] = 718
    obs["farms"][0]["tiles"][5][4] = None
    obs["private"]["inventories"] = [{"WHEAT": 3}]
    result = plan_terminal(action, obs, SimpleNamespace(episodeSteps=720), 4)
    assert result["farmer"] == ["DROP"]
    assert ["SELL", "WHEAT", 99999] in result["market"]
    assert len(result["market"]) <= 10


def test_reservations_prevent_duplicate_target_assignment():
    obs = observation()
    obs["farms"][0]["tiles"][5][4] = {"kind": "PLANT", "crop": "WHEAT", "yield_units": 3, "planted_day": 20, "max_lifespan_step": -1}
    obs["farms"][0]["hands"] = [[4, 4]]
    obs["private"]["inventories"].append({})
    result = plan_terminal({"market": []}, obs, {}, 4)
    assert result["farmer"] == ["SOUTH"]
    assert result["hands"] == [["PASS"]]


def test_full_shed_does_not_destroy_carried_goods():
    obs = observation(718)
    obs["private"] = {"shed": {"WHEAT": 100}, "inventories": [{"MILK": 3}]}
    assert plan_terminal({"market": []}, obs, {}, 4)["farmer"] == ["PASS"]


def test_partial_deposit_does_not_drop_overflow_or_animal():
    obs = observation(718)
    obs["private"] = {"shed": {"WHEAT": 98}, "inventories": [{"MILK": 3, "COW": 1}]}
    result = plan_terminal({"market": []}, obs, {}, 4)
    assert result["farmer"] == ["PLACE", "MILK", 2]


def test_immature_or_unreachable_target_is_not_harvested():
    obs = observation(718)
    obs["farms"][0]["tiles"][4][4] = {"kind": "PLANT", "crop": "WHEAT", "yield_units": 1, "planted_day": 29, "max_lifespan_step": -1}
    assert plan_terminal({"market": []}, obs, {}, 4)["farmer"] == ["PASS"]
    obs["farms"][0]["tiles"][4][4]["planted_day"] = 20
    # Even mature grain cannot be harvested AND dropped in the one remaining tick.
    assert plan_terminal({"market": []}, obs, {}, 4)["farmer"] == ["PASS"]
