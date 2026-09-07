"""Sweep harness mechanics: variant generation, config expansion, grid."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.sweep import expand_config, make_variant, project_game_budget  # noqa: E402

BASE = ROOT / "agents" / "variants" / "agent_v8_fert.py"


def test_make_variant_rewrites_constant(tmp_path, monkeypatch):
    import scripts.sweep as sweep
    monkeypatch.setattr(sweep, "SWEEP_DIR", tmp_path)
    out = make_variant(BASE, "t_detour7", {"FERT_DETOUR_RADIUS": 7})
    text = out.read_text(encoding="utf-8")
    assert "FERT_DETOUR_RADIUS = 7" in text
    # everything else is untouched (the base value is gone)
    assert "FERT_DETOUR_RADIUS = 2" not in text


def test_make_variant_unknown_constant_errors(tmp_path, monkeypatch):
    import scripts.sweep as sweep
    monkeypatch.setattr(sweep, "SWEEP_DIR", tmp_path)
    try:
        make_variant(BASE, "t_bad", {"NO_SUCH_CONSTANT": 1})
    except SystemExit:
        return
    raise AssertionError("expected SystemExit for an unknown constant")


def test_expand_config_variants_and_grid():
    cfg = {
        "variants": [
            {"name": "a", "params": {"FERT_DETOUR_RADIUS": 1}},
            {"name": "b", "params": {"HANDS_MAX": 13}},
        ],
        "grid": {"FERT_DETOUR_RADIUS": [1, 2], "HANDS_MAX": [11, 13]},
    }
    variants = expand_config(cfg)
    # 2 explicit + 4 grid, de-duplicated (detour1/hands13 combos unique)
    assert len(variants) == 6
    names = [v["name"] for v in variants]
    assert "a" in names and "b" in names
    assert any(v["name"].startswith("grid") for v in variants)
    # all params dicts carry both keys when from grid
    grid_v = [v for v in variants if v["name"].startswith("grid")]
    assert all(set(v["params"]) == {"FERT_DETOUR_RADIUS", "HANDS_MAX"} for v in grid_v)


def test_expand_config_dedupes_identical_params():
    cfg = {"variants": [
        {"name": "x", "params": {"FERT_DETOUR_RADIUS": 2}},
        {"name": "y", "params": {"FERT_DETOUR_RADIUS": 2}},
    ]}
    assert len(expand_config(cfg)) == 1


def test_direct_b21_budget_includes_control_only_in_finals():
    budget = project_game_budget(
        spec_count=23,
        include_base=False,
        top_k=4,
        screen_games=18,
        promote_games=100,
        final_games=68,
        finals_include_baseline=True,
    )
    assert budget == {"screen": 828, "promote": 800, "finals": 1360, "total": 2988}


def test_direct_b21_config_anchors_untouched_control():
    cfg = json.loads((ROOT / "sweeps" / "v10_b21_opening_direct.json").read_text(encoding="utf-8"))
    assert cfg["base"] == cfg["baseline"]
    assert cfg["include_untouched_base"] is False
    assert cfg["finals_include_baseline"] is True
    assert cfg["baseline_name"] == "CONTROL_B21_S16"
    assert len(expand_config(cfg)) == 23
