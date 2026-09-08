#!/usr/bin/env python3
"""Measure actual wall time, not an assumed 8-20x speedup.

Conservative baseline: direct pinned Python interpreter, without Kaggle's
observation copies, agent deepcopies, renderer, or replay logging. Rust timings
include subprocess startup, JSON/CSV I/O and result parsing; batches parse each
tape once. Sweep generation, agent search and statistics are NOT benchmarked.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import time

from export_tape import extract, write_tape
from py_reference import PythonReplay, action_turns
from rust_client import DEFAULT_BINARY, Job, replay, replay_many

ROOT = Path(__file__).resolve().parents[1]


def measure(fn, repeats):
    times = []
    value = None
    for _ in range(repeats):
        start = time.perf_counter()
        value = fn()
        times.append(time.perf_counter() - start)
    return statistics.median(times), times, value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, default=DEFAULT_BINARY)
    parser.add_argument("--games", type=int, default=64)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--steps", type=int, default=720)
    parser.add_argument("--trim-hands", action="store_true")
    args = parser.parse_args()
    if min(args.games, args.threads, args.repeats, args.steps) < 1:
        parser.error("counts must be positive")
    work = ROOT / "work/benchmark"
    work.mkdir(parents=True, exist_ok=True)
    path = work / "example.json"
    tape = extract()
    write_tape(path, tape)
    jobs = [Job(seed, path, path, bool(seed % 2)) for seed in range(args.games)]
    options = dict(binary=args.binary, steps=args.steps, trim_hands=args.trim_hands)
    # Warm filesystem/code paths before timed samples; no setup hidden in a loop.
    replay(jobs[0], **options)
    replay_many(jobs, threads=args.threads, **options)
    py, py_samples, expected = measure(lambda: [PythonReplay(tape, tape, job.seed, steps=args.steps, reverse=job.reverse, trim_hands=args.trim_hands).run() for job in jobs], args.repeats)
    single, single_samples, single_results = measure(lambda: [replay(job, **options) for job in jobs], args.repeats)
    serial, serial_samples, serial_results = measure(lambda: replay_many(jobs, threads=1, **options), args.repeats)
    parallel, parallel_samples, parallel_results = measure(lambda: replay_many(jobs, threads=args.threads, **options), args.repeats)
    for results in (single_results, serial_results, parallel_results):
        assert [r["rewards"] for r in results] == expected
        assert all(not r["errors"] for r in results)
    cpu = None
    cpu_file = Path("/proc/cpuinfo")
    if cpu_file.exists():
        cpu = next((line.split(":", 1)[1].strip() for line in cpu_file.read_text().splitlines() if line.startswith("model name")), None)
    try:
        rustc = subprocess.check_output(["rustc", "--version"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        rustc = None
    report = {
        "baseline": "direct unmodified Python interpreter; no framework/policy/statistics overhead",
        "rust_timing_includes": "process launch + tape/CSV parsing + simulation + result parsing",
        "games_per_sample": args.games, "repeats": args.repeats, "steps": args.steps,
        "action_turns_per_game": action_turns(args.steps), "trim_hands": args.trim_hands,
        "rayon_threads": args.threads, "logical_cpus": os.cpu_count(), "cpu": cpu,
        "platform": platform.platform(), "python": platform.python_version(), "rustc": rustc,
        "binary_sha256": hashlib.sha256(args.binary.read_bytes()).hexdigest(),
        "median_seconds": {"python": py, "rust_one_process_per_game": single, "rust_batch_1_thread": serial, "rust_batch_parallel": parallel},
        "speedup_vs_python": {"one_process_per_game": py / single, "batch_1_thread": py / serial, "batch_parallel": py / parallel},
        "parallel_speedup_vs_rust_1_thread": serial / parallel,
        "samples_seconds": {"python": py_samples, "rust_one_process_per_game": single_samples, "rust_batch_1_thread": serial_samples, "rust_batch_parallel": parallel_samples},
        "warning": "This is not a measurement of the user's complete 14k-game sweep, nor a 16-physical-core benchmark.",
    }
    (ROOT / "work/benchmark.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
