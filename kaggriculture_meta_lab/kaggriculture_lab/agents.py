"""Agent loading for closed-loop games.

A spec is one of:
  * "pass" | "random" | "starter"        built-in engine agents
  * a path to a .py exposing agent(obs[,cfg]) or act(obs[,cfg])
  * "tape:<replay.json[.gz]>[#seat]"     open-loop replay of one seat
                                          (default seat = replay winner)
  * "wrap:<base.py>:<wrapper.py>"        base policy wrapped by a variant module

Loaded callables are cached per process (the old runner re-imported every game).
Wrappers let us create experimental variants (e.g. aggressive fertilizer
buying) WITHOUT modifying the proven V7 policy file.
"""
from __future__ import annotations

import gzip
import importlib.util
import json
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

BUILTINS = {"pass", "random", "starter"}
AgentFn = Callable[..., dict]


def _load_py(path: Path) -> Any:
    path = path.resolve()
    mod_dir = str(path.parent)
    if mod_dir not in sys.path:
        sys.path.insert(0, mod_dir)
    spec = importlib.util.spec_from_file_location(
        f"kg_{path.stem}_{abs(hash(str(path)))}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _policy_from_module(mod: Any) -> AgentFn:
    for name in ("agent", "act"):
        fn = getattr(mod, name, None)
        if callable(fn):
            return fn  # type: ignore[return-value]
    raise AttributeError("module exposes neither agent() nor act()")


def _load_replay(path: Path) -> dict:
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def _find_steps(obj: Any) -> list:
    if isinstance(obj, dict):
        steps = obj.get("steps")
        if isinstance(steps, list) and steps:
            return steps
        for v in obj.values():
            r = _find_steps(v)
            if r:
                return r
    return []


def _winner_seat(steps: list) -> int | None:
    try:
        last = steps[-1]
        r = [float(s.get("reward") or 0.0) for s in last]
        if len(r) >= 2 and r[0] != r[1]:
            return 0 if r[0] > r[1] else 1
    except Exception:
        pass
    return None


def _make_tape(path: Path, seat: int | None) -> AgentFn:
    replay = _load_replay(path)
    steps = _find_steps(replay)
    if seat is None:
        seat = _winner_seat(steps) or 0
    tape: list[dict] = []
    for row in steps:
        action = {"farmer": ["PASS"], "hands": [], "market": []}
        if isinstance(row, list) and seat < len(row) and isinstance(row[seat], dict):
            a = row[seat].get("action")
            if isinstance(a, dict):
                action = a
        tape.append(action)

    def _agent(obs: dict, *a: Any, **k: Any) -> dict:
        step = int(obs.get("step", 0) or 0)
        act = tape[min(step, len(tape) - 1)] if tape else {"farmer": ["PASS"], "hands": [], "market": []}
        return {"farmer": list(act.get("farmer", ["PASS"])),
                "hands": [list(h) for h in act.get("hands", [])],
                "market": [list(o) for o in act.get("market", [])]}

    _agent.__tape_info__ = (str(path), seat, len(tape))  # type: ignore[attr-defined]
    return _agent


@lru_cache(maxsize=None)
def resolve(spec: str) -> Any:
    """Resolve a spec to a builtin name (str) or a callable. Cached per process."""
    if spec in BUILTINS:
        return spec
    if spec.startswith("tape:"):
        target = spec[len("tape:"):]
        seat = None
        if "#" in target:
            target, s = target.split("#", 1)
            seat = int(s)
        return _make_tape(_resolve_path(target), seat)
    if spec.startswith("wrap:"):
        # wrap:<base.py>:<wrapper.py>  -> wrapper.wrap(base_policy)
        _, base_ref, wrap_ref = spec.split(":", 2)
        base_mod = _load_py(_resolve_path(base_ref))
        wrap_mod = _load_py(_resolve_path(wrap_ref))
        base_fn = _policy_from_module(base_mod)
        if hasattr(wrap_mod, "wrap"):
            return wrap_mod.wrap(base_fn, base_mod)
        return _policy_from_module(wrap_mod)
    return _policy_from_module(_load_py(_resolve_path(spec)))


def _resolve_path(ref: str) -> Path:
    p = Path(ref)
    if p.is_file():
        return p
    # search a few sensible roots relative to the lab
    roots = [Path.cwd(),
             Path(__file__).resolve().parents[1],
             Path(__file__).resolve().parents[1] / "agents" / "ref",
             Path(__file__).resolve().parents[1] / "agents" / "variants",
             Path(__file__).resolve().parents[2] / "kaggriculture"]
    for root in roots:
        cand = root / ref if not Path(ref).is_absolute() else Path(ref)
        if cand.is_file():
            return cand
    raise FileNotFoundError(f"agent file not found: {ref}")


def label(spec: str) -> str:
    if spec in BUILTINS:
        return spec
    if spec.startswith("tape:"):
        return "tape:" + Path(spec[5:].split("#")[0]).stem
    if spec.startswith("wrap:"):
        return "wrap:" + Path(spec.split(":")[2]).stem
    return Path(spec).stem
