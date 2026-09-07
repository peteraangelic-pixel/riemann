"""Rust+Rayon fast backend for tape-vs-tape games, with Python fallback.

The sweep funnel plays thousands of games. The CPython interpreter
(`engine.play_game` via `tournament.run`) is the bottleneck (~0.3 game/s/core).
The validated Rust simulator (`rust_port/target/release/kg_sim`, see
`rust_port/VALIDATION.md`: byte-identical rewards, ~80x in batch mode) can play
**tape** agents far faster.

This module keeps a drop-in signature compatible with `tournament.run(jobs, ...)`:
  * tape-vs-tape jobs  -> one batched Rust call (tapes exported once, Rayon);
  * anything reactive   -> falls back to the Python engine automatically;
  * no Rust binary      -> the whole batch falls back to Python.

A "job" is the tuple produced by `tournament.build_jobs`:
    (seed, cand_spec, opp_spec, seat, steps, tag)

Only plain tape-agent files count as Rust-able: a `.py` that exposes a
two-seat `ACTIONS` structure (our champion and the three frozen controls all
do). Builtins ("pass"), replay specs ("tape:...","wrap:...") and reactive
`def agent(obs,cfg)` policies go to Python.
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
_RUST_DIR = _ROOT / "rust_port"
_DEFAULT_BINARY = _RUST_DIR / "target" / "release" / "kg_sim"

# outcome buckets identical to tournament._play
_OUTCOME = lambda s, o: "win" if s > o else "loss" if s < o else "tie"


def _row(job: tuple, self_r: float, opp_r: float, error: str | None) -> dict[str, Any]:
    seed, _cand, opp_spec, seat, _steps, tag = job
    return {"tag": tag, "seed": seed, "seat": seat, "opponent": opp_spec,
            "self_reward": float(self_r), "opp_reward": float(opp_r),
            "margin": float(self_r - opp_r),
            "outcome": "error" if error else _OUTCOME(self_r, opp_r),
            "error": error}


def rust_binary() -> Path | None:
    """Path to a usable kg_sim binary, or None (-> Python fallback)."""
    b = _DEFAULT_BINARY
    return b if b.exists() and __import__("os").access(b, __import__("os").X_OK) else None


def _load_actions(path: Path) -> list | None:
    """Import a tape-agent .py and return its two-seat ACTIONS, or None.

    Executes the module (the champion applies its BUY_WHEAT/SELL_WHEAT opening
    overrides at import time), then returns ACTIONS if it is a 2-seat list of
    per-step action dicts. Reactive modules / anything odd -> None.
    """
    try:
        import os as _os
        mod_dir = str(path.parent.resolve())
        if mod_dir not in sys.path:
            sys.path.insert(0, mod_dir)
        spec = importlib.util.spec_from_file_location(
            f"kgtape_{path.stem}_{abs(hash(str(path.resolve())))}", path)
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        actions = getattr(mod, "ACTIONS", None)
        if not isinstance(actions, list) or len(actions) != 2:
            return None
        for seat in actions:
            if not isinstance(seat, list) or not seat:
                return None
            if not all(isinstance(step, dict) for step in seat):
                return None
        return actions
    except Exception:
        return None


def _is_tape_spec(spec: Any) -> bool:
    """A Rust-able candidate/opponent is a path to a tape .py with ACTIONS."""
    if not isinstance(spec, str):
        return False
    if spec in ("pass", "random", "starter"):
        return False
    if spec.startswith(("tape:", "wrap:")):
        return False
    p = Path(spec)
    if not p.exists() or p.suffix != ".py":
        return False
    return _load_actions(p) is not None


def run_rust(jobs: list[tuple], workers: int, *, binary: Path | None = None,
             trim_hands: bool = True, progress_every: int = 200) -> list[dict[str, Any]]:
    """Play jobs with the Rust binary; raise RuntimeError if Rust unavailable.

    Callers should normally use `run_auto`, which falls back to Python. This
    function is split out so a missing/failed binary is explicitly detectable.
    """
    import json
    import time

    # rust_port/tools is not a package on sys.path; make rust_client importable.
    tools_dir = _RUST_DIR / "tools"
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    from rust_client import Job as _Job, replay_many as _replay_many  # noqa: E402

    binpath = binary or rust_binary()
    if binpath is None:
        raise RuntimeError("kg_sim binary not found (build rust_port in release)")

    # Partition: only jobs where BOTH agents are tape files go to Rust.
    rust_idx, py_idx = [], []
    for i, j in enumerate(jobs):
        _seed, cand, opp, _seat, _steps, _tag = j
        (rust_idx if (_is_tape_spec(cand) and _is_tape_spec(opp)) else py_idx).append(i)

    rows: dict[int, dict[str, Any]] = {}

    if py_idx:
        from kaggriculture_lab import tournament
        py_rows = tournament.run([jobs[i] for i in py_idx], workers,
                                 progress_every=progress_every)
        for i, r in zip(py_idx, py_rows):
            rows[i] = r

    if rust_idx:
        # Export each unique tape file once; the client caches parsed tapes too.
        export_dir = Path(tempfile.mkdtemp(prefix="kg-rust-"))
        spec_to_json: dict[str, Path] = {}

        def tape_json(spec: str) -> Path:
            if spec not in spec_to_json:
                actions = _load_actions(Path(spec))
                out = export_dir / (Path(spec).stem + ".json")
                out.write_text(json.dumps(actions), encoding="utf-8")
                spec_to_json[spec] = out
            return spec_to_json[spec]

        rjobs = []
        meta = []  # (job_index, cand_reward_index)
        for i in rust_idx:
            seed, cand, opp, seat, steps, _tag = jobs[i]
            cj, oj = tape_json(cand), tape_json(opp)
            # seat==0: cand plays physical seat 0 -> tape A = cand, normal.
            # seat==1: cand plays physical seat 1 -> reverse-seats so the
            # binary's tape A (cand) lands on seat 1; rewards stay in (cand,opp)
            # input order.
            reverse = (seat == 1)
            rjobs.append(_Job(int(seed), cj, oj, reverse=reverse))
            meta.append(i)

        started = time.perf_counter()
        results = _replay_many(rjobs, binary=binpath, steps=int(jobs[rust_idx[0]][4]),
                               step_mode="kaggle", threads=workers,
                               trim_hands=trim_hands, allow_errors=True)
        el = time.perf_counter() - started
        print(f"  [rust] {len(rust_idx)} tape games in {el:.1f}s "
              f"({len(rust_idx)/max(el,1e-9):.1f}/s, {workers} threads)",
              flush=True)

        for i, res in zip(meta, results):
            job = jobs[i]
            errs = res.get("errors")
            rewards = res.get("rewards")
            if errs or rewards is None:
                rows[i] = _row(job, 0.0, 0.0, "; ".join(map(str, errs)) or "rust error")
            else:
                # rewards are in input order (A=cand tape, B=opp tape)
                rows[i] = _row(job, rewards[0], rewards[1], None)

    return [rows[i] for i in range(len(jobs))]


def run_auto(jobs: list[tuple], workers: int, *, progress_every: int = 200,
             prefer_rust: bool = True) -> list[dict[str, Any]]:
    """Play jobs: Rust batch if available and requested, else Python engine.

    prefer_rust=False forces the pure-Python path (used for parity checks).
    """
    if prefer_rust and rust_binary() is not None:
        try:
            return run_rust(jobs, workers, progress_every=progress_every)
        except Exception as exc:  # any Rust failure -> never lose the batch
            print(f"  [rust] backend failed ({type(exc).__name__}: {exc}); "
                  f"falling back to Python engine", flush=True)
    from kaggriculture_lab import tournament
    return tournament.run(jobs, workers, progress_every=progress_every)
