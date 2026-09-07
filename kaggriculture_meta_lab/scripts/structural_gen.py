"""Structural tape generator: mutate the *body* of the champion tape, not just
the wheat opening.

The opening (BUY_WHEAT/SELL_WHEAT) is saturated - V10 showed every nearby wheat
quantity is a near-tie or worse. Real headroom is in the production structure
(the elite score 161-171k open-loop vs our ~89k). This module emits tape
*variants* as self-contained `.py` files that the sweep funnel
(`scripts/sweep.py`) loads directly - the same way it loads the champion.

A generated variant decodes the champion blob, applies a list of structural
mutations to the decoded ACTIONS, then re-encodes. Mutations are deliberately
*conservative / bounded* - they scale or truncate levers the elite push harder
(workers via HIRE, fertilizer), never invent large untested order blocks:

  * hire_scale       multiply the number of HIRE orders in the hiring window
                     (champion hires 284 workers; try fewer/more). Only hires
                     strictly before `hire_deadline` are scaled.
  * fert_scale       multiply FERTILIZER BUY quantities (champion buys ~23).
  * no_late_buy      drop every BUY_* order at/after a cutoff step (dead
                     inventory investment near the end of the season).
  * liquidate_from   ensure the final sell-off (SELL <kind> 500 across all
                     product kinds) starts at this step on both end steps;
                     if the tape already liquidates later, move it earlier.

Every mutation has an identity default that reproduces the champion byte-for-byte
(the sweep `--include-untouched-base` control and our tests rely on this).

Usage:
    # one named variant file
    python scripts/structural_gen.py --out agents/sweeps/v_fertx2.py \
        --set fert_scale=2.0 hire_scale=1.1
    # emit a whole sweep config (grid) for the funnel
    python scripts/structural_gen.py --emit-sweep sweeps/v11_struct.json \
        --grid '{"hire_scale":[0.85,1.0,1.15],"fert_scale":[1.0,1.5,2.0]}'
"""
from __future__ import annotations

import argparse
import base64
import copy
import json
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHAMPION = ROOT / "agents" / "current" / "agent_v9_b21_s16.py"

# Structural knobs and their identity defaults.
KNOBS = ("hire_scale", "fert_scale", "no_late_buy", "liquidate_from",
         "hire_deadline", "fert_deadline")
DEFAULTS = {"hire_scale": 1.0, "fert_scale": 1.0, "no_late_buy": 0,
            "liquidate_from": 0, "hire_deadline": 720, "fert_deadline": 720}

PRODUCT_KINDS = ("WHEAT", "CARROT", "MILK", "FERTILIZER", "WOOL",
                 "MELON", "STRAWBERRY", "EGG")  # EGG included harmlessly


def load_champion_actions() -> list:
    """Decode the champion tape -> fresh deep-copied [seat][step] ACTIONS."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "kg_champ_struct", CHAMPION)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # applies BUY_WHEAT/SELL_WHEAT overrides
    return copy.deepcopy(mod.ACTIONS)


def _iter_market(step_action: dict):
    return step_action.get("market") or []


def apply_mutations(actions: list, params: dict) -> list:
    p = {**DEFAULTS, **{k: v for k, v in params.items() if v is not None}}
    hire_scale = float(p["hire_scale"])
    fert_scale = float(p["fert_scale"])
    no_late_buy = int(p["no_late_buy"])
    liquidate_from = int(p["liquidate_from"])
    hire_deadline = int(p["hire_deadline"])
    fert_deadline = int(p["fert_deadline"])

    for seat in range(2):
        tape = actions[seat]
        hire_seen = 0       # global HIRE counter across the whole seat (Bresenham)
        hire_kept = 0
        for step_idx, act in enumerate(tape):
            market = act.get("market")
            if not market:
                continue
            new_market = []
            for order in list(market):
                op = order[0] if order else ""
                # --- late buy removal (dead investment) ---
                if no_late_buy and op.startswith("BUY") and step_idx >= no_late_buy:
                    continue
                # --- worker hiring scale (only within the hiring window) ---
                if op == "HIRE" and step_idx < hire_deadline and hire_scale != 1.0:
                    hire_seen += 1
                    target = int(round(hire_seen * hire_scale))
                    if hire_scale < 1.0:
                        # drop ~(1-scale) of hires: keep while the rounded target
                        # keeps advancing faster than the kept count
                        if target <= hire_kept:
                            continue  # this HIRE is removed by the scale
                        hire_kept += 1
                        new_market.append(order)
                    else:
                        # add (target - already_kept - 1 for this original) hires
                        new_market.append(order)
                        extra = target - hire_kept - 1
                        hire_kept = target
                        for _ in range(max(0, extra)):
                            new_market.append(["HIRE"])
                    continue
                if op == "HIRE":
                    hire_seen += 1
                    hire_kept += 1
                # --- fertilizer quantity scale (within fert window) ---
                if (op == "BUY_PRODUCT" and len(order) >= 3 and order[1] == "FERTILIZER"
                        and step_idx < fert_deadline and fert_scale != 1.0):
                    qty = order[2]
                    new_qty = max(1, int(round(qty * fert_scale)))
                    new_market.append(["BUY_PRODUCT", "FERTILIZER", new_qty])
                    continue
                new_market.append(order)
            act["market"] = new_market

        # --- endgame liquidation: make sure the final sell-off covers all kinds
        if liquidate_from and liquidate_from < len(tape) - 1:
            sell_block = [["SELL", kind, 500] for kind in PRODUCT_KINDS]
            # remove any existing all-500 liquidation at/after the cutoff, then
            # place the block on the last two steps (mirrors champion structure)
            for t in range(liquidate_from, len(tape)):
                mk = tape[t].get("market") or []
                mk = [o for o in mk if not (o and o[0] == "SELL" and len(o) > 2 and o[2] == 500)]
                tape[t]["market"] = mk
            for t in (len(tape) - 2, len(tape) - 1):
                if t >= liquidate_from:
                    existing = tape[t].get("market") or []
                    tape[t]["market"] = existing + [o for o in sell_block
                                                    if o not in existing]
    return actions


def encode_blob(actions: list) -> str:
    raw = json.dumps(actions, separators=(",", ":")).encode("utf-8")
    return base64.b85encode(zlib.compress(raw, 9)).decode("ascii")


VARIANT_TEMPLATE = '''"""Auto-generated structural variant of agent_v9_b21_s16 (champion).
Params: {params}
Generated by scripts/structural_gen.py - do not edit by hand; regenerate.
"""
import base64, copy, json, zlib

BUY_WHEAT = {buy_wheat}
SELL_WHEAT = {sell_wheat}
_BLOB = {blob!r}
ACTIONS = json.loads(zlib.decompress(base64.b85decode(_BLOB)))
for _actions in ACTIONS:
    _actions[0]["market"] = [["BUY_PRODUCT", "WHEAT", BUY_WHEAT]]
    for _order in _actions[1].get("market", []):
        if _order and _order[0] == "SELL" and _order[1] == "WHEAT":
            _order[2] = SELL_WHEAT


def agent(observation, configuration):
    p = int(observation.get("player", 0))
    step = min(int(observation.get("step", 0)), 719)
    action = copy.deepcopy(ACTIONS[p][step])
    farms = observation.get("farms") or []
    live = (farms[p].get("hands") or []) if p < len(farms) else []
    if action.get("hands"):
        action["hands"] = action["hands"][:len(live)]
    return action


act = agent
'''


def make_variant_source(params: dict, buy_wheat: int = 21, sell_wheat: int = 16) -> str:
    actions = apply_mutations(load_champion_actions(), params)
    blob = encode_blob(actions)
    return VARIANT_TEMPLATE.format(params=json.dumps(params, sort_keys=True),
                                   buy_wheat=buy_wheat, sell_wheat=sell_wheat,
                                   blob=blob)


def write_variant(params: dict, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(make_variant_source(params), encoding="utf-8")
    return out


def _parse_set(items: list[str]) -> dict:
    params = dict(DEFAULTS)
    for item in items:
        key, _, val = item.partition("=")
        key = key.strip()
        if key not in KNOBS:
            raise SystemExit(f"unknown knob {key!r}; valid: {', '.join(KNOBS)}")
        params[key] = float(val) if "." in val else int(float(val))
    return params


def emit_sweep_config(grid: dict, out: Path) -> Path:
    """Build a sweep .json that scans structural variants vs the champion."""
    import itertools
    keys = list(grid)
    variants = []
    out_dir = ROOT / "agents" / "sweeps"
    for combo in itertools.product(*[grid[k] for k in keys]):
        params = dict(zip(keys, combo))
        name = "struct_" + "_".join(f"{k[:4]}{v}" for k, v in params.items()
                                    if float(v) != float(DEFAULTS.get(k, 1.0))
                                    or k in ("no_late_buy", "liquidate_from"))
        name = name.replace(".", "p")
        vpath = Path("agents/sweeps") / f"{name}.py"
        write_variant(params, out_dir / f"{name}.py")
        variants.append({"name": name, "path": str(vpath).replace("\\", "/"),
                         "params": params})
    cfg = {
        "base": "agents/current/agent_v9_b21_s16.py",
        "baseline": "agents/current/agent_v9_b21_s16.py",
        "baseline_name": "b21s16",
        "start_seed": 20264100,
        "screen_games": 20,
        "promote_games": 120,
        "final_games": 175,
        "top_k": 6,
        "promotion_objective": "rating",
        "finals_include_baseline": True,
        "include_untouched_base": True,
        "variants": variants,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, help="write a single variant .py here")
    ap.add_argument("--set", dest="assign", action="append", default=[],
                    help="knob=value, repeatable (e.g. --set fert_scale=2.0)")
    ap.add_argument("--emit-sweep", type=Path,
                    help="write a sweep .json (with --grid) instead of one file")
    ap.add_argument("--grid", type=str,
                    help='JSON grid, e.g. \'{"hire_scale":[0.85,1.0,1.15]}\'')
    args = ap.parse_args()

    if args.emit_sweep:
        if not args.grid:
            raise SystemExit("--emit-sweep needs --grid '{...}'")
        grid = json.loads(args.grid)
        path = emit_sweep_config(grid, args.emit_sweep)
        print(f"wrote sweep config {path}")
        return 0

    params = _parse_set(args.assign)
    if not args.out:
        raise SystemExit("give --out path.py (or --emit-sweep)")
    write_variant(params, args.out if args.out.is_absolute() else ROOT / args.out)
    print(f"wrote variant {args.out} params={json.dumps(params, sort_keys=True)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
