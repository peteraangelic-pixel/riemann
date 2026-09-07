"""Single-game engine wrapper around kaggle-environments.

Runs with debug=False so illegal actions are silent no-ops (exactly like the
competition server), and never raises - a crashed agent returns an error row.
Seeds are deterministic and recorded so every result is reproducible.
"""
from __future__ import annotations

from typing import Any


def play_game(agent0: Any, agent1: Any, seed: int, steps: int = 720,
              record_trace: bool = False) -> dict[str, Any]:
    """Run one game. agent0/agent1 are callables or builtin names (pass/random/starter)."""
    from kaggle_environments import make

    try:
        env = make(
            "kaggriculture",
            configuration={"episodeSteps": int(steps), "seed": int(seed)},
            debug=False,
        )
        env.run([agent0, agent1])
        final = env.steps[-1]
        rewards = [float(getattr(s, "reward", 0.0) or 0.0) for s in final]
        statuses = [getattr(s, "status", "") for s in final]
        out: dict[str, Any] = {
            "seed": int(seed),
            "rewards": rewards,
            "statuses": statuses,
            "resolved_seed": env.info.get("seed"),
            "error": None,
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
