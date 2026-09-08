#!/usr/bin/env python3
"""Bounded integration pilot, NOT an agent search or promotion.

Run the actual patched sweep CLI through Python and Rust, compare every stage's
rows and decisions, and check frozen real controls. Synthetic policies force
all three stages to execute so skipped finals cannot give a vacuous pass.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import time
import urllib.request
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PORT = ROOT / "kaggriculture_meta_lab/rust_port"
sys.path[:0] = [str(ROOT / "kaggriculture_meta_lab"), str(PORT / "tools")]
from rust_port.tools.agent_tape import emit_source
from rust_port.tools.check_framework import load_framework, WHEEL_URL, WHEEL_SHA256
from prepare import prepare
from guard_tests import load_sweep


MAX_PER_BACKEND = 128
EXPECTED_FUNNEL_GAMES = 96


def setup_framework(work):
    wheel = work / "environment.whl"
    if not wheel.exists():
        with urllib.request.urlopen(WHEEL_URL, timeout=120) as response, wheel.open("wb") as target:
            while chunk := response.read(1024 * 1024):
                target.write(chunk)
    if hashlib.sha256(wheel.read_bytes()).hexdigest() != WHEEL_SHA256:
        raise ValueError("untrusted environment wheel")
    core = load_framework(wheel, work / "framework")
    sys.modules["kaggle_environments"].make = core.make


def normalized_rows(rows):
    normalized = []
    for row in rows:
        normalized.append({"tag": row["tag"], "seed": row["seed"], "seat": row["seat"], "opponent": row["opponent"],
                           "values_binary64": struct.pack(">3d", row["self_reward"], row["opp_reward"], row["margin"]).hex(),
                           "outcome": row["outcome"], "error": row["error"]})
    return sorted(normalized, key=lambda r: (r["tag"], r["seed"], r["seat"], r["opponent"]))


def fixture_config(lab):
    variants = []
    for name, spend in [("SMOKE_KEEPER", 0), ("SMOKE_LIGHT", 1), ("SMOKE_MID", 2), ("CONTROL_SMOKE", 3)]:
        # All files deliberately have the SAME basename and all prebuilt
        # variants have the SAME params={} to exercise the original bugs.
        path = lab / "fixtures" / name / "main.py"
        path.parent.mkdir(parents=True, exist_ok=True)
        actions = [{} for _ in range(720)]
        actions[0] = {"market": [["BUY_SEED", "WHEAT", spend]]}
        path.write_text(emit_source([actions, actions], trim_hands=True))
        if name != "CONTROL_SMOKE":
            variants.append({"name": name, "path": str(path.relative_to(lab)), "params": {}})
    cfg = {"name": "INTEGRATION_ONLY_DO_NOT_PROMOTE", "base": "fixtures/CONTROL_SMOKE/main.py",
           "baseline": "fixtures/CONTROL_SMOKE/main.py", "baseline_name": "CONTROL_SMOKE",
           "include_untouched_base": False, "finals_include_baseline": True,
           "promotion_objective": "balanced", "start_seed": 2026090800,
           "screen_games": 2, "promote_games": 10, "final_games": 2, "top_k": 3,
           "variants": variants}
    path = lab / "pilot-smoke.json"
    path.write_text(json.dumps(cfg, indent=2))
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--work", type=Path, default=ROOT / ".cache/funnel-pilot")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if not 1 <= args.workers <= 4:
        parser.error("pilot is deliberately limited to 1..4 workers")
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    lab, patch_path = prepare(args.source.resolve(), work / "patched")
    subprocess.run([sys.executable, str(HERE / "guard_tests.py"), "--original-lab", str(args.source.resolve() / "kaggriculture_meta_lab"), "--patched-lab", str(lab)], check=True)
    setup_framework(work)
    sweep = load_sweep(lab, "pilot_full_sweep")
    cfg_path = fixture_config(lab)
    cfg = json.loads(cfg_path.read_text())
    configs = sweep.expand_config(cfg)
    projected = sweep.project_game_budget(len(configs), False, 3, 2, 10, 2, True)
    assert len(configs) == 3 and projected["total"] == EXPECTED_FUNNEL_GAMES
    if sweep.rust_backend.rust_binary() is None:
        raise RuntimeError("build rust_port in release before the integration pilot")
    real_python = sweep.run
    real_rust = sweep.rust_backend.run_rust
    report = {"purpose": "integration_only", "agent_promoted": False, "kaggle_submissions": 0,
              "source": json.loads((HERE / "source_manifest.json").read_text()),
              "code_commit": os.environ.get("GITHUB_SHA"), "projected_funnel_games_per_backend": projected,
              "hard_game_cap_per_backend": MAX_PER_BACKEND, "backends": {}}
    old_cwd = Path.cwd()
    # Running from the REPOSITORY root is intentional; relative config paths
    # must not accidentally force a Python fallback or fail in strict Rust.
    os.chdir(ROOT)
    try:
        for mode, execute in (("python", real_python), ("rust", real_rust)):
            spent = 0
            calls = []
            def counted(jobs, workers, **kwargs):
                nonlocal spent
                if spent + len(jobs) > MAX_PER_BACKEND:
                    raise RuntimeError("pilot hard game cap exceeded before execution")
                spent += len(jobs)
                rows = execute(jobs, workers, **kwargs)
                calls.append({"jobs": len(jobs), "rows": normalized_rows(rows)})
                return rows
            command = [str(lab / "scripts/sweep.py"), "--config", str(cfg_path), "--workers", str(args.workers), "--backend", mode, "--max-total-games", "100"]
            start = time.perf_counter()
            with patch.object(sys, "argv", command), patch.object(sweep, "run", counted), patch.object(sweep.rust_backend, "run_rust", counted), redirect_stdout(io.StringIO()) as console:
                status = sweep.main()
            (work / f"{mode}-cli.txt").write_text(console.getvalue())
            assert status == 0 and spent == 96 and [c["jobs"] for c in calls] == [12, 60, 24]
            output = max((lab / "results").glob("sweep-INTEGRATION_ONLY_DO_NOT_PROMOTE-*.json"), key=lambda p:p.stat().st_mtime_ns)
            result = json.loads(output.read_text())
            assert result["variants"] == ["SMOKE_KEEPER", "SMOKE_LIGHT", "SMOKE_MID"]
            assert result["promoted"] == ["SMOKE_KEEPER", "SMOKE_LIGHT", "SMOKE_MID"]
            assert result["finals"]["ranked"] == ["SMOKE_KEEPER", "SMOKE_LIGHT", "SMOKE_MID", "CONTROL_SMOKE"]
            assert all(cell["games"] == 4 for row in result["finals"]["pairwise"].values() for cell in row.values())
            record = {"funnel_games": spent, "funnel_wall_seconds": time.perf_counter()-start,
                      "stages": calls[:], "result": result}

            b21 = lab / "agents/current/agent_v9_b21_s16.py"
            controls = [lab / "agents/current" / filename for filename in ("agent_v7_scripted.py", "agent_v8_aastik.py", "agent_v8_hybrid.py")]
            control_jobs = []
            for control in controls:
                control_jobs += sweep.build_jobs(str(b21), [str(control)], 2, 2026090900, tag=control.stem)
            with redirect_stdout(io.StringIO()):
                controls_rows = counted(control_jobs, args.workers, progress_every=100)
            record["control_games"] = len(control_jobs)
            record["control_rows"] = normalized_rows(controls_rows)
            record["total_games"] = spent
            assert spent == 108
            report["backends"][mode] = record

        python, rust = (report["backends"][name] for name in ("python", "rust"))
        assert python["result"] == rust["result"], "funnel decisions or BT strengths differ"
        assert python["stages"] == rust["stages"], "some game reward/identity differs"
        assert python["control_rows"] == rust["control_rows"], "current-control parity mismatch"
        report["all_stage_rows_and_decisions_identical"] = True
        report["current_control_rows_identical"] = True
        report["total_games_both_backends"] = 216

        # Prove refusal BEFORE any runner call: projected 96 > explicit cap 95.
        def must_not_run(*args, **kwargs):
            raise AssertionError("budget gate ran a game")
        command = [str(lab / "scripts/sweep.py"), "--config", str(cfg_path), "--workers", "1", "--backend", "rust", "--max-total-games", "95"]
        with patch.object(sys, "argv", command), patch.object(sweep, "run", must_not_run), patch.object(sweep.rust_backend, "run_rust", must_not_run), redirect_stdout(io.StringIO()):
            try:
                sweep.main()
            except SystemExit as error:
                assert "refusing projected 96" in str(error)
            else:
                raise AssertionError("budget overflow was not rejected")
        report["budget_rejected_before_execution"] = True
    finally:
        os.chdir(old_cwd)
    report["status"] = "passed"
    report["patch_sha256"] = hashlib.sha256(patch_path.read_bytes()).hexdigest()
    report["scope"] = "synthetic stage-coverage test + 12 frozen-control games per backend, not evidence of a stronger real agent"
    (work / "report.json").write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ("source", "backends")}, indent=2))
    print(json.dumps({mode:{k:record[k] for k in ("funnel_games", "control_games", "total_games", "funnel_wall_seconds")} for mode,record in report["backends"].items()}, indent=2))


if __name__ == "__main__":
    main()
