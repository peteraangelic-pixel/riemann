"""Validated Rust+Rayon backend for static tape games.

Python remains the controller/statistics layer.  Jobs whose two policies can be
materialized as tapes are batched through ``kg_sim``; reactive policies fall
back to the audited Python engine.  A Rust/protocol failure is never silently
scored and, once a binary is selected, never triggers an expensive surprise
rerun in Python.
"""
from __future__ import annotations

import gzip
import json
import os
import sys
import tempfile
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
_RUST_DIR = _ROOT / "rust_port"
_DEFAULT_BINARY = _RUST_DIR / "target" / "release" / "kg_sim"
_EMPTY = {"farmer": ["PASS"], "hands": [], "market": []}


@dataclass(frozen=True)
class TapeSource:
    actions: list
    trim_hands: bool


def _row(job: tuple, self_r: float, opp_r: float, error: str | None) -> dict[str, Any]:
    seed, _candidate, opponent, seat, _steps, tag = job
    outcome = "error" if error else "win" if self_r > opp_r else "loss" if self_r < opp_r else "tie"
    return {"tag": tag, "seed": seed, "seat": seat, "opponent": opponent,
            "self_reward": float(self_r), "opp_reward": float(opp_r),
            "margin": float(self_r - opp_r), "outcome": outcome, "error": error}


def rust_binary() -> Path | None:
    """Return the release binary only when it exists and is executable."""
    return _DEFAULT_BINARY if _DEFAULT_BINARY.exists() and os.access(_DEFAULT_BINARY, os.X_OK) else None


def _load_module_source(path: Path) -> TapeSource | None:
    """Compile only audited static templates without importing agent code."""
    try:
        from rust_port.tools.agent_tape import UnsupportedAgent, compile_file
        compiled = compile_file(path.resolve())
        return TapeSource(json.loads(compiled.payload), compiled.trim_hands)
    except (OSError, UnsupportedAgent, ValueError, json.JSONDecodeError):
        return None


def _read_replay(path: Path) -> dict:
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def _source(spec: str) -> TapeSource | None:
    """Resolve a static agent module or a raw ``tape:replay[#seat]`` source.

    Agent modules use the wrapper's hand trimming. Raw historical replay actions
    must stay untrimmed. A selected replay seat is duplicated so it represents
    the same open-loop policy in either physical seat.
    """
    from .agents import _find_steps, _resolve_path, _winner_seat

    if not isinstance(spec, str) or spec in {"pass", "random", "starter"} or spec.startswith("wrap:"):
        return None
    if spec.startswith("tape:"):
        target = spec[5:]
        seat = None
        if "#" in target:
            target, raw_seat = target.rsplit("#", 1)
            seat = int(raw_seat)
        replay = _read_replay(_resolve_path(target))
        steps = _find_steps(replay)
        if not steps:
            raise ValueError(f"replay has no steps: {target}")
        if seat is None:
            seat = _winner_seat(steps)
            if seat is None:
                seat = 0
        if seat not in (0, 1):
            raise ValueError("replay seat must be 0 or 1")
        # Replay row zero is initialization; action N is in row N+1.
        actions = []
        for row in steps[1:]:
            action = row[seat].get("action") if isinstance(row, list) and len(row) > seat else None
            actions.append(action if isinstance(action, dict) else _EMPTY)
        if not actions:
            actions = [_EMPTY]
        return TapeSource([actions, actions], trim_hands=False)

    path = _resolve_path(spec)
    if path.suffix != ".py":
        return None
    return _load_module_source(path)


def _is_tape_spec(spec: Any) -> bool:
    """Compatibility predicate used by generators/tests."""
    if not isinstance(spec, str):
        return False
    try:
        return _source(spec) is not None
    except (FileNotFoundError, ValueError, OSError, json.JSONDecodeError):
        return False


def _python_rows(jobs: list[tuple], indexes: list[int], workers: int,
                 progress_every: int) -> dict[int, dict[str, Any]]:
    if not indexes:
        return {}
    from . import tournament
    selected = [jobs[index] for index in indexes]
    return dict(zip(indexes, tournament.run(selected, workers, progress_every=progress_every)))


def run_rust(jobs: list[tuple], workers: int, *, binary: Path | None = None,
             progress_every: int = 200) -> list[dict[str, Any]]:
    """Run every compatible job in Rust and incompatible job in audited Python.

    Rust jobs are partitioned by horizon and per-input hand semantics. This is
    required for candidate-vs-raw-replay evaluation (trim A, do not trim B).
    """
    if not jobs:
        return []
    tools_dir = _RUST_DIR / "tools"
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    from rust_client import Job as RustJob, replay_many

    executable = binary or rust_binary()
    if executable is None:
        raise RuntimeError("kg_sim binary not found; build rust_port --release")

    sources: dict[str, TapeSource | None] = {}
    rust_groups: dict[tuple[int, bool, bool], list[int]] = defaultdict(list)
    python_indexes: list[int] = []
    for index, job in enumerate(jobs):
        _seed, candidate, opponent, _seat, steps, _tag = job
        candidate_source = sources.setdefault(candidate, _source(candidate))
        opponent_source = sources.setdefault(opponent, _source(opponent))
        if candidate_source is None or opponent_source is None:
            python_indexes.append(index)
        else:
            rust_groups[(int(steps), candidate_source.trim_hands,
                         opponent_source.trim_hands)].append(index)

    rows = _python_rows(jobs, python_indexes, workers, progress_every)
    with tempfile.TemporaryDirectory(prefix="kg-rust-") as directory:
        export_dir = Path(directory)
        exported: dict[str, Path] = {}

        def tape_path(spec: str) -> Path:
            if spec not in exported:
                path = export_dir / f"tape-{len(exported)}.json"
                path.write_text(json.dumps(sources[spec].actions), encoding="utf-8")
                exported[spec] = path
            return exported[spec]

        for (steps, trim_a, trim_b), indexes in rust_groups.items():
            rust_jobs = []
            for index in indexes:
                seed, candidate, opponent, seat, _steps, _tag = jobs[index]
                rust_jobs.append(RustJob(int(seed), tape_path(candidate),
                                         tape_path(opponent), reverse=(seat == 1)))
            started = time.perf_counter()
            results = replay_many(
                rust_jobs, binary=executable, steps=steps, step_mode="kaggle",
                threads=workers, trim_hands_a=trim_a, trim_hands_b=trim_b,
                allow_errors=True,
            )
            elapsed = time.perf_counter() - started
            print(f"  [rust] {len(indexes)} games in {elapsed:.3f}s "
                  f"({len(indexes) / max(elapsed, 1e-9):.1f}/s; "
                  f"trim A/B={trim_a}/{trim_b})", flush=True)
            for index, result in zip(indexes, results):
                errors = result.get("errors")
                rewards = result.get("rewards")
                if errors or rewards is None:
                    message = "; ".join(map(str, errors or [])) or "Rust game error"
                    rows[index] = _row(jobs[index], 0.0, 0.0, message)
                else:
                    rows[index] = _row(jobs[index], rewards[0], rewards[1], None)

    return [rows[index] for index in range(len(jobs))]


def run_auto(jobs: list[tuple], workers: int, *, progress_every: int = 200,
             prefer_rust: bool = True) -> list[dict[str, Any]]:
    """Use Rust when installed; otherwise use Python. Rust failures are fatal.

    We deliberately do not rerun a failed Rust batch in Python: that could hide
    a parity/protocol defect and unexpectedly consume hundreds of runner-minutes.
    """
    executable = rust_binary() if prefer_rust else None
    if executable is None:
        from . import tournament
        return tournament.run(jobs, workers, progress_every=progress_every)
    return run_rust(jobs, workers, binary=executable, progress_every=progress_every)
