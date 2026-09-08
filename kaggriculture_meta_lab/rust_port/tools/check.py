#!/usr/bin/env python3
"""Bit-exact differential tests: Rust vs the unmodified Python 1.32.7 interpreter.

The default suite checks 50+ seeds, both seats, raw/trimmed hands, coupled market,
configuration overrides, episode/action horizons, and full per-turn state traces.
No tolerance: rewards are compared as IEEE-754 bytes, not approximately.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
import time

from export_tape import extract, write_tape
from py_reference import PythonReplay, SIM

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BIN = ROOT / "target/release/kg_sim"


def bits(values):
    return b"".join(struct.pack(">d", float(v)) for v in values)


def difference(expected, actual, path="$ "):
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or expected.keys() != actual.keys():
            return f"{path}: different keys: Python={set(expected)}, Rust={set(actual) if isinstance(actual, dict) else actual!r}"
        for key in expected:
            found = difference(expected[key], actual[key], f"{path}.{key}")
            if found:
                return found
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(expected) != len(actual):
            return f"{path}: different list lengths: Python={len(expected)}, Rust={len(actual) if isinstance(actual, list) else actual!r}"
        for i, (left, right) in enumerate(zip(expected, actual)):
            found = difference(left, right, f"{path}[{i}]")
            if found:
                return found
    elif isinstance(expected, float) and isinstance(actual, (int, float)) and not isinstance(actual, bool):
        if bits([expected]) != bits([actual]):
            return f"{path}: Python={expected.hex()}, Rust={float(actual).hex()}"
    elif expected != actual:
        return f"{path}: Python={expected!r}, Rust={actual!r}"
    return None


def flags(*, steps=720, step_mode="kaggle", trim_hands=False, config_path=None, trim_hands_a=False, trim_hands_b=False):
    result = ["--steps", str(steps), "--step-mode", step_mode]
    if trim_hands:
        result.append("--trim-hands")
    if trim_hands_a:
        result.append("--trim-hands-a")
    if trim_hands_b:
        result.append("--trim-hands-b")
    if config_path:
        result += ["--config", str(config_path)]
    return result


def trace_check(binary, work, paths, tapes, seed, *, reverse=False, trim_hands=False, steps=720, step_mode="kaggle", config=None, trim_hands_a=False, trim_hands_b=False):
    trace = work / "current-trace.jsonl"
    cfg_path = None
    if config is not None:
        cfg_path = work / "current-config.json"
        cfg_path.write_text(json.dumps(config))
    cmd = [str(binary), "--tape-a", str(paths[0]), "--tape-b", str(paths[1]), "--seed", str(seed), "--trace", str(trace)]
    cmd += flags(steps=steps, step_mode=step_mode, trim_hands=trim_hands, config_path=cfg_path, trim_hands_a=trim_hands_a, trim_hands_b=trim_hands_b)
    if reverse:
        cmd.append("--reverse-seats")
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    result = json.loads(proc.stdout)
    assert not result["errors"], result
    py = PythonReplay(*tapes, seed, reverse=reverse, trim_hands=trim_hands, steps=steps, step_mode=step_mode, config=config, trim_hands_a=trim_hands_a, trim_hands_b=trim_hands_b)
    count = 0
    with trace.open() as f:
        for line in f:
            if count:
                assert py.advance(), "Rust emitted extra turns"
            actual = json.loads(line)
            diff = difference(py.snapshot(), actual)
            if diff:
                # Keep just this trace; the first differing state is reported in CI.
                raise AssertionError(f"seed={seed} reverse={reverse} trim={trim_hands}/A={trim_hands_a}/B={trim_hands_b} horizon={steps}/{step_mode}, turn={py.step}: {diff}")
            count += 1
    assert not py.advance(), "Rust trace ended early"
    assert count == py.turns + 1, (count, py.turns)
    assert bits(result["rewards"]) == bits(py.rewards()), (result, py.rewards())
    trace.unlink()
    return count


def random_tape(seed, turns=120):
    """Static, deterministic stress actions; never a Rust-side reactive policy."""
    rng = random.Random(seed)
    farmer_ops = [[op] for op in ("NORTH", "SOUTH", "EAST", "WEST", "PASS", "DROP", "DIG", "WATER", "HARVEST", "BUILD_COOP", "BUILD_PASTURE", "FERTILIZE", "FEED", "CARE", "COLLECT_FERTILIZER")]
    farmer_ops += [["PLANT", crop] for crop in SIM.CROPS]
    farmer_ops += [[op, item, n] for op in ("PICKUP", "PLACE") for item in list(SIM.ANIMALS) + ["WHEAT", "FERTILIZER"] for n in (1, 3)]
    orders = [["HIRE"], ["BUY_LAND"], [], ["UNKNOWN"], ["SELL", "WHEAT", "n/a"]]
    orders += [["BUY_SEED", crop, n] for crop in SIM.CROPS for n in (1, "2", 3.9, True)]
    orders += [["BUY_ANIMAL", animal, 1] for animal in SIM.ANIMALS]
    orders += [["BUY_PRODUCT", item, 3] for item in ("WHEAT", "FERTILIZER")]
    orders += [["SELL", item, 100] for item in SIM.PRODUCTS]
    return [[{"farmer": rng.choice(farmer_ops), "hands": [rng.choice(farmer_ops) for _ in range(rng.randrange(8))], "market": [rng.choice(orders) for _ in range(rng.randrange(14))]} for _ in range(turns)] for _ in range(2)]


def verify_sources():
    manifest = json.loads((ROOT / "reference/provenance.json").read_text())
    for name, expected in manifest["files"].items():
        actual = hashlib.sha256((ROOT / "reference" / name).read_bytes()).hexdigest()
        assert expected == actual, f"pinned reference changed: {name}"
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="explicit check mode (also the default)")
    parser.add_argument("--binary", type=Path, default=DEFAULT_BIN)
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--work", type=Path, default=ROOT / "work/check")
    args = parser.parse_args()
    if args.seeds < 1 or args.threads < 1:
        parser.error("--seeds and --threads must be positive")
    args.binary = args.binary.resolve()
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    manifest = verify_sources()
    example = extract()
    idle = [[{}], [{}]]
    asymmetric = copy.deepcopy(example)
    asymmetric[0][0]["market"] = [["BUY_PRODUCT", "WHEAT", 17]]
    asymmetric[1][0]["market"] = [["BUY_PRODUCT", "WHEAT", 31]]
    asymmetric[1][1]["market"][0] = ["SELL", "WHEAT", 11]
    tapes = {"example": example, "idle": idle, "asymmetric": asymmetric}
    paths = {name: work / f"{name}.json" for name in tapes}
    for name, tape in tapes.items():
        write_tape(paths[name], tape)
    seeds = list(dict.fromkeys(list(range(args.seeds)) + [-1, 2**32, -(2**63), 2**63 - 1]))
    checked_seeds = set(seeds)
    reward_checks = 0
    state_checks = 0
    batch_modes = []
    for trim in [False, True]:
        combos = [("example", "example", False), ("example", "idle", False), ("example", "idle", True), ("example", "asymmetric", True)]
        jobs = [(seed, a, b, reverse) for seed in seeds for a, b, reverse in combos]
        job_path = work / "jobs.csv"
        with job_path.open("w", newline="") as f:
            writer = csv.writer(f)
            for seed, a, b, reverse in jobs:
                writer.writerow([seed, paths[a].name, paths[b].name, int(reverse)])
        common = [str(args.binary), "--jobs", str(job_path)] + flags(trim_hands=trim)
        serial = subprocess.run(common + ["--threads", "1"], check=True, capture_output=True).stdout
        parallel = subprocess.run(common + ["--threads", str(args.threads)], check=True, capture_output=True).stdout
        assert serial == parallel, "Rayon changes output/order across thread counts"
        results = [json.loads(line) for line in parallel.splitlines()]
        assert len(results) == len(jobs)
        for job, result in zip(jobs, results):
            seed, a, b, reverse = job
            expected = PythonReplay(tapes[a], tapes[b], seed, reverse=reverse, trim_hands=trim).run()
            assert not result["errors"], (job, result)
            if bits(expected) != bits(result["rewards"]):
                trace_check(args.binary, work, (paths[a], paths[b]), (tapes[a], tapes[b]), seed, reverse=reverse, trim_hands=trim)
                raise AssertionError(f"rewards differ: {job}: Python={expected}, Rust={result}")
            reward_checks += 1
        batch_modes.append({"trim_hands": trim, "games": len(jobs), "thread_counts": [1, args.threads], "byte_identical_batch_output": True})
        for seed, a, b, reverse in [jobs[0], jobs[2], jobs[-1]]:
            state_checks += trace_check(args.binary, work, (paths[a], paths[b]), (tapes[a], tapes[b]), seed, reverse=reverse, trim_hands=trim)

    # The real LAB trims its candidate but not recorded opponent actions.
    # Rules must move with A/B rather than staying attached to physical seats.
    for a_trim, b_trim in [(True, False), (False, True)]:
        for reverse in [False, True]:
            for seed in [0, -1]:
                state_checks += trace_check(args.binary, work, (paths["example"], paths["asymmetric"]),
                                            (example, asymmetric), seed, reverse=reverse,
                                            trim_hands_a=a_trim, trim_hands_b=b_trim)
                reward_checks += 1

    # Exact-turns mode covers the true final daily refresh, including shop RNG.
    checked_seeds.update((17, 41))
    for steps in [0, 1, 23, 24, 25, 72, 720, 721, 769]:
        state_checks += trace_check(args.binary, work, (paths["example"], paths["asymmetric"]), (example, asymmetric), 17, steps=steps, step_mode="turns")
        reward_checks += 1
    for steps in [1, 2, 24, 25, 721]:
        state_checks += trace_check(args.binary, work, (paths["example"], paths["idle"]), (example, idle), 41, steps=steps)
        reward_checks += 1

    configs = [
        {"marketParams": {"default": {"WHEAT": {"base": 900}}, "WHEAT": {"base": 40}}},
        {"marketParams": {"default": {}}},
        {"startingMoney": 5000.0, "boardSize": 10.0, "turnsPerDay": 6.0, "shedCapacity": 3.0, "farmHandCostMult": 0.0},
        {"weedSpawnChance": 0, "townShopUnlockInterval": 1, "townShopSellInterval": 1, "townCenterSellInterval": 1},
        {"weedSpawnChance": 1, "turnsPerDay": 6, "maxMarketOrdersPerTurn": 2, "shedCapacity": 1, "startingMoney": 100000, "farmHandCostMult": 0},
        {"startingMoney": 0, "farmHandCostMult": 0, "shedCapacity": 2},
        {"startingMoney": 100000, "farmHandCostMult": 3, "shedCapacity": 7, "townShopUnlockInterval": 2, "townShopSellInterval": 3, "townCenterSellInterval": 7,
         "marketParams": {"WHEAT": {"base": 25.5, "I0": 400.5, "T": 3, "below_func": "log10", "below_target": 0.2, "above_func": "hinge"}, "CARROT": {"below_func": "sq"}, "MILK": {"above_func": "log10"}, "FERTILIZER": {"below_func": "unknown-fallback", "note": "preserve sparse overrides"}, "WOOL": 7, "UNKNOWN": {"base": 99}}},
    ]
    for i, config in enumerate(configs):
        checked_seeds.add(-17 - i)
        state_checks += trace_check(args.binary, work, (paths["example"], paths["asymmetric"]), (example, asymmetric), -17 - i, config=config, step_mode="turns")
        reward_checks += 1

    for i in range(12):
        checked_seeds.add(100000 + i)
        tape = random_tape(1000 + i)
        path = work / "random.json"
        write_tape(path, tape)
        config = {"startingMoney": 100000, "farmHandCostMult": i % 3, "shedCapacity": [1, 3, 100][i % 3], "turnsPerDay": [4, 7, 24][i % 3], "townShopUnlockInterval": 1, "weedSpawnChance": [0, 0.005, 0.1][i % 3]}
        state_checks += trace_check(args.binary, work, (path, paths["example"]), (tape, example), 100000 + i, steps=360, step_mode="turns", reverse=bool(i % 2), trim_hands=bool(i % 3), config=config)
        reward_checks += 1

    report = {
        "status": "passed", "engine": manifest["upstream_version"],
        "simulator_sha256": manifest["files"]["kaggriculture_sim.py"],
        "batch_seed_count": len(seeds), "distinct_episode_seeds": len(checked_seeds), "reward_comparisons": reward_checks,
        "full_state_comparisons": state_checks, "reward_comparison": "IEEE-754 binary64 byte equality (no tolerance)",
        "batches": batch_modes, "mixed_hand_mode_full_episodes": 8, "elapsed_seconds": round(time.perf_counter() - started, 3),
    }
    (ROOT / "work").mkdir(exist_ok=True)
    (ROOT / "work/check-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
