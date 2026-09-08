"""Safe tape batching boundary for the Python Meta-Lab.

Jobs keep the existing six-field LAB tuple (seed, candidate, opponent, seat,
episodeSteps, tag). Only proven static templates go to Rust. Python policies
are NEVER frozen merely because they expose ACTIONS. No tournament statistics
or reactive policies are implemented here.
"""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
import hashlib
import math
import operator
import os
from pathlib import Path
import tempfile
import time

from .agent_tape import MAX_SOURCE_BYTES, UnsupportedAgent, compile_source
from . import rust_client


class BackendError(RuntimeError):
    """Preparation/execution/protocol error; must not become a game result."""


@dataclass
class BatchReport:
    rows: list[dict]
    metrics: dict


def rust_binary(binary=None):
    path = Path(binary) if binary is not None else rust_client.DEFAULT_BINARY
    return path.resolve() if path.is_file() and os.access(path, os.X_OK) else None


def _int(value, label):
    try:
        if isinstance(value, bool):
            raise TypeError
        return operator.index(value)
    except TypeError as error:
        raise BackendError(f"{label} must be an integer") from error


def _jobs(jobs):
    normalized = []
    for index, job in enumerate(jobs):
        if not isinstance(job, (tuple, list)) or len(job) != 6:
            raise BackendError(f"job {index}: expected six LAB fields")
        seed, candidate, opponent, seat, steps, tag = job
        seed, seat, steps = _int(seed, "seed"), _int(seat, "seat"), _int(steps, "steps")
        if not -(2**63) <= seed < 2**63 or seat not in (0, 1) or not 1 <= steps <= 2**31 - 1:
            raise BackendError(f"job {index}: seed/seat/steps outside supported range")
        if not isinstance(candidate, str) or not isinstance(opponent, str) or not candidate or not opponent:
            raise BackendError(f"job {index}: candidate/opponent must be nonempty specs")
        normalized.append((seed, candidate, opponent, seat, steps, tag))
    return normalized


def _row(job, own, other, error=None):
    seed, _candidate, opponent, seat, _steps, tag = job
    return {"tag": tag, "seed": seed, "seat": seat, "opponent": opponent,
            "self_reward": float(own), "opp_reward": float(other),
            "margin": float(own - other),
            "outcome": "error" if error else "win" if own > other else "loss" if own < other else "tie",
            "error": error}


def _resolve(spec, resolver):
    if spec in ("pass", "random", "starter") or spec.startswith(("tape:", "wrap:")):
        raise UnsupportedAgent("builtin/replay/wrapper requires the Python runner")
    path = Path(resolver(spec)) if resolver is not None else Path(spec).expanduser()
    if path.suffix.lower() != ".py":
        raise UnsupportedAgent("only audited Python tape templates are auto-compiled")
    return path.resolve(strict=True)


def _python_rows(jobs, indices, runner, workers, progress_every):
    if runner is None:
        try:
            from kaggriculture_lab import tournament
            runner = tournament.run
        except ImportError as error:
            raise BackendError("Python fallback requires the LAB tournament runner or python_runner callback") from error
    # tournament.run returns as_completed order. Unique opaque correlation tags
    # also disambiguate duplicate user tags/jobs; tags never reach the agent.
    mapping = {f"__kg_backend_job_{index}": index for index in indices}
    tagged = [(*jobs[index][:5], tag) for tag, index in mapping.items()]
    returned = runner(tagged, workers, progress_every=progress_every)
    if not isinstance(returned, list) or len(returned) != len(indices):
        raise BackendError("Python runner returned an incomplete batch")
    result = {}
    for row in returned:
        required = {"tag", "seed", "seat", "opponent", "self_reward", "opp_reward", "margin", "outcome", "error"}
        if not isinstance(row, dict) or not required.issubset(row) or not isinstance(row.get("tag"), str) or row["tag"] not in mapping:
            raise BackendError("Python runner returned an unknown job tag")
        index = mapping[row["tag"]]
        if index in result:
            raise BackendError("Python runner returned a duplicate job tag")
        job = jobs[index]
        if row.get("seed") != job[0] or row.get("seat") != job[3] or row.get("opponent") != job[2]:
            raise BackendError("Python runner returned mismatched job identity")
        error = row.get("error")
        if error is not None:
            if not isinstance(error, str) or not error or row.get("outcome") != "error":
                raise BackendError("Python runner returned a malformed error row")
            result[index] = _row(job, 0, 0, error)
            continue
        own, other, margin = row.get("self_reward"), row.get("opp_reward"), row.get("margin")
        try:
            valid = all(type(v) in (int, float) and math.isfinite(v) for v in (own, other, margin))
        except OverflowError:
            valid = False
        if not valid:
            raise BackendError("Python runner returned non-finite/missing rewards")
        expected = _row(job, own, other)
        if row.get("outcome") != expected["outcome"] or margin != expected["margin"]:
            raise BackendError("Python runner returned inconsistent outcome/margin")
        result[index] = {**row, **expected}
    return result


def run_report(jobs, workers, *, mode="auto", binary=None, python_runner=None,
               resolver=None, timeout=None, progress_every=200):
    """Execute once, return ordered rows plus honest end-to-end metrics.

    `auto` falls back ONLY for unavailable Rust or unproven policy templates.
    A failed Rust process/protocol is raised, never silently rerun in Python.
    `rust` is strict: all jobs must be supported before anything is executed.
    """
    started = time.perf_counter()
    jobs = _jobs(jobs)
    workers = _int(workers, "workers")
    if workers < 1 or mode not in ("auto", "rust", "python"):
        raise BackendError("invalid workers/mode")
    metrics = {"jobs": len(jobs), "source_reads": 0, "source_compilations": 0,
               "rust_jobs": 0, "python_jobs": 0, "unique_rust_games": 0,
               "rust_calls": 0, "exported_tapes": 0, "python_reasons": {}}
    if not jobs:
        metrics["total_seconds"] = time.perf_counter() - started
        return BatchReport([], metrics)
    binary = None if mode == "python" else rust_binary(binary)
    if mode == "rust" and binary is None:
        raise BackendError("strict Rust mode requires a usable kg_sim binary")
    by_spec, by_path, by_content = {}, {}, {}

    def source(spec):
        if spec in by_spec:
            return by_spec[spec]
        try:
            path = _resolve(spec, resolver)
            if path not in by_path:
                with path.open("rb") as file:
                    data = file.read(MAX_SOURCE_BYTES + 1)
                metrics["source_reads"] += 1
                digest = hashlib.sha256(data).hexdigest()
                if digest not in by_content:
                    metrics["source_compilations"] += 1
                    try:
                        by_content[digest] = (compile_source(data), None)
                    except UnsupportedAgent as error:
                        by_content[digest] = (None, str(error))
                by_path[path] = by_content[digest]
            compiled, reason = by_path[path]
        except (OSError, UnsupportedAgent) as error:
            compiled, reason = None, str(error)
        by_spec[spec] = compiled
        if reason:
            metrics["python_reasons"][spec] = reason
        return compiled

    groups = OrderedDict()
    python_indices = []
    for index, job in enumerate(jobs):
        if binary is None:
            python_indices.append(index)
            continue
        a, b = source(job[1]), source(job[2])
        if a is None or b is None:
            python_indices.append(index)
            continue
        metrics["rust_jobs"] += 1
        bucket = (job[4], a.trim_hands, b.trim_hands)
        # Pure deterministic snapshots allow safe within-batch game reuse.
        # Python/reactive jobs are never deduplicated or replayed automatically.
        key = (a.fingerprint, b.fingerprint, job[0], job[3])
        unique = groups.setdefault(bucket, OrderedDict())
        if key not in unique:
            unique[key] = {"a": a, "b": b, "indices": []}
        unique[key]["indices"].append(index)
    if mode == "rust" and python_indices:
        raise BackendError("strict Rust mode encountered an unproven/reactive/missing agent")
    metrics["python_jobs"] = len(python_indices)
    metrics["preparation_seconds"] = time.perf_counter() - started
    rows = {}
    native_started = time.perf_counter()
    if groups:
        with tempfile.TemporaryDirectory(prefix="kg-verified-tapes-") as directory:
            exported = {}

            def export(compiled):
                digest = hashlib.sha256(compiled.payload).hexdigest()
                if digest not in exported:
                    path = Path(directory) / f"{digest}.json"
                    path.write_bytes(compiled.payload)
                    exported[digest] = path
                return exported[digest]

            for (steps, trim_a, trim_b), unique in groups.items():
                entries = list(unique.values())
                native_jobs = []
                for entry in entries:
                    job = jobs[entry["indices"][0]]
                    native_jobs.append(rust_client.Job(job[0], export(entry["a"]), export(entry["b"]), job[3] == 1))
                metrics["rust_calls"] += 1
                metrics["unique_rust_games"] += len(native_jobs)
                try:
                    results = rust_client.replay_many(native_jobs, binary=binary, steps=steps, threads=workers,
                                                      trim_hands_a=trim_a, trim_hands_b=trim_b,
                                                      timeout=timeout, allow_errors=True)
                    if not isinstance(results, list) or len(results) != len(entries):
                        raise BackendError("Rust runner returned an incomplete batch")
                    for number, (entry, result) in enumerate(zip(entries, results), start=1):
                        rust_client._validate_row(result, number)
                        error = ("; ".join(result["errors"]) or "Rust reported a game error") if result["errors"] else None
                        own, other = result["rewards"] if error is None else (0, 0)
                        for index in entry["indices"]:
                            rows[index] = _row(jobs[index], own, other, error)
                except BackendError:
                    raise
                except Exception as error:
                    raise BackendError("Rust execution/protocol failed; no automatic Python rerun") from error
            metrics["exported_tapes"] = len(exported)
    metrics["native_seconds"] = time.perf_counter() - native_started
    python_started = time.perf_counter()
    if python_indices:
        rows.update(_python_rows(jobs, python_indices, python_runner, workers, progress_every))
    metrics["python_seconds"] = time.perf_counter() - python_started
    metrics["reused_rust_results"] = metrics["rust_jobs"] - metrics["unique_rust_games"]
    metrics["total_seconds"] = time.perf_counter() - started
    if progress_every:
        print(f"[backend] {len(jobs)} jobs in {metrics['total_seconds']:.3f}s total; "
              f"Rust {metrics['rust_jobs']} ({metrics['unique_rust_games']} unique), "
              f"Python {metrics['python_jobs']}; source reads {metrics['source_reads']}", flush=True)
    return BatchReport([rows[i] for i in range(len(jobs))], metrics)


def run_auto(jobs, workers, *, progress_every=200, prefer_rust=True, **kwargs):
    return run_report(jobs, workers, mode="auto" if prefer_rust else "python", progress_every=progress_every, **kwargs).rows


def run_rust(jobs, workers, *, progress_every=200, **kwargs):
    return run_report(jobs, workers, mode="rust", progress_every=progress_every, **kwargs).rows
