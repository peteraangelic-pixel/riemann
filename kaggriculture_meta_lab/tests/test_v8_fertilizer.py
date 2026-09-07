"""V8 fertilizer variant: loads, never collapses (the RESERVE bug), and applies
fertilizer in the field. Strength vs V7 is measured by scripts/run_tournament
(the 40-game closed-loop gate passed: 67.5% score rate, CI 52-80)."""
import importlib.util
from pathlib import Path

from kaggriculture_lab.engine import play_game

ROOT = Path(__file__).resolve().parents[1]
V8 = ROOT / "agents" / "variants" / "agent_v8_fert.py"


def _load():
    spec = importlib.util.spec_from_file_location("v8_fert", V8)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_v8_constants_are_safe():
    mod = _load()
    # Shed fertilizer reserve must stay 0: storing cheap fertilizer in the
    # 100-cap shed blocks premium end-of-day deposits (the ~300 collapse cause).
    assert mod.FERTILIZER_RESERVE == 0
    # Crop mix is deliberately unchanged from V7 (strawberries not bundled).
    assert mod.STRAWBERRY_TARGET == 0
    assert mod.FERT_DETOUR_RADIUS == 2


def test_v8_does_not_collapse_and_finishes():
    mod = _load()
    res = play_game(mod.act, "starter", seed=20260907, steps=720)
    assert res["error"] is None
    assert res["statuses"] == ["DONE", "DONE"]
    # A healthy farm ends far above the starting cash; the broken routing ended
    # at ~300-800. Require a realistic lower bound to guard against regression.
    assert res["rewards"][0] > 15000, res["rewards"]


def test_v8_applies_fertilizer_in_field():
    mod = _load()
    res = play_game(mod.act, "starter", seed=20260907, steps=720, record_trace=True)
    assert res.get("replay")
    fert = 0
    for row in res["replay"]["steps"]:
        action = row[0].get("action") or {}
        for op in [action.get("farmer"), *action.get("hands", [])]:
            if isinstance(op, list) and op and op[0] == "FERTILIZE":
                fert += 1
    assert fert >= 1  # cow fertilizer is applied to premium crops, not just sold
