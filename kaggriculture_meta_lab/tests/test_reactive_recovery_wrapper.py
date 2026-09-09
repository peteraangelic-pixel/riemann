from kaggriculture_meta_lab.agents.variants.reactive_recovery_wrapper import _local_safe_action, recover


def _obs(tile, *, day=10, hour=12, inventory=None):
    tiles = [[None for _ in range(10)] for _ in range(10)]
    tiles[0][0] = tile
    return {
        "player": 0,
        "step": day * 24 + hour,
        "day": day,
        "hour": hour,
        "farms": [
            {"farmer": [0, 0], "hands": [], "tiles": tiles},
            {"farmer": [0, 0], "hands": [], "tiles": [[None] * 10 for _ in range(10)]},
        ],
        "private": {"inventories": [inventory or {}]},
    }


def test_urgent_crop_overrides_unsafe_base_move():
    tile = {"kind": "PLANT", "crop": "WHEAT", "planted_day": 9,
            "yield_units": 1, "watered_today": False, "consecutive_unwatered": 1}
    out = recover(_obs(tile), {"farmer": ["EAST"], "hands": [], "market": [["HIRE"]]})
    assert out["farmer"] == ["WATER"]
    assert out["market"] == [["HIRE"]]


def test_endgame_mature_crop_is_harvested_without_extra_water():
    tile = {"kind": "PLANT", "crop": "WHEAT", "planted_day": 25,
            "yield_units": 3, "watered_today": False, "consecutive_unwatered": 0}
    assert _local_safe_action(tile, {}, 28, 3) == ["HARVEST"]


def test_animal_service_preconditions_are_visible():
    animal = {"kind": "PASTURE", "animal": "COW", "yield_units": 0,
              "fed_today": False, "cared_today": False, "fertilizer_available": True}
    assert _local_safe_action(animal, {"WHEAT": 1}, 10, 5) == ["FEED"]
    assert _local_safe_action(animal, {}, 10, 5) == ["CARE"]


def test_nonurgent_local_tile_preserves_productive_base_action():
    tile = {"kind": "PLANT", "crop": "WHEAT", "planted_day": 10,
            "yield_units": 1, "watered_today": True, "consecutive_unwatered": 0}
    base = {"farmer": ["EAST"], "hands": [], "market": []}
    assert recover(_obs(tile), base)["farmer"] == ["EAST"]
