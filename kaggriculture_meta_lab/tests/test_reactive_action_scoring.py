from pathlib import Path
import importlib.util

PATH = Path(__file__).parents[1] / "agents" / "variants" / "agent_v11_reactive_score.py"
spec = importlib.util.spec_from_file_location("v11_score", PATH)
mod = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mod)


def test_evening_water_overtakes_harvest():
    claimed = set()
    target = mod._select_target(
        [("harvest", [(1, 0)]), ("water", [(0, 2)])], 0, 0, 17, claimed
    )
    assert target == (0, 2)
    assert claimed == {(0, 2)}


def test_daytime_harvest_uses_live_value_and_distance():
    claimed = set()
    target = mod._select_target(
        [("harvest", [(4, 0), (1, 0)])], 0, 0, 8, claimed,
        {(4, 0): 200, (1, 0): 0},
    )
    assert target == (4, 0)


def test_claims_prevent_duplicate_worker_target():
    claimed = set()
    first = mod._select_target([("urgent_water", [(1, 0), (2, 0)])], 0, 0, 18, claimed)
    second = mod._select_target([("urgent_water", [(1, 0), (2, 0)])], 0, 0, 18, claimed)
    assert (first, second) == ((1, 0), (2, 0))


def test_fertilizer_never_beats_unwatered_crop_in_evening():
    target = mod._select_target(
        [("fertilize", [(0, 0)]), ("water", [(2, 0)])], 0, 0, 20, set()
    )
    assert target == (2, 0)
