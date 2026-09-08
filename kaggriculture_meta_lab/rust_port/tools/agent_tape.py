"""Conservative, non-executing compiler for known static tape-agent templates.

Having ACTIONS is NOT proof that a policy is static. We require an audited
function-AST template and evaluate only a bounded, pure data-expression subset.
Anything else belongs in the Python runner. No import/exec/eval of agent code.
"""
from __future__ import annotations

import ast
import base64
import copy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import zlib

MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_DECODED_BYTES = 64 * 1024 * 1024

RAW_AGENT = '''def agent(observation, configuration):
    p = int(observation.get("player", 0))
    step = min(int(observation.get("step", 0)), len(ACTIONS[p]) - 1)
    return copy.deepcopy(ACTIONS[p][step])
'''
CLIPPED_AGENT = '''def agent(observation, configuration):
    p = int(observation.get("player", 0))
    step = min(int(observation.get("step", 0)), len(ACTIONS[p]) - 1)
    action = copy.deepcopy(ACTIONS[p][step])
    action["hands"] = action.get("hands", [])[:len(observation["farms"][p]["hands"])]
    return action
'''


def _canonical(node):
    if isinstance(node, ast.AST):
        # Python 3.12 adds an empty type_params field. Nonempty generic type
        # parameters are unsupported; never ignore executable annotations.
        return [type(node).__name__, {k: _canonical(v) for k, v in ast.iter_fields(node)
                                     if not (k == "type_params" and not v)}]
    if isinstance(node, list):
        return [_canonical(v) for v in node]
    return node


def ast_fingerprint(node):
    return hashlib.sha256(json.dumps(_canonical(node), sort_keys=True, separators=(",", ":")).encode()).hexdigest()


# Audited against 99c364e55fc88bd03954ab93e7b742fedac45101 and the frozen B21
# reference. Fingerprints cover the complete FunctionDef, not just its name.
_B21 = "efb00ea756e0120d48f44ff77f14cc3c1198d23017072cc867fe88fe15e91137"
_STRUCTURAL = "6f3cbbb33f3ae558f136797d710743d9355f16ba7eddd54f61462d7b7ac3d7ef"
_V7 = "8b61077650aa632fc46a0fcbdaf72975353819d63c548e7d1330528a0d4e3633"
_V8 = "32eacec672470fcad4230de319d19fbf0ef1b9d1197b655a6db03bf97fe705e6"
_DELEGATE = "b05e64ed460656a07bd8e9eafe72deec956d8496f12cfa93619a82a90b17fbda"
_DECODER = "1a6d010aa7acd22a6441b925b8cd9ccb11fbd530e9c63038b98a78abd3520444"
_B21_LOOP = "5486be4a8ef27c53f1144f77fdb17b257756b88a4d5a43851de1869e9c1be370"
_STRUCTURAL_LOOP = "bf7e49c98eb308dccf60979c2aafdb63ee20fe3d62610c057a54801a26d084cc"
_RAW = ast_fingerprint(ast.parse(RAW_AGENT).body[0])
_CLIPPED = ast_fingerprint(ast.parse(CLIPPED_AGENT).body[0])


class UnsupportedAgent(ValueError):
    """This source cannot be proven equivalent to the supported tape contract."""


@dataclass(frozen=True)
class CompiledTape:
    payload: bytes
    trim_hands: bool
    fingerprint: str
    source_sha256: str
    family: str


def _decompress(data):
    decoder = zlib.decompressobj()
    decoded = decoder.decompress(data, MAX_DECODED_BYTES + 1)
    if len(decoded) > MAX_DECODED_BYTES or not decoder.eof:
        raise UnsupportedAgent("oversized or truncated tape payload")
    return decoded


def _evaluate(node, values, decoder_allowed, depth=0):
    if depth > 64:
        raise UnsupportedAgent("data expression too deep")
    evaluate = lambda n, env=values: _evaluate(n, env, decoder_allowed, depth + 1)
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name) and node.id in values:
        return values[node.id]
    if isinstance(node, ast.List):
        return [evaluate(v) for v in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(evaluate(v) for v in node.elts)
    if isinstance(node, ast.Dict) and all(k is not None for k in node.keys):
        return {evaluate(k): evaluate(v) for k, v in zip(node.keys, node.values)}
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = evaluate(node.operand)
        if type(value) not in (int, float):
            raise UnsupportedAgent("non-numeric unary expression")
        return value if isinstance(node.op, ast.UAdd) else -value
    if isinstance(node, ast.ListComp) and len(node.generators) == 1:
        gen = node.generators[0]
        if gen.is_async or gen.ifs or not isinstance(gen.target, ast.Name):
            raise UnsupportedAgent("unsupported comprehension")
        sequence = evaluate(gen.iter)
        if not isinstance(sequence, (tuple, list)) or len(sequence) > 2:
            raise UnsupportedAgent("only the two-seat decoder comprehension is supported")
        return [evaluate(node.elt, {**values, gen.target.id: value}) for value in sequence]
    if isinstance(node, ast.Call) and not node.keywords:
        if isinstance(node.func, ast.Attribute) and node.func.attr == "decode":
            if node.args and (len(node.args) != 1 or evaluate(node.args[0]) not in ("utf-8", "utf8")):
                raise UnsupportedAgent("only UTF-8 decode is supported")
            value = evaluate(node.func.value)
            if not isinstance(value, bytes):
                raise UnsupportedAgent("decode receiver is not bytes")
            return value.decode("utf8")
        if len(node.args) == 1:
            function = ast.unparse(node.func)
            argument = evaluate(node.args[0])
            if function == "base64.b85decode" and isinstance(argument, (str, bytes)):
                return base64.b85decode(argument)
            if function == "zlib.decompress" and isinstance(argument, bytes):
                return _decompress(argument)
            if function == "json.loads" and isinstance(argument, (str, bytes)) and len(argument) <= MAX_DECODED_BYTES:
                return json.loads(argument)
            if function == "_d" and decoder_allowed and isinstance(argument, (str, bytes)):
                return json.loads(_decompress(base64.b85decode(argument)))
    raise UnsupportedAgent("source contains an unapproved data expression")



def _validate_actions(actions, *, require_hands=False):
    if not isinstance(actions, list) or len(actions) != 2 or any(not isinstance(s, list) or not s for s in actions):
        raise UnsupportedAgent("not a two-seat action tape")
    item_ops = {"PICKUP", "PLACE", "PLANT", "BUY_SEED", "BUY_PRODUCT", "BUY_ANIMAL", "SELL"}
    def operation(value):
        if not isinstance(value, list) or (value and not isinstance(value[0], str)):
            raise UnsupportedAgent("unproven action shape")
        if value and value[0] in item_ops:
            if len(value) > 1 and not isinstance(value[1], str):
                raise UnsupportedAgent("unproven item argument")
            if len(value) > 2 and (type(value[2]) not in (int, bool) or not -(2**63) <= value[2] < 2**63):
                raise UnsupportedAgent("auto-compilation requires integer quantity arguments")
    for stream in actions:
        for action in stream:
            if not isinstance(action, dict) or (require_hands and "hands" not in action):
                raise UnsupportedAgent("invalid action object for this template")
            if "farmer" in action:
                operation(action["farmer"])
            for field in ("hands", "market"):
                entries = action.get(field, [])
                if not isinstance(entries, list):
                    raise UnsupportedAgent("unproven hands/market container")
                for value in entries:
                    operation(value)


def compile_source(source):
    raw = source.encode("utf8") if isinstance(source, str) else source
    if len(raw) > MAX_SOURCE_BYTES:
        raise UnsupportedAgent("source exceeds size limit")
    try:
        tree = ast.parse(raw.decode("utf-8-sig"))
    except (SyntaxError, UnicodeError) as error:
        raise UnsupportedAgent("not supported Python source") from error
    function_nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    functions = {n.name: ast_fingerprint(n) for n in function_nodes}
    if len(functions) != len(function_nodes):
        raise UnsupportedAgent("duplicate function definition")
    primary = functions.get("agent")
    if primary == _DELEGATE:
        primary = functions.get("act")
    elif primary is None:
        primary = functions.get("act")
    families = {_B21: "b21", _STRUCTURAL: "structural", _V7: "v7", _V8: "v8", _RAW: "raw", _CLIPPED: "clipped"}
    if primary not in families:
        raise UnsupportedAgent("unrecognized or reactive policy body; ACTIONS alone is insufficient")
    if any(value not in {*families, _DELEGATE, _DECODER} for value in functions.values()):
        raise UnsupportedAgent("unapproved helper function")
    family = families[primary]
    allowed_names = {"ACTIONS", "BUY_WHEAT", "SELL_WHEAT", "_P0", "_P1", "_BLOB", "SEAT_MODE", "CLAMP_SELL", "RENOIR_OPENING", "OPENING_SWITCH_STEP"}
    values = {}
    imported = set()
    defined = set()
    definitions_started = False
    try:
        for node in tree.body:
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                continue
            if isinstance(node, ast.Import):
                if definitions_started:
                    raise UnsupportedAgent("imports must precede data and function definitions")
                if any(n.name not in {"base64", "copy", "json", "zlib"} or n.asname is not None for n in node.names):
                    raise UnsupportedAgent("unapproved import")
                imported.update(n.name for n in node.names)
                continue
            definitions_started = True
            if imported != {"base64", "copy", "json", "zlib"}:
                raise UnsupportedAgent("required standard imports are missing")
            if isinstance(node, ast.FunctionDef):
                defined.add(node.name)
                continue
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                key = node.targets[0].id
                if key == "act" and isinstance(node.value, ast.Name) and node.value.id == "agent" and "agent" in defined and functions.get("agent") in families:
                    continue
                if key not in allowed_names:
                    raise UnsupportedAgent("unapproved module assignment")
                values[key] = _evaluate(node.value, values, "_d" in defined and functions.get("_d") == _DECODER)
                continue
            if isinstance(node, ast.For):
                kind = ast_fingerprint(node)
                if kind not in {_B21_LOOP, _STRUCTURAL_LOOP}:
                    raise UnsupportedAgent("unapproved tape mutation")
                for stream in values["ACTIONS"]:
                    stream[0]["market"] = [["BUY_PRODUCT", "WHEAT", values["BUY_WHEAT"]]]
                    if kind == _B21_LOOP:
                        stream[1]["market"][0] = ["SELL", "WHEAT", values["SELL_WHEAT"]]
                    else:
                        for order in stream[1].get("market", []):
                            if order and order[0] == "SELL" and order[1] == "WHEAT":
                                order[2] = values["SELL_WHEAT"]
                continue
            raise UnsupportedAgent("unapproved top-level statement")
        actions = values["ACTIONS"]
        if family == "v8":
            if not isinstance(actions, list) or len(actions) < 720:
                raise UnsupportedAgent("fixed 719 clamp requires at least 720 entries")
            actions = copy.deepcopy(actions[:720])
            cutoff = values["OPENING_SWITCH_STEP"]
            opening = values["RENOIR_OPENING"]
            if type(cutoff) is not int or not 0 <= cutoff <= min(len(opening), 720):
                raise UnsupportedAgent("unsupported opening switch")
            for index in range(cutoff):
                actions[index]["market"] = copy.deepcopy(opening[index])
            actions = [actions, copy.deepcopy(actions)]
        if family == "v7":
            if values.get("CLAMP_SELL") is not False:
                raise UnsupportedAgent("CLAMP_SELL is state-dependent")
            mode = values.get("SEAT_MODE")
            if mode != "AUTO":
                if mode not in ("P0", "P1"):
                    raise UnsupportedAgent("unsupported schedule-side selection")
                selected = actions[int(mode[-1])]
                actions = [copy.deepcopy(selected), copy.deepcopy(selected)]
        _validate_actions(actions, require_hands=family == "v8")
        if family in ("b21", "structural"):
            if any(len(s) < 720 for s in actions):
                raise UnsupportedAgent("fixed 719 clamp requires at least 720 entries")
            actions = [s[:720] for s in actions]
        payload = json.dumps(actions, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    except UnsupportedAgent:
        raise
    except (KeyError, IndexError, TypeError, ValueError, zlib.error, UnicodeError) as error:
        raise UnsupportedAgent("invalid static tape data") from error
    trim = family != "raw"
    # Missing action fields and their explicit defaults mean the same thing
    # to the interpreter. Do not waste games on different metadata/key presence.
    effective = [[{"farmer": a.get("farmer", ["PASS"]), "hands": a.get("hands", []),
                   "market": a.get("market", [])} for a in stream] for stream in actions]
    effective_json = json.dumps(effective, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    fingerprint = hashlib.sha256(effective_json + (b"\x01" if trim else b"\x00")).hexdigest()
    return CompiledTape(payload, trim, fingerprint, hashlib.sha256(raw).hexdigest(), family)


def compile_file(path):
    path = Path(path)
    with path.open("rb") as stream:
        source = stream.read(MAX_SOURCE_BYTES + 1)
    return compile_source(source)


def emit_source(actions, *, trim_hands=True):
    """Self-contained static agent emitted in a recognized, auditable template."""
    _validate_actions(actions)
    blob = base64.b85encode(zlib.compress(json.dumps(actions, separators=(",", ":"), allow_nan=False).encode(), 9)).decode()
    return ("import base64, copy, json, zlib\n" + f"_BLOB = {blob!r}\n" +
            "ACTIONS = json.loads(zlib.decompress(base64.b85decode(_BLOB)))\n\n" +
            (CLIPPED_AGENT if trim_hands else RAW_AGENT) + "\nact = agent\n")
