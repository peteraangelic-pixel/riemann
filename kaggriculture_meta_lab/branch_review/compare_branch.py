#!/usr/bin/env python3
"""Read-only comparison of peer engine + LAB boundary, with real Rust binaries.

Kernel equality is checked bytewise; boundary regressions are tested against
an unmodified Kaggle framework. Benchmarks time the WHOLE adapter call, not
only its final subprocess. No policy search or Kaggle submission is performed.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import urllib.request
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
PORT = ROOT / "kaggriculture_meta_lab/rust_port"
sys.path.insert(0, str(PORT))
sys.path.insert(0, str(PORT / "tools"))
from tools.agent_tape import compile_file, emit_source
from tools import lab_backend
from tools.py_reference import PythonReplay
from tools.check_framework import load_framework, WHEEL_URL, WHEEL_SHA256


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def core_for_review(work):
    wheel = work / "environment.whl"
    if not wheel.exists():
        with urllib.request.urlopen(WHEEL_URL, timeout=120) as response, wheel.open("wb") as target:
            shutil.copyfileobj(response, target)
    if digest(wheel) != WHEEL_SHA256:
        raise ValueError("untrusted wheel")
    core = load_framework(wheel, work / "framework")
    sys.modules["kaggle_environments"].make = core.make
    return core


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--work", type=Path, default=ROOT / ".cache/branch-review-results")
    parser.add_argument("--jobs", type=int, default=256)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    peer_lab = args.source.resolve() / "kaggriculture_meta_lab"
    peer_port = peer_lab / "rust_port"
    manifest = json.loads((Path(__file__).parent / "source_manifest.json").read_text())
    identity = {str(p.relative_to(PORT)): {"ours": digest(p), "peer": digest(peer_port / p.relative_to(PORT))}
                for p in list((PORT / "src").glob("*.rs")) + [PORT / "Cargo.toml", PORT / "Cargo.lock"]}
    assert all(v["ours"] == v["peer"] for v in identity.values()), "kernel changed; review differences first"
    report = {"peer_commit": manifest["commit"], "later_checked_peer_commit": manifest["later_checked_commit"],
              "ours_commit": os.environ.get("GITHUB_SHA"), "kernel_identity": identity,
              "logical_cpus": os.cpu_count(), "rustc": subprocess.check_output(["rustc", "--version"], text=True).strip()}
    if Path("/proc/cpuinfo").exists():
        report["cpu"] = next((line.split(":", 1)[1].strip() for line in Path("/proc/cpuinfo").read_text().splitlines() if line.startswith("model name")), None)
    binaries = {}
    for label, crate in (("ours", PORT), ("peer", peer_port)):
        subprocess.run(["cargo", "build", "--release", "--locked", "--manifest-path", str(crate / "Cargo.toml")], check=True, timeout=300)
        binaries[label] = crate / "target/release/kg_sim"
    report["binary_sha256"] = {label: digest(path) for label, path in binaries.items()}
    core = core_for_review(work)
    sys.path.insert(0, str(peer_lab))
    from kaggriculture_lab import agents as peer_agents, tournament as peer_tournament
    peer = load(peer_lab / "kaggriculture_lab/rust_backend.py", "review_peer_backend")
    peer_client = load(peer_port / "tools/rust_client.py", "review_peer_client")
    generator = load(peer_lab / "scripts/structural_gen.py", "review_peer_generator")

    def reference_one(job):
        seed, a, b, seat, steps, tag = job
        first, second = peer_agents.resolve(a), peer_agents.resolve(b)
        players = [first, second] if seat == 0 else [second, first]
        env = core.make("kaggriculture", configuration={"seed": seed, "episodeSteps": steps})
        failures = []
        original = env.interpreter
        def audited(states, context):
            failures.extend(s.status for s in states if s.status in ("ERROR", "TIMEOUT", "INVALID"))
            return original(states, context)
        env.interpreter = audited
        env.run(players)
        if failures:
            raise AssertionError(f"reference agent failed: {failures}")
        own, other = float(env.state[seat].reward), float(env.state[1-seat].reward)
        return {"tag": tag, "seed": seed, "seat": seat, "opponent": b,
                "self_reward": own, "opp_reward": other, "margin": own-other,
                "outcome": "win" if own>other else "loss" if own<other else "tie", "error": None}

    def python_runner(jobs, workers, **kwargs):
        # Intentionally reverse completion order, just as as_completed may do.
        return [reference_one(job) for job in reversed(jobs)]

    def old_run(jobs):
        with patch.dict(sys.modules, {"rust_client": peer_client}), patch.object(peer_tournament, "run", side_effect=python_runner):
            return peer.run_rust(jobs, 4, binary=binaries["peer"], progress_every=0)

    def new_run(jobs):
        return lab_backend.run_report(jobs, 4, binary=binaries["ours"], python_runner=python_runner, progress_every=0)

    def write_agent(name, data, trim=False):
        path = work / "agents" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(emit_source(data, trim_hands=trim))
        return str(path)

    a_data = [[{"market": [["BUY_SEED", "WHEAT", 1]]}], [{"market": [["BUY_SEED", "WHEAT", 3]]}]]
    b_data = [[{"market": [["BUY_SEED", "WHEAT", 2]]}], [{"market": [["BUY_SEED", "WHEAT", 4]]}]]
    a = write_agent("alpha.py", a_data)
    b = write_agent("beta.py", b_data)
    same_a = write_agent("one/agent.py", a_data)
    same_b = write_agent("two/agent.py", b_data)
    reactive = work / "agents/reactive.py"
    reactive.write_text('ACTIONS=[[{"market":[["BUY_SEED","WHEAT",99]]}],[{}]]\n'
                        'def agent(observation, configuration):\n'
                        ' if observation["farms"][observation["player"]]["money"] > 0:\n'
                        '  return {"farmer":["PASS"],"hands":[],"market":[]}\n'
                        ' return ACTIONS[observation["player"]][0]\n')
    phantom = [{} for _ in range(50)]
    phantom[0] = {"market": [["BUY_SEED", "WHEAT", 1]]}
    phantom[1] = {"farmer": ["PLANT", "WHEAT"], "hands": [["PLANT", "WHEAT"]]}
    phantom[2] = {"farmer": ["WATER"]}
    phantom[24] = {"farmer": ["WATER"]}
    phantom[48] = {"farmer": ["HARVEST"]}
    phantom[49] = {"farmer": ["DROP"], "market": [["SELL", "WHEAT", 100]]}
    clipped = write_agent("clipped.py", [phantom, phantom], True)
    raw = write_agent("raw.py", [phantom, phantom], False)
    suites = {
        "same_basename": [(0, same_a, same_b, 0, 2, "same-name")],
        "mixed_horizons": [(0, a, b, 0, 2, "short"), (0, a, b, 0, 3, "long")],
        "reactive_with_actions": [(0, str(reactive), b, 0, 2, "reactive")],
        "mixed_hand_rules": [(17, clipped, raw, seat, 51, f"seat-{seat}") for seat in (0,1)],
        "python_completion_order": [(11, "pass", "pass", 0, 2, "duplicate-tag"), (12, a, b, 0, 2, "native"), (13, "pass", "pass", 1, 3, "duplicate-tag")],
    }
    report["boundary_cases"] = {}
    for name, jobs in suites.items():
        expected = [reference_one(job) for job in jobs]
        with redirect_stdout(io.StringIO()):
            old = old_run(jobs)
            new = new_run(jobs)
        assert new.rows == expected, (name, new.rows, expected)
        report["boundary_cases"][name] = {"expected": expected, "peer": old, "ours": new.rows,
                                         "peer_equal": old == expected, "ours_equal": True,
                                         "our_metrics": new.metrics}

    # Current controls: every emitted action at every turn, both seats and four
    # live-hand counts, then actual full games for two seeds and both seats.
    controls = sorted((peer_lab / "agents/current").glob('*.py'))
    b21 = peer_lab / "agents/current/agent_v9_b21_s16.py"
    report["template_equivalence"] = []
    checks = 0
    for path in controls:
        compiled = compile_file(path)
        data = json.loads(compiled.payload)
        policy = peer_agents.resolve(str(path))
        for seat in (0,1):
            for step in list(range(720)) + [721, 999]:
                for hands in (0,1,5,12):
                    obs = {"player": seat, "step": step, "farms": [{"hands": [[4,4]]*hands} for _ in (0,1)], "private": {"shed": {}}}
                    expected = policy(obs, {})
                    got = copy.deepcopy(data[seat][min(step,len(data[seat])-1)])
                    if compiled.trim_hands:
                        got["hands"] = got.get("hands", [])[:hands]
                    assert got == expected, (path.name, seat, step, hands)
                    checks += 1
        jobs = [(seed, str(b21), str(path), seat, 720, str(path.name)) for seed in (0,7) for seat in (0,1)]
        expected = [reference_one(job) for job in jobs]
        with redirect_stdout(io.StringIO()):
            got = new_run(jobs)
        assert got.rows == expected
        report["template_equivalence"].append({"file": path.name, "family": compiled.family,
                                               "fingerprint": compiled.fingerprint,
                                               "peer_detects_as_tape": peer._is_tape_spec(str(path)),
                                               "full_framework_games": len(jobs), "ours_equal": True})
    report["template_action_comparisons"] = checks
    generated = work / "agents/generated.py"
    generated.write_text(generator.make_variant_source({"fert_scale": 1.5}))
    generated_data = load(generated, "review_generated_tape").ACTIONS
    assert json.loads(compile_file(generated).payload) == generated_data
    report["generated_structural_template_compiles_losslessly"] = True

    structural = [[{} for _ in range(720)] for _ in (0,1)]
    for stream in structural:
        stream[-2]["market"] = [["SELL", "WHEAT", 500]]
        stream[-1]["market"] = [["SELL", "WHEAT", 500]]
    first = generator.apply_mutations(copy.deepcopy(structural), {"liquidate_from": 600})
    second = generator.apply_mutations(copy.deepcopy(structural), {"liquidate_from": 700})
    fert = [[{"market": [["BUY_PRODUCT", "FERTILIZER", 5]]}], [{}]]
    fert = generator.apply_mutations(fert, {"fert_scale": 0.0})
    expanded = generator.apply_mutations(generator.load_champion_actions(), {"hire_scale": 1.3})
    report["structural_generator"] = {
        "cutoff_600_vs_700_raw_json_identical": first == second,
        "cutoff_600_vs_700_effective_markets_identical": [[a.get("market") or [] for a in stream] for stream in first] == [[a.get("market") or [] for a in stream] for stream in second],
        "new_compiler_reuses_effective_cutoff_identity": compile_file(write_agent("cutoff600.py", first, True)).fingerprint == compile_file(write_agent("cutoff700.py", second, True)).fingerprint,
        "first_liquidation_step_for_600": next(i for i,a in enumerate(first[0]) if a.get("market")),
        "fertilizer_qty_at_scale_zero": fert[0][0]["market"][0][2],
        "missing_tomato_in_product_kinds": "TOMATO" not in generator.PRODUCT_KINDS,
        "turns_above_10_orders_at_hire_scale_1_3": sum(len(a.get("market", [])) > 10 for s in expanded for a in s),
        "no_agent_strength_claim": True,
    }
    jobs = [(seed, str(b21), str(b21), seed%2, 720, "benchmark") for seed in range(args.jobs)]
    # Import-count measurement is outside timed samples, avoiding spy overhead.
    with patch.object(peer, "_load_actions", wraps=peer._load_actions) as counter, redirect_stdout(io.StringIO()):
        old_run(jobs[:8])
        loads = counter.call_count
    report["peer_load_actions_calls_for_8_jobs_one_unique_file"] = loads
    with redirect_stdout(io.StringIO()):
        new_probe = new_run(jobs[:8])
    report["our_preparation_for_8_jobs"] = new_probe.metrics

    # A protocol failure must not replay an already-started mixed batch.
    calls = []
    def fallback_spy(jobs, workers, **kwargs):
        calls.append(len(jobs))
        return python_runner(jobs, workers, **kwargs)
    fail_jobs = [(0, a, b, 0, 2, "native"), (1, "pass", "pass", 0, 2, "python")]
    with patch.dict(sys.modules, {"rust_client": peer_client}), patch.object(peer, "rust_binary", return_value=binaries["peer"]), patch.object(peer_client, "replay_many", side_effect=RuntimeError("injected native failure")), patch.object(peer_tournament, "run", side_effect=fallback_spy), redirect_stdout(io.StringIO()):
        peer.run_auto(fail_jobs, 4)
    report["peer_python_fallback_calls_after_native_failure"] = calls[:]
    calls.clear()
    with patch("tools.lab_backend.rust_client.replay_many", side_effect=RuntimeError("injected native failure")), redirect_stdout(io.StringIO()):
        try:
            lab_backend.run_report(fail_jobs, 4, binary=binaries["ours"], python_runner=fallback_spy)
        except lab_backend.BackendError:
            pass
        else:
            raise AssertionError("native failure was hidden")
    report["our_python_fallback_calls_after_native_failure"] = calls

    # Test .exe discovery without pretending this Linux job is a Windows run.
    exe = work / "windows-name/kg_sim.exe"
    exe.parent.mkdir(exist_ok=True)
    exe.write_text("probe only")
    exe.chmod(0o755)
    with patch.object(peer, "_DEFAULT_BINARY", exe.with_suffix("")):
        report["peer_finds_exe_without_suffix_in_default_path"] = peer.rust_binary() is not None
    report["our_windows_default_name"] = lab_backend.rust_client.binary_name("nt")

    # No stdout timing extracted from the peer's rounded native-only message.
    # Both measurements include classification, exports, CSV I/O and cleanup
    # performed by the adapter itself. Outputs must match exactly.
    times = {"peer": [], "ours": []}
    expected = None
    for repeat in range(args.repeats):
        for name in (["peer", "ours"] if repeat%2 == 0 else ["ours", "peer"]):
            with redirect_stdout(io.StringIO()):
                start = time.perf_counter()
                result = old_run(jobs) if name == "peer" else new_run(jobs).rows
                elapsed = time.perf_counter() - start
            if expected is None:
                expected = result
            assert result == expected, f"timed batch mismatch: {name}"
            times[name].append(elapsed)
    report["adapter_benchmark"] = {"games": args.jobs, "repeats": args.repeats, "threads": 4,
                                    "workload": "B21 self-play, varied seeds, alternating seats, whole adapter call",
                                    "samples_seconds": times,
                                    "median_seconds": {k:statistics.median(v) for k,v in times.items()}}
    report["adapter_benchmark"]["speedup_ours_vs_peer"] = statistics.median(times["peer"])/statistics.median(times["ours"])
    report["scope"] = "same native engine; improvements are in the LAB boundary, not a new faster game algorithm"
    report["status"] = "completed; inspect individual peer failures, not only workflow color"
    (work / "review.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({"boundary_cases": {k:v["peer_equal"] for k,v in report["boundary_cases"].items()},
                      "template_action_comparisons": checks, "adapter_benchmark": report["adapter_benchmark"],
                      "structural_generator":report["structural_generator"]},indent=2))


if __name__ == "__main__":
    main()
