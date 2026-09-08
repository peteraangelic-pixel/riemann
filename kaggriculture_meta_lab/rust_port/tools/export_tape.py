#!/usr/bin/env python3
"""Safely export the supplied example's ACTIONS to plain [seat][step] JSON.

No Python code from the agent is executed. Supports a literal ACTIONS array or
json.loads(zlib.decompress(base64.b85decode(<literal>))) and the supplied
BUY_WHEAT / SELL_WHEAT overrides. Other mutations are rejected, not guessed.
The live hands slice belongs to replay options (--trim-hands), not static JSON.
Input extension (.py/.txt/.json) is irrelevant.
"""
from __future__ import annotations

import argparse
import ast
import base64
import copy
import json
from pathlib import Path
import zlib

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AGENT = ROOT / "reference/agent_v9_b21_s16.example.py"
MAX_DECODED_BYTES = 64 * 1024 * 1024


def validate_tape(tape):
    if not isinstance(tape, list) or len(tape) != 2:
        raise ValueError("expected [seat0_actions, seat1_actions]")
    if any(not isinstance(seat, list) or not seat for seat in tape):
        raise ValueError("both seats must have a nonempty action list")
    return tape



def extract_single_stream(path):
    """Explicit JSON-only [step] -> [seat][step] convenience conversion.

    Keep the native simulator's two-seat contract strict. In particular,
    malformed arrays must not silently become two PASS agents.
    """
    actions = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(actions, list) or not actions or not all(isinstance(a, dict) for a in actions):
        raise ValueError("single stream must be a nonempty JSON array of action objects")
    return [copy.deepcopy(actions), copy.deepcopy(actions)]


def _unwrap(node, function):
    if not isinstance(node, ast.Call) or ast.unparse(node.func) != function or len(node.args) != 1 or node.keywords:
        raise ValueError(f"expected {function}(<one literal argument>)")
    return node.args[0]


def extract(path=DEFAULT_AGENT):
    source = Path(path).read_text(encoding="utf-8-sig")
    try:
        return validate_tape(json.loads(source))
    except json.JSONDecodeError:
        pass
    tree = ast.parse(source, filename=str(path))
    assignments = {
        node.targets[0].id: node.value for node in tree.body
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
    }
    if "ACTIONS" not in assignments:
        raise ValueError("no top-level ACTIONS assignment")
    node = assignments["ACTIONS"]
    if isinstance(node, ast.List):
        tape = ast.literal_eval(node)
    else:
        node = _unwrap(node, "json.loads")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "decode":
            if node.keywords or (node.args and (len(node.args) != 1 or ast.literal_eval(node.args[0]) not in ("utf-8", "utf8"))):
                raise ValueError("only UTF-8 decode is supported")
            node = node.func.value
        for function in ("zlib.decompress", "base64.b85decode"):
            node = _unwrap(node, function)
        encoded = ast.literal_eval(node)
        if not isinstance(encoded, (str, bytes)):
            raise ValueError("base85 payload must be a literal string")
        decoder = zlib.decompressobj()
        decoded = decoder.decompress(base64.b85decode(encoded), MAX_DECODED_BYTES + 1)
        if len(decoded) > MAX_DECODED_BYTES or not decoder.eof:
            raise ValueError("decoded tape is too large or truncated")
        tape = json.loads(decoded)
    validate_tape(tape)

    expected_loop = ast.parse('''for _actions in ACTIONS:
 _actions[0]["market"]=[["BUY_PRODUCT","WHEAT",BUY_WHEAT]]
 _actions[1]["market"][0]=["SELL","WHEAT",SELL_WHEAT]
''').body[0]
    loops = [node for node in tree.body if isinstance(node, ast.For)]
    for node in loops:
        if ast.dump(node) != ast.dump(expected_loop):
            raise ValueError("unsupported top-level mutation; export actual actions on the Python side")
        buy = ast.literal_eval(assignments["BUY_WHEAT"])
        sell = ast.literal_eval(assignments["SELL_WHEAT"])
        if type(buy) is not int or type(sell) is not int:
            raise ValueError("BUY_WHEAT and SELL_WHEAT must be integer literals")
        for seat in tape:
            seat[0]["market"] = [["BUY_PRODUCT", "WHEAT", buy]]
            seat[1]["market"][0] = ["SELL", "WHEAT", sell]

    # Permit definitions/imports/data assignments, not hidden executable mutations.
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.For)):
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in {"ACTIONS", "BUY_WHEAT", "SELL_WHEAT", "act"}:
                continue
        raise ValueError(f"unsupported top-level statement at line {node.lineno}; no agent code was executed")
    return tape


def write_tape(path, tape):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(validate_tape(tape), separators=(",", ":")) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, nargs="?", default=DEFAULT_AGENT)
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--single-stream", action="store_true", help="explicitly mirror a JSON [step] action list into both seats")
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve():
        parser.error("output must not overwrite the input source")
    try:
        tape = extract_single_stream(args.source) if args.single_stream else extract(args.source)
        write_tape(args.output, tape)
    except (OSError, ValueError, SyntaxError) as error:
        parser.error(str(error))
    print(args.output)


if __name__ == "__main__":
    main()
