"""Tests for the structural tape generator and the Rust backend wiring.

These are CPU-cheap: they verify transforms on the decoded ACTIONS and the
backend's tape-detection / fallback logic, without playing 720-step games.
The one end-to-end dollar-parity check (identity == champion) runs a single
game and is kept small.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

import structural_gen as sg  # noqa: E402


def _hires(actions):
    return sum(1 for seat in actions for step in seat
               for o in (step.get("market") or []) if o and o[0] == "HIRE")


def _fert_qty(actions):
    return sum(o[2] for seat in actions for step in seat
               for o in (step.get("market") or [])
               if o and o[0] == "BUY_PRODUCT" and len(o) > 2 and o[1] == "FERTILIZER")


def test_identity_reproduces_champion():
    champ = sg.load_champion_actions()
    assert sg.apply_mutations(sg.load_champion_actions(), {}) == champ
    # explicit identity knobs
    assert sg.apply_mutations(sg.load_champion_actions(),
                              {"hire_scale": 1.0, "fert_scale": 1.0}) == champ


def test_hire_scale_both_directions():
    champ = sg.load_champion_actions()
    base = _hires(champ)
    assert _hires(sg.apply_mutations(sg.load_champion_actions(), {"hire_scale": 0.7})) \
        == pytest.approx(base * 0.7, abs=2)
    assert _hires(sg.apply_mutations(sg.load_champion_actions(), {"hire_scale": 1.3})) \
        == pytest.approx(base * 1.3, abs=2)


def test_fert_scale():
    champ = sg.load_champion_actions()
    assert _fert_qty(sg.apply_mutations(sg.load_champion_actions(), {"fert_scale": 2.0})) \
        == pytest.approx(_fert_qty(champ) * 2.0, abs=2)


def test_no_late_buy_removes_only_late_orders():
    champ = sg.load_champion_actions()
    out = sg.apply_mutations(sg.load_champion_actions(), {"no_late_buy": 650})
    late = [o for seat in out for t, step in enumerate(seat) if t >= 650
            for o in (step.get("market") or []) if o and str(o[0]).startswith("BUY")]
    assert late == []
    # early buys untouched
    assert sg.apply_mutations(sg.load_champion_actions(), {"no_late_buy": 10 ** 9}) \
        == champ


def test_liquidation_covers_all_kinds_at_end():
    out = sg.apply_mutations(sg.load_champion_actions(), {"liquidate_from": 700})
    for seat in range(2):
        for t in (718, 719):
            kinds = {o[1] for o in (out[seat][t].get("market") or [])
                     if o and o[0] == "SELL" and len(o) > 2 and o[2] == 500}
            for need in ("WHEAT", "CARROT", "MILK", "FERTILIZER", "WOOL",
                         "MELON", "STRAWBERRY"):
                assert need in kinds


def test_variant_file_roundtrip_and_dollar_parity():
    """A generated identity variant plays byte-identically to the champion."""
    from kaggriculture_lab.engine import play_game

    tmp = ROOT / "agents" / "sweeps" / "_test_ident.py"
    try:
        sg.write_variant({"hire_scale": 1.0, "fert_scale": 1.0}, tmp)
        spec = importlib.util.spec_from_file_location("test_ident_variant", tmp)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        champ_path = ROOT / "agents" / "current" / "agent_v9_b21_s16.py"
        cspec = importlib.util.spec_from_file_location("test_champ", champ_path)
        cmod = importlib.util.module_from_spec(cspec)
        cspec.loader.exec_module(cmod)

        rc = play_game(cmod.agent, cmod.agent, seed=0)["rewards"]
        ri = play_game(mod.agent, mod.agent, seed=0)["rewards"]
        assert rc == ri == [60225.0, 60976.0]  # Fable's documented Rust parity value
    finally:
        tmp.unlink(missing_ok=True)


def test_rust_backend_detects_tape_agents():
    from kaggriculture_lab import rust_backend as rb

    champ = str(ROOT / "agents" / "current" / "agent_v9_b21_s16.py")
    assert rb._is_tape_spec(champ) is True
    assert rb._is_tape_spec("pass") is False
    assert rb._is_tape_spec("tape:replay.json") is False
    assert rb._is_tape_spec("wrap:a.py:b.py") is False
    assert rb._is_tape_spec("nonexistent_file.py") is False


def test_rust_backend_falls_back_without_binary(monkeypatch):
    """With no kg_sim binary, run_auto must use the Python engine, not raise."""
    from kaggriculture_lab import rust_backend as rb
    from kaggriculture_lab.tournament import build_jobs

    monkeypatch.setattr(rb, "rust_binary", lambda: None)
    champ = str(ROOT / "agents" / "current" / "agent_v9_b21_s16.py")
    jobs = build_jobs(champ, [champ], games=1, start_seed=0,
                      swap_seats=True, steps=720, tag="fb")
    rows = rb.run_auto(jobs, workers=2, progress_every=100)
    assert len(rows) == 2
    assert all(r["outcome"] in ("win", "loss", "tie") for r in rows)
    assert all(r["error"] is None for r in rows)
