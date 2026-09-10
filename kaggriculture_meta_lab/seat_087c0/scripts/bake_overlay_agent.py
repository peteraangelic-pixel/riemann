#!/usr/bin/env python3
"""Bake a submission-style agent: base tape + inlined overlay.

Usage: bake_overlay_agent.py base_agent.py overlay.py out.py --name NAME --doc DOC
Copies _BLOB/_ACTIONS lines from the base tape agent verbatim, inlines the
overlay module source (must be self-contained, defines overlay(action,obs,cfg)),
and emits agent() = playback + hand trim + overlay + PASS fallback.
Used for slow-harness parity checks and for promotion artifacts.
"""
import sys
from pathlib import Path


def main():
    args = sys.argv[1:]
    base_p, ov_p, out_p = args[0], args[1], args[2]
    name, doc = "baked", ""
    i = 3
    while i < len(args):
        if args[i] == "--name":
            name = args[i + 1]; i += 2
        elif args[i] == "--doc":
            doc = args[i + 1]; i += 2
        else:
            i += 1
    base = Path(base_p).read_text()
    blob_line = next(l for l in base.splitlines() if l.startswith("_BLOB = ") or l.startswith("_BLOB="))
    act_line = next(l for l in base.splitlines() if l.startswith("_ACTIONS = ") or l.startswith("_ACTIONS=") or l.startswith("_ACTIONS=json"))
    decode_imports = "import base64, copy, json, zlib"
    if "bz2" in act_line and "base64" in act_line:
        decode_imports = "import base64, bz2, copy, json"
    ov_src = Path(ov_p).read_text()
    body = f'''"""{name}: {doc}

Baked tape+overlay agent (base {Path(base_p).name} + {Path(ov_p).name}).
"""
{decode_imports}
{blob_line}
{act_line.replace("_ACTIONS", "_ACTIONS", 1)}

# --- inlined overlay: {Path(ov_p).name} ---
{ov_src}

def _safe_pass(observation):
    try:
        p = int(observation.get("player", 0))
        hands = ((observation.get("farms") or [])[p] or {{}}).get("hands") or []
        n = len(hands)
    except Exception:
        n = 0
    return {{"farmer": ["PASS"], "hands": [["PASS"]] * n, "market": []}}

def agent(observation, configuration=None):
    try:
        p = int(observation.get("player", 0))
        stream = _ACTIONS if isinstance(_ACTIONS[0], dict) else _ACTIONS[p]
        step = min(int(observation.get("step", 0)), len(stream) - 1)
        action = copy.deepcopy(stream[step])
        hands = ((observation.get("farms") or [])[p] or {{}}).get("hands") or []
        action["hands"] = action.get("hands", [])[:len(hands)]
        obs = {{"player": p, "step": int(observation.get("step", 0)),
                "farms": observation.get("farms"), "private": observation.get("private"),
                "market": observation.get("market"), "town": observation.get("town")}}
        cfg = {{}}
        try:
            if hasattr(configuration, "keys"):
                for k in list(configuration.keys()):
                    try:
                        cfg[k] = configuration[k]
                    except Exception:
                        pass
            elif configuration is not None and hasattr(configuration, "__dict__"):
                cfg = dict(vars(configuration))
        except Exception:
            pass
        return overlay(action, obs, cfg)
    except Exception:
        return _safe_pass(observation)

def act(observation, configuration=None):
    return agent(observation, configuration)
'''
    Path(out_p).write_text(body)
    print(f"baked {out_p}")


if __name__ == "__main__":
    main()
