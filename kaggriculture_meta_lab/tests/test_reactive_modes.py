from kaggriculture_lab.reactive_modes import choose_mode, classify_public_pressure, r2_safe_candidates


def test_endgame_mode_is_deterministic():
    assert choose_mode({"step": 700}).mode == "ENDGAME"


def test_cash_recovery_precedes_expansion():
    assert choose_mode({"step": 100, "cash": 20, "available_cells": 0}).mode == "RECOVERY"


def test_animals_mode_has_priority_when_maintenance_is_due():
    assert choose_mode({"step": 100, "cash": 1000, "animals_needing_feed": 2}).mode == "ANIMALS"


def test_public_pressure_does_not_use_opponent_identity():
    pressure = classify_public_pressure({"prices": {"WHEAT": 20}, "demand": {"WHEAT": 100}, "wheat_stock": 10, "opponent": "secret-name"})
    assert pressure["price_pressure"] == 80
    assert pressure["production_pressure"] == 90


def test_r2_filters_actions_by_selected_mode():
    obs = {"step": 100, "cash": 1000, "animals_needing_care": 1,
           "legal_actions": [{"type": "CARE"}, {"type": "PLANT"}, {"type": "BUILD_COOP"}]}
    assert r2_safe_candidates(obs) == [{"type": "CARE"}]
