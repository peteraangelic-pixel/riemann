#!/usr/bin/env python3
"""Large, measured tape batch: no 14k-game Python extrapolation or policy search.

Times the complete Python client -> Rust -> validated results round trip. The
same jobs run at every thread count; an ordered IEEE-754 reward digest must
match for ALL games and repeats. An evenly spaced subset is also evaluated by
the unmodified Python interpreter, outside the timed Rust samples.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import struct
import subprocess
import time

from export_tape import extract, validate_tape, write_tape
from py_reference import PythonReplay, action_turns
from rust_client import DEFAULT_BINARY, Job, replay_many

ROOT = Path(__file__).resolve().parents[1]


def reward_digest(results):
    digest = hashlib.sha256()
    for row in results:
        if row["errors"] or row["rewards"] is None:
            raise AssertionError("failed game in performance batch")
        digest.update(struct.pack(">2d", *row["rewards"]))
    return digest.hexdigest()


def sample_indices(games, count):
    count = min(games, count)
    if count == 1:
        return [0]
    return [i * (games - 1) // (count - 1) for i in range(count)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, default=DEFAULT_BINARY)
    parser.add_argument("--tape-a", type=Path)
    parser.add_argument("--tape-b", type=Path)
    parser.add_argument("--games", type=int, default=14000)
    parser.add_argument("--threads", default="1,4,16", help="comma-separated counts; one-thread control is always included")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--python-checks", type=int, default=64)
    parser.add_argument("--steps", type=int, default=720)
    parser.add_argument("--trim-hands", action="store_true")
    parser.add_argument("--timeout", type=float, default=300, help="maximum wall time per Rust batch")
    parser.add_argument("--output", type=Path, default=ROOT / "work/batch-benchmark.json")
    args = parser.parse_args()
    try:
        threads = list(dict.fromkeys([1] + [int(t) for t in args.threads.split(",")]))
    except ValueError:
        parser.error("--threads must be a comma-separated list of integers")
    if min(args.games, args.repeats, args.python_checks, args.steps, args.timeout, *threads) <= 0:
        parser.error("counts and timeout must be positive")
    work = ROOT / "work/batch-benchmark"
    work.mkdir(parents=True, exist_ok=True)
    if args.tape_a is None:
        args.tape_a = work / "example.json"
        write_tape(args.tape_a, extract())
    args.tape_a = args.tape_a.resolve()
    args.tape_b = (args.tape_b or args.tape_a).resolve()
    args.binary = args.binary.resolve()
    a = validate_tape(json.loads(args.tape_a.read_text()))
    b = a if args.tape_b == args.tape_a else validate_tape(json.loads(args.tape_b.read_text()))
    jobs = [Job(seed, args.tape_a, args.tape_b, bool(seed % 2)) for seed in range(args.games)]
    options = {"binary": args.binary, "steps": args.steps, "trim_hands": args.trim_hands, "timeout": args.timeout}
    expected_digest = None
    reference = None
    timings = []
    for count in threads:
        replay_many(jobs[:min(32, len(jobs))], threads=count, **options)
        samples = []
        for _ in range(args.repeats):
            start = time.perf_counter()
            rows = replay_many(jobs, threads=count, **options)
            samples.append(time.perf_counter() - start)
            # Checksumming is outside the timing; client I/O and validation are inside.
            digest = reward_digest(rows)
            if expected_digest is None:
                expected_digest, reference = digest, rows
            if digest != expected_digest:
                raise AssertionError(f"results/order changed with {count} threads")
        median = statistics.median(samples)
        timings.append({"threads": count, "median_seconds": median, "samples_seconds": samples,
                        "games_per_second": args.games / median})
    checked = sample_indices(args.games, args.python_checks)
    for index in checked:
        job = jobs[index]
        rewards = PythonReplay(a, b, job.seed, steps=args.steps, reverse=job.reverse, trim_hands=args.trim_hands).run()
        if struct.pack(">2d", *rewards) != struct.pack(">2d", *reference[index]["rewards"]):
            raise AssertionError(f"Python mismatch at job {index}, seed={job.seed}")
    for row in timings:
        row["speedup_vs_rust_1_thread"] = timings[0]["median_seconds"] / row["median_seconds"]
    cpu = None
    if Path("/proc/cpuinfo").exists():
        cpu = next((line.split(":", 1)[1].strip() for line in Path("/proc/cpuinfo").read_text().splitlines() if line.startswith("model name")), None)
    try:
        rustc = subprocess.check_output(["rustc", "--version"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        rustc = None
    report = {
        "status": "passed", "workload": "one fixed tape pair, seeds 0..games-1, alternating reversed seats",
        "games_per_sample": args.games, "repeats": args.repeats, "steps": args.steps,
        "action_turns_per_game": action_turns(args.steps), "trim_hands": args.trim_hands,
        "ordered_reward_sha256": expected_digest, "all_thread_counts_and_repeats_identical": True,
        "python_checked_jobs": len(checked), "python_sample_first_last_indices": [checked[0], checked[-1]],
        "logical_cpus": os.cpu_count(), "cpu": cpu, "platform": platform.platform(),
        "python": platform.python_version(), "rustc": rustc, "revision": os.environ.get("GITHUB_SHA"),
        "binary_sha256": hashlib.sha256(args.binary.read_bytes()).hexdigest(),
        "tape_a_sha256": hashlib.sha256(args.tape_a.read_bytes()).hexdigest(),
        "tape_b_sha256": hashlib.sha256(args.tape_b.read_bytes()).hexdigest(),
        "timings": timings,
        "measurement": "complete client call including CSV writing, subprocess launch, tape parsing, simulation, result parsing and validation",
        "scope": "Not the full user's sweep, no agent search/statistics; 16 workers do not imply 16 physical CPU cores. No estimated Python speedup is reported.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
