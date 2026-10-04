"""Single-game engine wrapper around kaggle-environments.

Runs with debug=False so illegal actions are silent no-ops (exactly like the
competition server), and never raises - a crashed agent returns an error row.
Seeds are deterministic and recorded so every result is reproducible.
"""
from __future__ import annotations

import math
from typing import Any


def play_game(agent0: Any, agent1: Any, seed: int, steps: int = 720,
              record_trace: bool = False) -> dict[str, Any]:
    """Run one game. agent0/agent1 are callables or builtin names (pass/random/starter)."""
    from kaggle_environments import make

    try:
        try:
            env = make(
                "kaggriculture",
                configuration={"episodeSteps": int(steps), "seed": int(seed)},
                debug=False,
            )
        except Exception as first_error:
            # Recent public kaggle-environments wheels do not always bundle the
            # competition environment. Register our byte-audited reference
            # copy rather than turning every closed-loop game into a false
            # agent failure.
            if "Unknown Environment Specification" not in str(first_error):
                raise
            import importlib.util
            from pathlib import Path
            from kaggle_environments import core, utils
            reference_root = Path(__file__).resolve().parents[1] / "rust_port/reference"
            if not hasattr(utils, "resolve_episode_seed"):
                seed_spec = importlib.util.spec_from_file_location(
                    "_kg_seed_utils", reference_root / "seed_utils.py")
                if seed_spec is None or seed_spec.loader is None:
                    raise RuntimeError("cannot load audited seed helper")
                seed_module = importlib.util.module_from_spec(seed_spec)
                seed_spec.loader.exec_module(seed_module)
                utils.resolve_episode_seed = seed_module.resolve_episode_seed
            reference = reference_root / "kaggriculture_sim.py"
            spec = importlib.util.spec_from_file_location("_kg_reference_sim", reference)
            if spec is None or spec.loader is None:
                raise RuntimeError(f"cannot load reference environment: {reference}")
            sim = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(sim)
            core.register("kaggriculture", {
                "specification": sim.specification, "interpreter": sim.interpreter,
                "renderer": sim.renderer, "html_renderer": sim.html_renderer,
                "agents": sim.agents,
            })
            env = make(
                "kaggriculture",
                configuration={"episodeSteps": int(steps), "seed": int(seed)},
                debug=False,
            )
        failures = []
        seen_failed = set()
        interpreter = env.interpreter

        def audited_interpreter(state, context):
            # Observe incoming status before Kaggriculture can rewrite it to
            # DONE, including an exception on the very last action turn.
            for player, agent_state in enumerate(state):
                status = getattr(agent_state, "status", "")
                if status in {"ERROR", "INVALID", "TIMEOUT"} and player not in seen_failed:
                    failures.append(f"agent {player}: {status} before interpreter")
                    seen_failed.add(player)
            return interpreter(state, context)

        env.interpreter = audited_interpreter
        env.run([agent0, agent1])
        final = env.steps[-1]
        if len(final) != 2:
            raise ValueError("expected exactly two final agent states")
        statuses = [getattr(s, "status", "") for s in final]
        # The game interpreter may overwrite ERROR/TIMEOUT with DONE on its
        # final turn. Check the recorded history, not only terminal statuses.
        for index, frame in enumerate(env.steps):
            for player, state in enumerate(frame):
                status = getattr(state, "status", "")
                if status in {"ERROR", "INVALID", "TIMEOUT"} and player not in seen_failed:
                    failures.append(f"agent {player}: {status} at replay row {index}")
                    seen_failed.add(player)
        if statuses != ["DONE", "DONE"]:
            failures.append(f"unfinished/failed terminal statuses: {statuses}")
        rewards = []
        for player, state in enumerate(final):
            value = getattr(state, "reward", None)
            try:
                if value is None or isinstance(value, bool):
                    raise ValueError("missing/non-numeric reward")
                value = float(value)
                if not math.isfinite(value):
                    raise ValueError("non-finite reward")
            except (TypeError, ValueError, OverflowError):
                failures.append(f"agent {player}: invalid terminal reward")
                value = 0.0  # Compatibility placeholder, NEVER a scored game.
            rewards.append(value)
        out: dict[str, Any] = {
            "seed": int(seed),
            "rewards": rewards,
            "statuses": statuses,
            "resolved_seed": env.info.get("seed"),
            "error": "; ".join(failures) if failures else None,
        }
        if record_trace:
            # full replay for open-loop reuse / x-ray
            out["replay"] = env.toJSON()
        return out
    except Exception as exc:  # never kill the batch
        return {
            "seed": int(seed), "rewards": [0.0, 0.0], "statuses": ["ERROR", "ERROR"],
            "resolved_seed": None, "error": f"{type(exc).__name__}: {exc}",
        }
