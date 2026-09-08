#!/usr/bin/env python3
"""Controlled review of the immutable uploaded ZIP; never replaces production code.

Build original, build a separately labelled compile-only repair, compare both
against Python, then benchmark only a workload whose rewards match. Sources,
compiler diagnostics, mechanical patch and measurements remain distinguishable.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import shutil
import statistics
import struct
import subprocess
import sys
import tempfile
import time

from prepare_archive import prepare, ZIP_SHA256

ROOT = Path(__file__).resolve().parents[2]
PORT = ROOT / "kaggriculture_meta_lab/rust_port"
sys.path.insert(0, str(PORT / "tools"))
from export_tape import extract, write_tape
from py_reference import PythonReplay
from rust_client import _invoke


def cargo_build(crate, target, label, extra_env=None):
    command = ["cargo", "build", "--release", "--message-format=json", "--manifest-path", str(crate / "Cargo.toml")]
    if crate == PORT:
        command.append("--locked")
    env = {**os.environ, "CARGO_TARGET_DIR": str(target), "CARGO_TERM_COLOR": "never", **(extra_env or {})}
    start = time.perf_counter()
    run = subprocess.run(command, capture_output=True, text=True, env=env, timeout=300)
    diagnostics = []
    executable = None
    for line in run.stdout.splitlines():
        try:
            value = json.loads(line)
        except ValueError:
            continue
        if value.get("reason") == "compiler-message":
            message = value["message"]
            if message.get("level") == "error":
                diagnostics.append({"code": (message.get("code") or {}).get("code"),
                                    "message": message["message"], "rendered": message.get("rendered"),
                                    "locations": [{k: span[k] for k in ("file_name", "line_start", "column_start")} for span in message.get("spans", []) if span.get("is_primary")]})
        if value.get("reason") == "compiler-artifact" and value.get("executable") and value["target"]["name"] == "kg_sim":
            executable = value["executable"]
    return {"label": label, "exit_code": run.returncode, "elapsed_seconds": time.perf_counter() - start,
            "errors": diagnostics, "stderr": run.stderr[-2000:], "executable": executable}


def money_equal(expected, actual):
    # Numeric equality FIRST: converting a wrong >2**53 integer to float could
    # otherwise hide that it differs from the Python float-valued reward.
    return isinstance(actual, list) and len(actual) == 2 and all(
        type(v) in (int, float) and v == e and struct.pack(">d", v) == struct.pack(">d", e)
        for e, v in zip(expected, actual)
    )


def single(binary, case, work, alternate=False):
    command = [str(binary), "--tape-a", str(case["a_path"]), "--tape-b", str(case["b_path"]), "--seed", str(case["seed"])]
    if case.get("turns") is not None:
        command += ["--turns", str(case["turns"])] if alternate else ["--step-mode", "turns", "--steps", str(case["turns"])]
    else:
        command += ["--steps", str(case.get("steps", 720))]
    if case.get("reverse"):
        command.append("--reverse-seats")
    if case.get("trim"):
        command.append("--trim-hands")
    if case.get("config") is not None:
        path = work / "current-config.json"
        path.write_text(json.dumps(case["config"]))
        command += ["--config", str(path)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=20)
    try:
        value = json.loads(result.stdout)
    except ValueError:
        value = None
    return {"exit_code": result.returncode, "result": value, "stderr": result.stderr[-1000:]}


def batch(binary, jobs, steps, threads):
    # Identical Python I/O/protocol path for both binaries; no newer, unsupported
    # CLI flags are passed to the other implementation.
    with tempfile.TemporaryDirectory(prefix="kg-port-compare-") as directory:
        path = Path(directory) / "jobs.csv"
        resolved = {}
        with path.open("w", newline="") as output:
            writer = csv.writer(output)
            for seed, a, b, reverse in jobs:
                for tape in (a, b):
                    if tape not in resolved:
                        resolved[tape] = Path(tape).resolve()
                writer.writerow([seed, resolved[a], resolved[b], int(reverse)])
        return _invoke([str(binary), "--jobs", str(path), "--steps", str(steps), "--threads", str(threads)], len(jobs), False, timeout=180)


def measure(fn, repeats):
    times = []
    result = None
    for _ in range(repeats):
        start = time.perf_counter()
        result = fn()
        times.append(time.perf_counter() - start)
    return {"median_seconds": statistics.median(times), "samples_seconds": times}, result


def instrument(fixed):
    fixtures = json.loads((PORT / "tests/fixtures/conformance.json").read_text())
    for row in fixtures["rng"]:
        row["mixed_call_bits"] = [[struct.unpack(">Q", struct.pack(">d", value))[0], choice] for value, choice in row["mixed_calls"]]
    (fixed / "review_conformance.json").write_text(json.dumps(fixtures))
    here = Path(__file__).resolve().parent
    for source, fragment in [("src/main.rs", "probes_allocator.rs.txt"), ("src/sim.rs", "probes_sim.rs.txt")]:
        path = fixed / source
        path.write_text(path.read_text() + (here / fragment).read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=ROOT / "kaggriculture_meta_lab/kaggriculture_rust_port_updated_20260908.zip")
    parser.add_argument("--work", type=Path, default=ROOT / ".cache/port-review")
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--large-games", type=int, default=2048)
    args = parser.parse_args()
    if min(args.seeds, args.repeats, args.large_games) < 1:
        parser.error("positive counts required")
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    report = {"archive_sha256": ZIP_SHA256, "source_commit": os.environ.get("GITHUB_SHA"),
              "compiler": subprocess.check_output(["rustc", "--version"], text=True).strip(),
              "python": platform.python_version(), "platform": platform.platform(), "logical_cpus": os.cpu_count(),
              "scope": "original ZIP vs compile-only repair vs production engine; no gameplay repair in the alternate"}
    if Path("/proc/cpuinfo").exists():
        report["cpu"] = next((line.split(":", 1)[1].strip() for line in Path("/proc/cpuinfo").read_text().splitlines() if line.startswith("model name")), None)
    original, fixed, patch_path = prepare(args.archive, work)
    report["compile_patch_sha256"] = hashlib.sha256(patch_path.read_bytes()).hexdigest()
    report["original_build"] = cargo_build(original, work / "target-original", "unmodified ZIP")
    report["repaired_build"] = cargo_build(fixed, work / "target-fixed", "mechanical compile-only repair")
    ours = cargo_build(PORT, work / "target-ours", "production thin LTO")
    report["production_build"] = ours
    if ours["exit_code"]:
        raise RuntimeError(f"production build failed: {ours}")
    ours_bin = Path(ours["executable"])
    if report["repaired_build"]["exit_code"]:
        (work / "review.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        return
    alt_bin = work / "kg_sim_compile_only"
    shutil.copy2(report["repaired_build"]["executable"], alt_bin)
    report["binary_sha256"] = {"production": hashlib.sha256(ours_bin.read_bytes()).hexdigest(), "compile_only": hashlib.sha256(alt_bin.read_bytes()).hexdigest()}

    b21 = extract()
    asymmetric = copy.deepcopy(b21)
    asymmetric[0][0]["market"] = [["BUY_PRODUCT", "WHEAT", 17]]
    asymmetric[1][0]["market"] = [["BUY_PRODUCT", "WHEAT", 31]]
    asymmetric[1][1]["market"][0] = ["SELL", "WHEAT", 11]
    tapes = {"b21": b21, "asymmetric": asymmetric, "idle": [[{}], [{}]],
             "seat_a": [[{"market": [["BUY_SEED", "WHEAT", 1]]}], [{"market": [["BUY_SEED", "WHEAT", 3]]}]],
             "seat_b": [[{"market": [["BUY_SEED", "WHEAT", 2]]}], [{"market": [["BUY_SEED", "WHEAT", 4]]}]],
             "buy_product": [[{"market": [["BUY_PRODUCT", "WHEAT", 1]]}], [{}]],
             "guard": [[{"market": [["BUY_SEED", "WHEAT", 100000]]}], [{}]]}
    for name, quantity in [("string_qty", "2"), ("float_qty", 2.9), ("bool_qty", True), ("wide_qty", 2**31)]:
        tapes[name] = [[{"market": [["BUY_SEED", "WHEAT", quantity]]}], [{}]]
    animal = [{} for _ in range(26)]
    animal[0] = {"market": [["BUY_ANIMAL", "COW", 1]]}
    animal[1] = {"farmer": ["PICKUP", "COW"]}
    animal[2] = {"farmer": ["BUILD_PASTURE"]}
    animal[3] = {"farmer": ["PLACE", "COW", 0]}
    animal[24] = {"farmer": ["COLLECT_FERTILIZER"]}
    animal[25] = {"farmer": ["DROP"], "market": [["SELL", "FERTILIZER", 100]]}
    tapes["animal_qty_zero"] = [animal, [{}]]
    paths = {}
    for name, tape in tapes.items():
        paths[name] = work / f"{name}.json"
        write_tape(paths[name], tape)
    cases = []
    def add(name, a="b21", b="b21", seed=0, **options):
        cases.append({"name": name, "a": a, "b": b, "a_path": paths[a], "b_path": paths[b], "seed": seed, **options})
    for seed in range(args.seeds):
        add("b21_normal", seed=seed)
    edge_seeds = [0, 1, 7, 42, -1, 2**32, -(2**63), 2**63-1]
    for seed in edge_seeds:
        add("b21_trimmed", seed=seed, trim=True)
        add("asymmetric_normal", b="asymmetric", seed=seed)
        add("asymmetric_reverse", b="asymmetric", seed=seed, reverse=True)
    add("reverse_minimal", a="seat_a", b="seat_b", reverse=True, steps=2)
    add("kaggle_steps_one", a="seat_a", b="idle", steps=1)
    add("literal_zero_turns", a="seat_a", b="idle", turns=0)
    for name in ("string_qty", "float_qty", "bool_qty", "wide_qty"):
        add(name, a=name, b="idle", steps=2)
    add("animal_place_ignores_zero_qty", a="animal_qty_zero", b="idle", steps=27)
    add("market_i0_initialization", a="buy_product", b="idle", steps=2, config={"marketParams": {"WHEAT": {"I0": 400}}})
    add("fractional_market_base", a="buy_product", b="idle", steps=2, config={"marketParams": {"WHEAT": {"base": 25.5}}})
    add("unknown_shape_fallback", a="buy_product", b="idle", steps=2, config={"marketParams": {"WHEAT": {"below_func": "unknown"}}})
    full_spec = json.loads((PORT / "reference/kaggriculture_config.json").read_text())
    full_spec["configuration"]["startingMoney"]["default"] = 5000
    add("full_spec_override", a="idle", b="idle", steps=2, config=full_spec)
    add("money_above_exact_binary64", a="idle", b="idle", steps=2, config={"startingMoney": 2**53+1})
    add("market_guard_boundary", a="guard", b="idle", steps=2, config={"startingMoney": 1000000}, guard_warning=True)
    results = []
    for case in cases:
        with contextlib.redirect_stdout(io.StringIO()):
            expected = PythonReplay(tapes[case["a"]], tapes[case["b"]], case["seed"],
                                    steps=case.get("turns", case.get("steps", 720)),
                                    step_mode="turns" if "turns" in case else "kaggle",
                                    reverse=case.get("reverse", False), trim_hands=case.get("trim", False), config=case.get("config")).run()
        ours_result = single(ours_bin, case, work)
        alt_result = single(alt_bin, case, work, alternate=True)
        ours_equal = money_equal(expected, (ours_result["result"] or {}).get("rewards"))
        if not ours_equal:
            raise AssertionError(f"production/reference mismatch: {case['name']} {expected} {ours_result}")
        results.append({"case": case["name"], "seed": case["seed"], "expected": expected,
                        "production": ours_result, "alternate": alt_result,
                        "alternate_equal": money_equal(expected, (alt_result["result"] or {}).get("rewards"))})
    report["parity"] = {"cases": len(results), "production_matches": len(results),
                        "alternate_matches": sum(row["alternate_equal"] for row in results), "rows": results}

    # Quoted filename is a real CSV field, not a comma-separated substring.
    quoted = work / "quoted, tape.json"
    write_tape(quoted, tapes["idle"])
    csv_results = {}
    for label, binary in (("production", ours_bin), ("alternate", alt_bin)):
        try:
            value = batch(binary, [(0, quoted, paths["idle"], False)], 2, 1)
            csv_results[label] = {"ok": value == [{"rewards": [3000, 3000], "errors": []}], "results": value}
        except Exception as error:
            csv_results[label] = {"ok": False, "error": str(error)[:1200]}
    report["quoted_csv_path"] = csv_results
    assert csv_results["production"]["ok"]

    # Diagnostics are cfg(test)-only; benchmark binary above was saved before
    # this instrumentation and does not contain an allocation counter.
    instrument(fixed)
    report["injected_probes"] = {}
    for mode in ("debug", "release"):
        cmd = ["cargo", "test", "--manifest-path", str(fixed / "Cargo.toml")]
        if mode == "release":
            cmd.append("--release")
        cmd += ["review_", "--", "--nocapture"]
        probe = subprocess.run(cmd, capture_output=True, text=True, timeout=180,
                               env={**os.environ, "CARGO_TARGET_DIR": str(work / "target-fixed"), "CARGO_TERM_COLOR": "never"})
        output = probe.stdout + probe.stderr
        report["injected_probes"][mode] = {"exit_code": probe.returncode, "log": output[-14000:]}
        for line in probe.stdout.splitlines():
            if line.startswith("REVIEW_ALLOC_JSON="):
                report["injected_probes"][mode]["allocations_after_setup"] = json.loads(line.partition("=")[2])

    # Performance uses NON-REVERSED normal B21 self-play, the common validated
    # subset. It does NOT excuse the failures in unsupported/broken scenarios.
    common_ok = all(r["alternate_equal"] for r in results if r["case"] == "b21_normal")
    report["performance_common_subset_validated"] = common_ok
    if common_ok:
        jobs = [(seed, paths["b21"], paths["b21"], False) for seed in range(64)]
        python_time, expected = measure(lambda: [PythonReplay(b21, b21, seed).run() for seed in range(64)], args.repeats)
        report["performance"] = {"games": 64, "repeats": args.repeats, "steps": 720, "action_turns": 719,
                                  "reverse": False, "python": python_time, "binaries": {}}
        variants = {"production_thin": ours_bin, "alternate_compile_only_fat": alt_bin}
        fat = cargo_build(PORT, work / "target-ours-fat", "production with fat LTO experiment", {"CARGO_PROFILE_RELEASE_LTO": "fat"})
        report["fat_lto_build"] = fat
        if fat["exit_code"] == 0:
            variants["production_fat_experiment"] = Path(fat["executable"])
        for label, binary in variants.items():
            batch(binary, jobs[:8], 720, 4)
            measurements = {}
            for threads in (1, 4):
                timing, got = measure(lambda: batch(binary, jobs, 720, threads), args.repeats)
                assert all(money_equal(e, r["rewards"]) for e, r in zip(expected, got))
                timing["speedup_vs_python"] = python_time["median_seconds"] / timing["median_seconds"]
                measurements[f"batch_{threads}_threads"] = timing
            single_time, got = measure(lambda: [_invoke([str(binary), "--tape-a", str(paths["b21"]), "--tape-b", str(paths["b21"]), "--seed", str(seed), "--steps", "720"], 1, False)[0] for seed in range(64)], args.repeats)
            assert all(money_equal(e, r["rewards"]) for e, r in zip(expected, got))
            single_time["speedup_vs_python"] = python_time["median_seconds"] / single_time["median_seconds"]
            measurements["one_process_per_game"] = single_time
            report["performance"]["binaries"][label] = measurements
        large_jobs = [(seed, paths["b21"], paths["b21"], False) for seed in range(args.large_games)]
        reference = None
        report["large_batch"] = {"games": args.large_games, "threads": 4, "repeats": args.repeats, "binaries": {}}
        for label, binary in variants.items():
            timing, got = measure(lambda: batch(binary, large_jobs, 720, 4), args.repeats)
            if reference is None:
                reference = got
            equal = len(got) == len(reference) and all(money_equal(a["rewards"], b["rewards"]) for a, b in zip(reference, got))
            timing["equal_to_production"] = equal
            timing["games_per_second"] = args.large_games / timing["median_seconds"]
            report["large_batch"]["binaries"][label] = timing
    report["production_changed"] = False
    report["no_kaggle_submission"] = True
    (work / "review.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"original_build_exit": report["original_build"]["exit_code"],
                      "repaired_build_exit": report["repaired_build"]["exit_code"],
                      "parity": {k: v for k, v in report["parity"].items() if k != "rows"},
                      "performance": report.get("performance"), "large_batch": report.get("large_batch")}, indent=2))


if __name__ == "__main__":
    main()
