"""Opening-tape patching: change only the wheat quantities, keep the rest."""
import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.opening_sweep import _load_tape, _patch_order, make_opening_variant  # noqa


def test_patch_order_sets_qty_in_place():
    mkt = [["BUY_PRODUCT", "WHEAT", 21], ["SELL", "WHEAT", 16]]
    assert _patch_order(mkt, "SELL", "WHEAT", 20) is True
    assert mkt[1] == ["SELL", "WHEAT", 20]
    assert _patch_order(mkt, "BUY_PRODUCT", "WHEAT", 23) is True
    assert mkt[0] == ["BUY_PRODUCT", "WHEAT", 23]


def test_patch_order_missing_returns_false():
    assert _patch_order([["HIRE"]], "SELL", "WHEAT", 5) is False


def test_variant_changes_only_wheat_quantities():
    actions, _, _ = _load_tape(ROOT / "agents" / "current" / "agent_v9_b21_s16.py")
    out = make_opening_variant(actions, 23, 20, "t_b23_s20")
    import importlib.util
    spec = importlib.util.spec_from_file_location("t_b23", out)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    for seat in range(2):
        # turn 0 buy updated
        assert ["BUY_PRODUCT", "WHEAT", 23] in m.ACTIONS[seat][0]["market"]
        # turn 1 sell updated but the seed/hire/animal orders preserved
        mkt1 = m.ACTIONS[seat][1]["market"]
        assert ["SELL", "WHEAT", 20] in mkt1
        assert ["BUY_SEED", "MELON", 12] in mkt1
        assert mkt1.count(["HIRE"]) == 5
        assert ["BUY_ANIMAL", "COW", 2] in mkt1
    # length unchanged (full schedule preserved)
    assert len(m.ACTIONS[0]) == 720


def test_identity_variant_keeps_quantities():
    actions, _, _ = _load_tape(ROOT / "agents" / "current" / "agent_v9_b21_s16.py")
    out = make_opening_variant(copy.deepcopy(actions), 21, 16, "t_ident")
    import importlib.util
    spec = importlib.util.spec_from_file_location("t_ident", out)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert ["BUY_PRODUCT", "WHEAT", 21] in m.ACTIONS[0][0]["market"]
    assert ["SELL", "WHEAT", 16] in m.ACTIONS[0][1]["market"]
