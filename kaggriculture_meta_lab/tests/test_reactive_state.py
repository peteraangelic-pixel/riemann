from kaggriculture_lab.reactive_state import estimate


def observation():
    own = [[None for _ in range(10)] for _ in range(10)]
    opp = [[None for _ in range(10)] for _ in range(10)]
    own[0][0] = {"kind": "PLANT", "crop": "WHEAT", "planted_day": 2,
                 "yield_units": 3, "watered_today": False, "consecutive_unwatered": 1,
                 "fertilized_until_day": 0}
    own[1][0] = {"kind": "PASTURE", "animal": "COW", "yield_units": 2,
                 "fed_today": False, "cared_today": True, "fertilizer_available": True}
    own[9][9] = "LOCKED"
    opp[0][0] = {"kind": "PLANT", "crop": "STRAWBERRY", "planted_day": 1,
                 "yield_units": 1}
    return {
        "player": 0, "step": 5 * 24 + 17, "day": 5, "hour": 17,
        "farms": [
            {"money": 1234, "farmer": [4, 4], "hands": [[3, 4]],
             "unlocked_quadrants": ["NW"], "tiles": own},
            {"money": 900, "farmer": [4, 4], "hands": [],
             "unlocked_quadrants": ["NW"], "tiles": opp},
        ],
        "private": {"seeds": {"WHEAT": 7}, "shed": {"MILK": 3},
                    "inventories": [{"WHEAT": 2}, {"FERTILIZER": 1}]},
        "market": {"prices": {"WHEAT": 31.5}, "inventory": {"WHEAT": 20}},
        "town": {"unlocked_shops": ["PET_CAFE"]},
    }


def test_exact_state_estimator_exposes_policy_inputs():
    state = estimate(observation(), {"turnsPerDay": 24, "shedCapacity": 100})
    assert (state.step, state.day, state.hour, state.player) == (137, 5, 17, 0)
    assert state.own.cash == 1234
    assert state.own.hands == 1
    assert state.own.seeds == {"WHEAT": 7}
    assert state.own.shed == {"MILK": 3}
    assert state.own.units[1].position == (3, 4)
    assert state.own.units[1].load == 1
    assert state.prices["WHEAT"] == 31.5
    assert state.shops == ("PET_CAFE",)


def test_estimator_classifies_tiles_and_opponent_without_private_leak():
    state = estimate(observation())
    wheat = state.own.crops("WHEAT")[0]
    assert wheat.position == (0, 0)
    assert wheat.mature(state.day)
    assert wheat.unwatered_days == 1
    assert wheat.fertilized_until == 0  # integer zero is valid state, not missing
    cow = state.own.animals("COW")[0]
    assert cow.fertilizer_ready and not cow.fed
    assert state.own.locked_cells == ((9, 9),)
    assert len(state.own.free_cells) == 97
    assert len(state.opponent.crops("STRAWBERRY")) == 1
    assert state.opponent.seeds == {} and state.opponent.shed == {}
