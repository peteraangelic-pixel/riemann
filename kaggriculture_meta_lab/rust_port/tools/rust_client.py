"""Thin Python subprocess API. Sweeps/Wilson/statistics stay with the caller.

Batch mode starts ONE Rust process and caches each tape once. Avoid thousands
of per-game subprocesses when evaluating a seed sweep.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
import tempfile
from typing import Iterable

DEFAULT_BINARY = Path(__file__).resolve().parents[1] / "target/release/kg_sim"


@dataclass(frozen=True)
class Job:
    seed: int
    tape_a: Path | str
    tape_b: Path | str
    reverse: bool = False


def _options(steps, step_mode, trim_hands, config):
    args = ["--steps", str(steps), "--step-mode", step_mode]
    if trim_hands:
        args.append("--trim-hands")
    if config is not None:
        args += ["--config", str(Path(config).resolve())]
    return args


def _invoke(args, expected, allow_errors):
    result = subprocess.run(args, capture_output=True, text=True)
    try:
        lines = [json.loads(line) for line in result.stdout.splitlines()]
    except json.JSONDecodeError as e:
        raise RuntimeError(f"simulator did not return JSON: {result.stderr}\n{result.stdout}") from e
    if len(lines) != expected:
        raise RuntimeError(f"expected {expected} simulator results, received {len(lines)}: {result.stderr}\n{result.stdout}")
    errors = [line for line in lines if line.get("errors") or line.get("rewards") is None]
    if not allow_errors and (errors or result.returncode):
        raise RuntimeError(f"simulator failure (do not count as a win/loss): {errors or result.stderr}")
    return lines


def replay(job: Job, *, binary=DEFAULT_BINARY, steps=720, step_mode="kaggle", trim_hands=False, config=None):
    args = [str(Path(binary).resolve()), "--seed", str(job.seed), "--tape-a", str(Path(job.tape_a).resolve()), "--tape-b", str(Path(job.tape_b).resolve())]
    args += _options(steps, step_mode, trim_hands, config)
    if job.reverse:
        args.append("--reverse-seats")
    return _invoke(args, 1, False)[0]


def replay_many(jobs: Iterable[Job], *, binary=DEFAULT_BINARY, steps=720, step_mode="kaggle", threads=None, trim_hands=False, config=None, allow_errors=False):
    jobs = list(jobs)
    if not jobs:
        return []
    with tempfile.TemporaryDirectory(prefix="kg-jobs-") as directory:
        csv_path = Path(directory) / "jobs.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for job in jobs:
                writer.writerow([job.seed, Path(job.tape_a).resolve(), Path(job.tape_b).resolve(), int(job.reverse)])
        args = [str(Path(binary).resolve()), "--jobs", str(csv_path)]
        args += _options(steps, step_mode, trim_hands, config)
        if threads is not None:
            args += ["--threads", str(threads)]
        return _invoke(args, len(jobs), allow_errors)
