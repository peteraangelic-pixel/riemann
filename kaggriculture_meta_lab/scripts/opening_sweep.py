"""Sweep the WHEAT OPENING of a tape agent, closed-loop vs the champion.

The strongest lever found so far is the scripted opening (the first few turns'
market orders): the live champion `agent_v9_b21_s16.py` is a V7 tape whose
opening buys 21 wheat and sells 16 (reserve 3), and that beat every other
buy/sell combination in the TOP49 open-loop grid (research/V9_V7_OPENING_GRID).

This script does the same search but in the CLOSED loop (two real policies on
shared seeds, both seats), which is what the final Bradley-Terry ranking
actually rewards. It generates tape variants by patching the opening orders of
a base tape, plays each against the champion, and writes a committable report.

Patches (per variant):
    buy   : first-turn [BUY_PRODUCT, WHEAT, n]
    sell  : first-turn [SELL, WHEAT, k]

The rest of the tape (the elite full-game schedule) is unchanged, so an
opening variant is the champion with a different wheat-quantity opener.

Examples:
    python scripts/opening_sweep.py --workers 16
    python scripts/opening_sweep.py --games 40 --reserve 3,5,7
"""
from __future__ import annotations

import argparse
import base64
import copy
import importlib.util
import json
import sys
import time
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kaggriculture_lab.stats import aggregate  # noqa: E402
from kaggriculture_lab.tournament import (  # noqa: E402
    _available_mem_gb, build_jobs, default_workers, run,
)

CHAMPION = ROOT / "agents" / "current" / "agent_v9_b21_s16.py"
GEN_DIR = ROOT / "agents" / "openings"


def _load_tape(path: Path):
    spec = importlib.util.spec_from_file_location(f"tape_{path.stem}", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.ACTIONS, getattr(m, "SELL_WHEAT", None), getattr(m, "BUY_WHEAT", None)


def _encode(actions) -> str:
    return base64.b85encode(zlib.compress(
        json.dumps(actions, separators=(",", ":")).encode(), 9)).decode()


def _patch_order(market, op, item, qty):
    """Set qty on the first matching [op, item, *] order; return True if found."""
    for order in market:
        if len(order) >= 3 and order[0] == op and order[1] == item:
            order[2] = qty
            return True
    return False


def make_opening_variant(base_actions, buy: int, sell: int, name: str) -> Path:
    """Patch the opening WHEAT quantities in BOTH seat tapes and emit an agent.

    Champion layout (observed): turn 0 market = [[BUY_PRODUCT,WHEAT,buy]];
    turn 1 market[0] = [SELL,WHEAT,sell] followed by seed/hire/animal orders.
    We touch ONLY those two quantities, preserving every other opening order.
    """
    schedules = copy.deepcopy(base_actions)
    for seat_actions in schedules:
        m0 = seat_actions[0].get("market", [])
        if not _patch_order(m0, "BUY_PRODUCT", "WHEAT", buy):
            m0.insert(0, ["BUY_PRODUCT", "WHEAT", buy])
        # SELL lives in turn 1 for the champion
        found = False
        for step_actions in seat_actions[1:4]:
            if _patch_order(step_actions.get("market", []), "SELL", "WHEAT", sell):
                found = True
                break
        if not found:
            seat_actions[1].setdefault("market", []).insert(0, ["SELL", "WHEAT", sell])
    payload = _encode(schedules)
    GEN_DIR.mkdir(parents=True, exist_ok=True)
    source = (
        '"""Tape opening variant: BUY {buy} / SELL {sell} wheat, base champion."""\n'
        "import base64, copy, json, zlib\n"
        "ACTIONS = json.loads(zlib.decompress(base64.b85decode(PAYLOAD)).decode())\n"
        "def agent(observation, configuration):\n"
        "    p = int(observation.get('player', 0))\n"
        "    step = min(int(observation.get('step', 0)), len(ACTIONS[p]) - 1)\n"
        "    action = copy.deepcopy(ACTIONS[p][step])\n"
        "    farms = observation.get('farms') or []\n"
        "    hands = (farms[p].get('hands') or []) if p < len(farms) else []\n"
        "    action['hands'] = (action.get('hands') or [])[:len(hands)]\n"
        "    return action\n"
        "act = agent\n"
    ).replace("{buy}", str(buy)).replace("{sell}", str(sell)).replace(
        "PAYLOAD", repr(payload))
    out = GEN_DIR / f"{name}.py"
    out.write_text(source, encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=str(CHAMPION))
    ap.add_argument("--games", type=int, default=25, help="seeds (x2 seats) per variant")
    ap.add_argument("--workers", type=int, default=default_workers())
    ap.add_argument("--buys", default="17,19,21,23,25")
    ap.add_argument("--reserve", default="3,5", help="sell = buy - reserve")
    ap.add_argument("--start-seed", type=int, default=20264000)
    args = ap.parse_args()

    mem_safe = max(1, int(_available_mem_gb() / 0.45))
    if args.workers > mem_safe:
        print(f"[note] workers clamped {args.workers} -> {mem_safe} (RAM)")
        args.workers = mem_safe

    base_actions, _, _ = _load_tape(Path(args.base))
    buys = [int(x) for x in args.buys.split(",") if x.strip()]
    reserves = [int(x) for x in args.reserve.split(",") if x.strip()]

    # generate variants + an untouched champion control
    variants = [("b21_s16_champ", Path(args.base))]
    for b in buys:
        for r in reserves:
            s = b - r
            if s <= 0:
                continue
            name = f"b{b:02d}_s{s:02d}"
            path = make_opening_variant(base_actions, b, s, name)
            variants.append((name, path))

    t0 = time.perf_counter()
    lines = ["# Opening sweep (closed loop vs champion tape)",
             f"base={Path(args.base).name}  games/var={args.games} seeds x2 seats  "
             f"workers={args.workers}",
             f"variants={len(variants)}", ""]

    jobs = []
    for name, path in variants:
        jobs += build_jobs(str(path), [str(Path(args.base))], args.games,
                           args.start_seed, swap_seats=True, steps=720, tag=name)
    print(f"[opening sweep] {len(variants)} variants x {args.games*2} games = {len(jobs)}")
    rows = run(jobs, args.workers, progress_every=max(40, len(jobs) // 5))

    aggs = {t: aggregate([r for r in rows if r["tag"] == t])
            for t in sorted({r["tag"] for r in rows})}
    ranked = sorted(aggs.items(), key=lambda kv: (kv[1].score_rate, kv[1].mean_margin),
                    reverse=True)
    lines.append(f"  {'variant':<18} {'W-L-T':>9} {'score%':>7} {'Wilson95':>13} "
                 f"{'margin':>9} {'err':>3}")
    for name, a in ranked:
        lines.append(f"  {name:<18} {f'{a.wins}-{a.losses}-{a.ties}':>9} "
                     f"{a.score_rate*100:7.1f} {f'{a.ci_low*100:.0f}-{a.ci_high*100:.0f}':>13} "
                     f"{a.mean_margin:+9.0f} {a.errors:3d}")
    lines.append("")
    lines.append("Score is vs the champion tape: 50% = identical opener.")
    lines.append("")
    lines.append("WARNING: a high win-rate with ~$0 median margin (near-tie "
                 "mirror games) is a tie-break artefact, NOT strength. Two near-"
                 "identical tapes differ by a handful of dollars; that breaks "
                 "coin-flip games one way. PROMOTE only a variant that ALSO shows "
                 "higher ABSOLUTE cash vs a DIVERSE opponent (run validate.py with "
                 "--baseline agents/current/agent_v7_scripted.py) AND vs the TOP49 "
                 "open-loop corpus. Mirror win-rate alone proves nothing.")
    lines.append(f"\nelapsed {time.perf_counter()-t0:.0f}s")

    out = ROOT / "results" / f"opening-sweep-{time.strftime('%Y%m%d-%H%M%S')}.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {out}")
    print("\n".join(lines[4:]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
