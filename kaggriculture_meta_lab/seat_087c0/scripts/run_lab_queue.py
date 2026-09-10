#!/usr/bin/env python3
"""Driver for push-triggered Rust LAB batches in GitHub Actions.

Reads kaggriculture_meta_lab/seat_087c0/lab_queue.json. Two job types:
  {"type": "h2h", "tag": ..., "candidates": [...], "opponents": [...],
   "start_seed": N, "games": M, "threads": T, "parity_k": K}
    -> results/rust_<tag>.json via rust_h2h.py.
  {"type": "search", "tag": ..., "donors": {name: path}, ...evolution params...}
    -> results/rust_<tag>.json + candidates/<tag>_winner.py (if emitted)
       via search_rust_evolve.py.
"type" defaults to "h2h". Any failure aborts with nonzero exit; partial
results are still on disk.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

SEAT = Path(__file__).resolve().parents[1]
QUEUE = SEAT / "lab_queue.json"


def main():
    queue = json.loads(QUEUE.read_text())
    jobs = queue.get("jobs", [])
    only = os.environ.get("LAB_TAG", "")
    if only:
        jobs = [j for j in jobs if j.get("tag") == only]
    if not jobs:
        raise SystemExit("lab_queue.json has no jobs (for LAB_TAG filter)")
    binary = str(SEAT.parent / "rust_port" / "target" / "release" / "kg_sim")
    for job in jobs:
        tag = job["tag"]
        if job.get("type", "h2h") == "search":
            out = SEAT / "results" / f"rust_{tag}.json"
            agent = SEAT / "candidates" / f"{tag}_winner.py"
            cmd = [sys.executable, str(SEAT / "scripts" / "search_rust_evolve.py")]
            cmd += ["--donors"] + [f"{k}={v}" for k, v in job["donors"].items()]
            cmd += ["--units-german", job["units_german"], "--units-v3", job["units_v3"]]
            cmd += ["--controls"] + [f"{k}={v}" for k, v in job["controls"].items()]
            for key in ("idx_v4", "idx_hybrid", "idx_v3", "population", "generations",
                        "elite", "finalists", "block", "cut_max", "train_seeds",
                        "seed_base", "holdout_start", "holdout_games", "threads",
                        "mask_seed"):
                if key in job:
                    cmd += [f"--{key.replace('_', '-')}", str(job[key])]
            cmd += ["--engine", job.get("engine", "rust"), "--binary", binary,
                    "--output", str(out), "--agent-output", str(agent), "--tag", tag]
            print(f"### LAB search {tag}", flush=True)
            subprocess.run(cmd, check=True)
            print(f"### LAB search {tag} done -> {out}", flush=True)
            continue
        if job.get("type", "h2h") == "ablate":
            out = SEAT / "results" / f"rust_{tag}.json"
            cmd = [sys.executable, str(SEAT / "scripts" / "ablate_blocks.py"),
                   "--base", job["base"], "--donor", job["donor"]]
            if "block" in job:
                cmd += ["--block", str(job["block"])]
            cmd += ["--controls"] + [f"{k}={v}" for k, v in job["controls"].items()]
            cmd += ["--start-seed", str(job["start_seed"]), "--games", str(job["games"]),
                    "--binary", binary, "--threads", str(job.get("threads", 4)),
                    "--output", str(out), "--tag", tag]
            print(f"### LAB ablate {tag}", flush=True)
            subprocess.run(cmd, check=True)
            print(f"### LAB ablate {tag} done -> {out}", flush=True)
            continue
        seeds = list(range(int(job["start_seed"]), int(job["start_seed"]) + int(job["games"])))
        out = SEAT / "results" / f"rust_{tag}.json"
        cmd = [sys.executable, str(SEAT / "scripts" / "rust_h2h.py"),
               json.dumps(job["candidates"]), json.dumps(job["opponents"]),
               json.dumps(seeds), str(out), "--binary", binary,
               "--threads", str(job.get("threads", 4)),
               "--py-parity-k", str(job.get("parity_k", 8))]
        print(f"### LAB job {tag}: {' '.join(cmd[1:])}", flush=True)
        subprocess.run(cmd, check=True)
        print(f"### LAB job {tag} done -> {out}", flush=True)


if __name__ == "__main__":
    main()
