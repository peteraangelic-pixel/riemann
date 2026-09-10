#!/usr/bin/env python3
"""Probe: what does the champion tape leave on the table?

Self-play of a static tape (mirror) on N seeds, then report final money,
leftover shed inventory value (at final prices), and per-day money curve.
Answers: is a forced endgame sell-all override worth anything?
"""
import importlib.util
import json
import sys
from pathlib import Path

SEAT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SEAT.parent / "rust_port" / "tools"))
from py_reference import PythonReplay  # noqa: E402


def load_tape(path):
    spec = importlib.util.spec_from_file_location("tape_probe", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    A = getattr(m, "ACTIONS", None) or getattr(m, "_ACTIONS", None)
    if isinstance(A[0], dict):
        A = [A, A]
    return A


def main():
    tape_path, seeds_json = sys.argv[1], sys.argv[2]
    seeds = json.loads(seeds_json)
    tape = load_tape(tape_path)
    print(f"{'seed':>6} {'final0':>9} {'final1':>9} {'shedval0':>9} {'shedval1':>9} {'shed_n0':>7} {'shed_n1':>7}")
    curves = {}
    for s in seeds:
        r = PythonReplay(tape, tape, s, steps=720, trim_hands=True)
        money_curve = [[], []]
        while r.advance():
            if r.step % 24 == 0:
                snap = r.snapshot()
                for p in (0, 1):
                    money_curve[p].append(round(snap["farms"][p]["money"]))
        snap = r.snapshot()
        prices = snap["market"].get("prices", {})
        finals, shedvals, shedns = [], [], []
        for p in (0, 1):
            finals.append(snap["farms"][p]["money"])
            shed = r.state[p].observation.private.get("shed", {})
            v = sum((shed.get(k, 0) or 0) * float(prices.get(k, 0) or 0) for k in shed)
            shedvals.append(round(v))
            shedns.append(sum((n or 0) for n in shed.values()))
        print(f"{s:>6} {finals[0]:>9.0f} {finals[1]:>9.0f} {shedvals[0]:>9} {shedvals[1]:>9} {shedns[0]:>7} {shedns[1]:>7}")
        curves[s] = money_curve
    out = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    if out:
        out.write_text(json.dumps({"curves": curves}, indent=1))


if __name__ == "__main__":
    main()
