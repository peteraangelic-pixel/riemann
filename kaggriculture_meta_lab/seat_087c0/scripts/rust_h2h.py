#!/usr/bin/env python3
"""Fast H2H for STATIC tape agents via the Rust kg_sim batch simulator.

Same CLI and log format as fast_h2h.py, but jobs run through
rust_port/target/release/kg_sim (Rayon batches, ~3500 games/s in CI)
instead of the Python interpreter. Intended for GitHub Actions LAB runs
(see .github/workflows/kaggriculture-seat087c0-rust-lab.yml); works
anywhere the release binary is built.

Tapes are loaded with fast_h2h.load_tape (import-based, handles this
seat's ACTIONS/_ACTIONS formats incl. single-stream mirroring and the
hardened try/except agent wrapper), serialized once per distinct file to
temp JSON ([seat0, seat1]), and replayed with per-tape hand trimming.

Correctness rules (same as the sibling LAB):
  * rewards[0] is always the candidate: kg_sim swaps rewards back when
    seats are reversed (lib.rs outcome()), same convention as py_reference.
  * Rust rows carry only rewards/errors; any error aborts (exit 3) -
    failures are never silently scored.
  * --py-parity-k K replays the first K jobs of EVERY pair through the
    pinned Python interpreter and aborts (exit 2) on any mismatch.

CLI: rust_h2h.py '[cand_paths]' '[opp_paths]' '[seeds]' log.json
       [--binary PATH] [--threads N] [--steps 720] [--py-parity-k K]
"""
import json
import os
import sys
import tempfile
import time
from pathlib import Path

SEAT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SEAT / "scripts"))
sys.path.insert(0, str(SEAT.parent / "rust_port" / "tools"))
from fast_h2h import load_tape  # noqa: E402
from py_reference import PythonReplay  # noqa: E402
from rust_client import Job, replay_many  # noqa: E402

DEFAULT_BINARY = SEAT.parent / "rust_port" / "target" / "release" / "kg_sim"


def parse(argv):
    binary = str(DEFAULT_BINARY)
    threads = os.cpu_count() or 4
    steps = 720
    parity_k = 0
    rest = []
    i = 0
    while i < len(argv):
        if argv[i] == "--binary":
            binary = argv[i + 1]; i += 2
        elif argv[i] == "--threads":
            threads = int(argv[i + 1]); i += 2
        elif argv[i] == "--steps":
            steps = int(argv[i + 1]); i += 2
        elif argv[i] == "--py-parity-k":
            parity_k = int(argv[i + 1]); i += 2
        else:
            rest.append(argv[i]); i += 1
    cand_files, opp_files, seeds, logpath = (json.loads(rest[0]), json.loads(rest[1]),
                                             json.loads(rest[2]), rest[3])
    return cand_files, opp_files, seeds, logpath, binary, threads, steps, parity_k


def main():
    cand_files, opp_files, seeds, logpath, binary, threads, steps, parity_k = parse(sys.argv[1:])
    bpath = Path(binary)
    if not (bpath.exists() and os.access(bpath, os.X_OK)):
        raise SystemExit(f"rust binary missing/not executable: {bpath} (run cargo build --release in rust_port)")
    log = []
    with tempfile.TemporaryDirectory(prefix="kg-rust-h2h-") as td:
        td = Path(td)
        tape_paths = {}
        for p in dict.fromkeys(cand_files + opp_files):
            A = load_tape(p)
            tp = td / (Path(p).stem + ".tape.json")
            tp.write_text(json.dumps(A, separators=(",", ":")))
            tape_paths[p] = tp
        for cpath in cand_files:
            for opath in opp_files:
                if Path(cpath).stem == Path(opath).stem:
                    continue
                jobs = [Job(seed=s, tape_a=tape_paths[cpath], tape_b=tape_paths[opath],
                            reverse=bool(sw)) for s in seeds for sw in (0, 1)]
                t0 = time.time()
                rows = replay_many(jobs, binary=bpath, steps=steps, threads=threads,
                                   trim_hands_a=True, trim_hands_b=True,
                                   allow_errors=True)
                dt = time.time() - t0
                bad = [(j, r) for j, r in zip(jobs, rows) if r.get("errors") or r.get("rewards") is None]
                if bad:
                    for j, r in bad[:5]:
                        print(f"  !! RUST ERROR {cpath} vs {opath} seed {j.seed} swap {int(j.reverse)}: {r.get('errors')}", flush=True)
                    raise SystemExit(f"rust errors: {len(bad)}/{len(rows)} - no results accepted (exit 3)")
                if parity_k:
                    cand = json.loads(tape_paths[cpath].read_text())
                    opp = json.loads(tape_paths[opath].read_text())
                    for j, r in zip(jobs[:parity_k], rows[:parity_k]):
                        rp = PythonReplay(cand, opp, j.seed, steps=steps,
                                          reverse=j.reverse, trim_hands=True)
                        while rp.advance():
                            pass
                        pr = rp.rewards()
                        rr = r["rewards"]
                        if (pr[0], pr[1]) != (rr[0], rr[1]):
                            print(f"PARITY FAIL {Path(cpath).stem} vs {Path(opath).stem} "
                                  f"seed {j.seed} swap {int(j.reverse)}: rust={rr} python={pr}", flush=True)
                            sys.exit(2)
                    print(f"  parity OK ({min(parity_k, len(jobs))} games)", flush=True)
                w = l = t = 0; ms = sc = so = 0.0; games = []
                for j, r in zip(jobs, rows):
                    r0, r1 = r["rewards"]
                    w, l, t = w + (r0 > r1), l + (r0 < r1), t + (r0 == r1)
                    ms += r0 - r1; sc += r0; so += r1
                    games.append({"seed": j.seed, "swap": int(j.reverse), "r0": r0, "r1": r1})
                n = w + l + t
                line = {"cand": Path(cpath).stem, "opp": Path(opath).stem, "w": w, "l": l, "t": t,
                        "margin_sum": ms, "mean_cand": sc / n, "mean_opp": so / n,
                        "backend": "rust", "threads": threads, "steps": steps,
                        "rust_seconds": round(dt, 2), "games_per_s": round(n / dt, 2),
                        "py_parity_k": min(parity_k, n) if parity_k else 0, "games": games}
                log.append(line)
                print(json.dumps({k: v for k, v in line.items() if k != "games"}) + f"  [{dt:.1f}s]", flush=True)
    Path(logpath).write_text(json.dumps(log, indent=1))


if __name__ == "__main__":
    main()
