"""Thin Python subprocess API. Sweeps/Wilson/statistics stay with the caller.

Batch mode starts ONE Rust process and caches each tape once. Avoid thousands
of per-game subprocesses when evaluating a seed sweep. Responses are validated
before they can enter statistics; malformed/missing/non-finite scores always
raise SimulatorError, even with allow_errors=True.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
import json
import math
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


class SimulatorError(RuntimeError):
    """A game failure, broken protocol, failed process or timeout; never a score."""


def _options(steps, step_mode, trim_hands, config, trim_hands_a=False, trim_hands_b=False):
    args = ["--steps", str(steps), "--step-mode", step_mode]
    if trim_hands:
        args.append("--trim-hands")
    if trim_hands_a:
        args.append("--trim-hands-a")
    if trim_hands_b:
        args.append("--trim-hands-b")
    if config is not None:
        args += ["--config", str(Path(config).resolve())]
    return args


def _excerpt(text, limit=2000):
    if len(text) <= limit:
        return text
    return text[:limit // 2] + "\n... output truncated ...\n" + text[-limit // 2:]


def _reject_constant(value):
    raise ValueError(f"non-finite JSON number {value}")


def _validate_row(row, index):
    def invalid(reason):
        raise SimulatorError(f"invalid simulator response at record {index}: {reason}")

    if not isinstance(row, dict):
        invalid("expected an object")
    if "rewards" not in row or "errors" not in row:
        invalid("missing rewards/errors fields")
    errors = row["errors"]
    if not isinstance(errors, list) or not all(isinstance(e, str) for e in errors):
        invalid("errors must be a list of strings")
    rewards = row["rewards"]
    if rewards is None:
        if not errors:
            invalid("null rewards without an explicit game error")
        return
    if not isinstance(rewards, list) or len(rewards) != 2:
        invalid("rewards must contain exactly two finite numbers")
    for value in rewards:
        if type(value) not in (int, float):
            invalid("rewards must be numeric, not booleans/strings/null")
        try:
            finite = math.isfinite(value)
        except OverflowError:
            finite = False
        if not finite:
            invalid("non-finite or overflowing reward")


def _invoke(args, expected, allow_errors, timeout=None):
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        raise SimulatorError(f"simulator timed out after {timeout}s; no partial results were accepted") from e
    except OSError as e:
        raise SimulatorError(f"cannot start simulator {args[0]}: {e}") from e
    try:
        lines = [json.loads(line, parse_constant=_reject_constant) for line in result.stdout.splitlines()]
    except ValueError as e:
        raise SimulatorError(f"simulator did not return valid finite JSON: {e}\n{_excerpt(result.stderr)}\n{_excerpt(result.stdout)}") from e
    if len(lines) != expected:
        raise SimulatorError(f"expected {expected} simulator results, received {len(lines)}: {_excerpt(result.stderr)}\n{_excerpt(result.stdout)}")
    for index, row in enumerate(lines, start=1):
        _validate_row(row, index)
    errors = [row for row in lines if row["errors"]]
    if result.returncode not in (0, 1):
        raise SimulatorError(f"simulator process failed with code {result.returncode}; no results accepted: {_excerpt(result.stderr)}")
    if result.returncode and not errors:
        raise SimulatorError(f"simulator exited with code {result.returncode} without an explicit game error; no results accepted: {_excerpt(result.stderr)}")
    if errors and not allow_errors:
        raise SimulatorError(f"simulator failure (do not count as a win/loss): {_excerpt(str(errors))}")
    return lines


def replay(job: Job, *, binary=DEFAULT_BINARY, steps=720, step_mode="kaggle", trim_hands=False, config=None, timeout=None, trim_hands_a=False, trim_hands_b=False):
    args = [str(Path(binary).resolve()), "--seed", str(job.seed), "--tape-a", str(Path(job.tape_a).resolve()), "--tape-b", str(Path(job.tape_b).resolve())]
    args += _options(steps, step_mode, trim_hands, config, trim_hands_a, trim_hands_b)
    if job.reverse:
        args.append("--reverse-seats")
    return _invoke(args, 1, False, timeout=timeout)[0]


def replay_many(jobs: Iterable[Job], *, binary=DEFAULT_BINARY, steps=720, step_mode="kaggle", threads=None, trim_hands=False, config=None, allow_errors=False, timeout=None, trim_hands_a=False, trim_hands_b=False):
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
        args += _options(steps, step_mode, trim_hands, config, trim_hands_a, trim_hands_b)
        if threads is not None:
            args += ["--threads", str(threads)]
        return _invoke(args, len(jobs), allow_errors, timeout=timeout)
