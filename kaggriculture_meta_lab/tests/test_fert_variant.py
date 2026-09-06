"""The fertilizer variant must (a) load on top of V7 and (b) actually inject
BUY_PRODUCT FERTILIZER orders when fertilizer is cheap."""
import importlib.util
from pathlib import Path

from kaggriculture_lab.agents import resolve, _resolve_path
from kaggriculture_lab.engine import play_game

ROOT = Path(__file__).resolve().parents[1]


def _load_variant():
    spec = f"wrap:{ROOT/'agents/ref/agent_v7.py'}:{ROOT/'agents/variants/fert_buyer.py'}"
    return resolve(spec)


def test_fert_wrapper_loads_and_runs():
    fn = _load_variant()
    # play a short closed-loop game against pass; must not crash and must finish
    res = play_game(fn, "pass", seed=123, steps=120)
    assert res["error"] is None, res.get("error")
    assert res["statuses"] == ["DONE", "DONE"]


def test_fert_orders_when_cheap():
    # Build a synthetic obs with cheap fertilizer and enough cash.
    variant_mod_path = _resolve_path(str(ROOT / "agents/variants/fert_buyer.py"))
    spec = importlib.util.spec_from_file_location("fert_mod", variant_mod_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    calls = []

    def base_fn(obs, config=None):
        calls.append(1)
        return {"farmer": ["PASS"], "hands": [], "market": []}

    agent = mod.wrap(base_fn, type("M", (), {})())
    obs = {
        "player": 0,
        "farms": [{"money": 5000, "hands": [], "farmer": [0, 0], "tiles": []}],
        "private": {"shed": {"FERTILIZER": 0}, "inventories": []},
        "market": {"prices": {"FERTILIZER": 5}},
    }
    out = agent(obs)
    verbs = [o[0] for o in out["market"] if isinstance(o, list) and o]
    assert "BUY_PRODUCT" in verbs
    buy = [o for o in out["market"] if o and o[0] == "BUY_PRODUCT"][0]
    assert buy[1] == "FERTILIZER" and buy[2] > 0


def test_no_fert_orders_when_expensive():
    variant_mod_path = _resolve_path(str(ROOT / "agents/variants/fert_buyer.py"))
    spec = importlib.util.spec_from_file_location("fert_mod2", variant_mod_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    def base_fn(obs, config=None):
        return {"farmer": ["PASS"], "hands": [], "market": []}

    agent = mod.wrap(base_fn, type("M", (), {})())
    obs = {
        "player": 0,
        "farms": [{"money": 5000}],
        "private": {"shed": {"FERTILIZER": 0}, "inventories": []},
        "market": {"prices": {"FERTILIZER": 999}},  # too expensive
    }
    out = agent(obs)
    assert not any(o and o[0] == "BUY_PRODUCT" for o in out["market"])
