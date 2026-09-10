#!/usr/bin/env python3
"""Driver for push-triggered Rust LAB batches in GitHub Actions.

Reads kaggriculture_meta_lab/seat_087c0/lab_queue.json:
  {"jobs": [{"tag": ..., "candidates": [...], "opponents": [...],
             "start_seed": N, "games": M, "threads": T, "parity_k": K}, ...]}
Runs rust_h2h.py per job (seeds start_seed..start_seed+games-1, both seats)
and writes kaggriculture_meta_lab/seat_087c0/results/rust_<tag>.json.
Any failure aborts with nonzero exit; partial results are still on disk.
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
