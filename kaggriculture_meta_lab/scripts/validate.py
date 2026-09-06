"""One-command candidate validation -> writes a COMMITTABLE result file.

Runs the two things that actually decide a mutation:
  1. CLOSED loop: candidate (V8) vs baseline (V7), paired seeds, both seats,
     process-parallel, with the Wilson promotion gate.
  2. OPEN loop: candidate vs the recorded opponents in the replay corpus
     (bundled corpus/sample, or your full online/ folder), on the original seeds.

Writes a human-readable UTF-8 summary to results/validate-<timestamp>.md (this
folder IS tracked in git, unlike reports/*.json), prints it, and exits non-zero
if the closed-loop gate fails.

Examples:
    python scripts/validate.py                       # 20 seeds = 40 closed games
    python scripts/validate.py --games 100 --workers 16
    python scripts/validate.py --corpus ../kaggriculture/online --team "Lauresowe"
"""
from __future__ import annotations

import argparse
import gzip
import json
import statistics
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kaggriculture_lab.stats import aggregate, promotion_gate  # noqa: E402
from kaggriculture_lab.tournament import (  # noqa: E402
    _available_mem_gb, build_jobs, default_workers, run,
)

V8 = "agents/variants/agent_v8_fert.py"
V7 = "agents/ref/agent_v7.py"


def _corpus_job(args):
    replay_path, candidate_spec, team_subs = args
    from kaggriculture_lab.agents import resolve
    from kaggriculture_lab.corpus import load_replay, score_episode
    try:
        cand = resolve(candidate_spec)
        replay = load_replay(Path(replay_path))
        seat = None
        names = replay.get("info", {}).get("TeamNames")
        if names:
            for i, name in enumerate(names):
                if any(t.lower() in str(name).lower() for t in team_subs):
                    seat = i
                    break
        if seat is None:
            seat = 0
        res = score_episode(cand, replay, seat)
        res["episode"] = Path(replay_path).parent.name or Path(replay_path).stem
        return res
    except Exception as exc:  # noqa: BLE001
        return {"episode": str(replay_path), "error": f"{type(exc).__name__}: {exc}"}


def run_corpus(corpus: Path, candidate: str, team: list[str], workers: int, limit: int):
    episodes = sorted(corpus.rglob("replay.json*")) if corpus.exists() else []
    if limit:
        episodes = episodes[:limit]
    if not episodes:
        return None
    jobs = [(str(p), candidate, tuple(team)) for p in episodes]
    out = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(_corpus_job, j) for j in jobs]
        for fut in as_completed(futs):
            try:
                out.append(fut.result())
            except Exception as exc:  # noqa: BLE001
                out.append({"episode": "unknown",
                            "error": f"{type(exc).__name__}: {exc}"})
    good = [r for r in out if not r.get("error")]
    wins = sum(r["outcome"] == "win" for r in good)
    losses = sum(r["outcome"] == "loss" for r in good)
    ties = len(good) - wins - losses
    means = [r["self"] for r in good]
    rec = [r.get("rec_self", 0.0) for r in good]
    return {
        "games": len(good), "errors": len(out) - len(good),
        "wins": wins, "losses": losses, "ties": ties,
        "mean_self": statistics.mean(means) if means else 0.0,
        "median_self": statistics.median(means) if means else 0.0,
        "mean_rec": statistics.mean(rec) if rec else 0.0,
        "episodes": [r["episode"] for r in good],
        "detail": good,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", default=V8)
    ap.add_argument("--baseline", default=V7)
    ap.add_argument("--games", type=int, default=20, help="seeds (x2 seats) for closed loop")
    ap.add_argument("--workers", type=int, default=default_workers())
    ap.add_argument("--start-seed", type=int, default=20262000)
    ap.add_argument("--corpus", default="corpus/sample")
    ap.add_argument("--team", action="append", default=["Lauresowe"])
    ap.add_argument("--corpus-limit", type=int, default=0)
    args = ap.parse_args()

    # each worker pins ~0.3-0.4 GB (env + agent imports); clamp to what RAM
    # can sustain so an over-eager --workers on a small box can't OOM-kill pool
    mem_safe = max(1, int(_available_mem_gb() / 0.45))
    if args.workers > mem_safe:
        print(f"[note] --workers {args.workers} clamped to {mem_safe} "
              f"(~{_available_mem_gb():.1f} GB RAM available; ~0.45 GB/worker)")
        args.workers = mem_safe

    t0 = time.perf_counter()
    lines = []
    def log(s=""):
        print(s)
        lines.append(s)

    log(f"# Validation: {Path(args.candidate).name} vs {Path(args.baseline).name}")
    log(f"workers={args.workers}  closed-loop seeds={args.games} (x2 seats)  "
        f"corpus={args.corpus}")
    log("")

    # ---- closed loop ----
    jobs = build_jobs(args.candidate, [args.baseline], args.games,
                      args.start_seed, swap_seats=True, steps=720)
    log(f"[1/2] Closed loop: {len(jobs)} games ...")
    rows = run(jobs, args.workers, progress_every=max(20, len(jobs) // 4))
    agg = aggregate(rows)
    s0 = aggregate([r for r in rows if r["seat"] == 0])
    s1 = aggregate([r for r in rows if r["seat"] == 1])
    ok, reasons = promotion_gate(agg, min_games=max(20, len(jobs) // 2))
    log("")
    log(f"  {agg.wins}W {agg.losses}L {agg.ties}T  score {agg.score_rate*100:.1f}%  "
        f"95% Wilson {agg.ci_low*100:.1f}-{agg.ci_high*100:.1f}")
    log(f"  mean margin {agg.mean_margin:+,.0f} (median {agg.median_margin:+,.0f}, "
        f"p10 {agg.p10_margin:+,.0f})  errors {agg.errors}")
    log(f"  seat0 {s0.wins}-{s0.losses} margin {s0.mean_margin:+,.0f} | "
        f"seat1 {s1.wins}-{s1.losses} margin {s1.mean_margin:+,.0f}")
    log(f"  GATE: {'PASS' if ok else 'FAIL'} — {' ; '.join(reasons)}")
    log("")

    # ---- open loop ----
    corpus_dir = (ROOT / args.corpus) if not Path(args.corpus).is_absolute() else Path(args.corpus)
    log(f"[2/2] Open-loop corpus: {corpus_dir}")
    corp = run_corpus(corpus_dir, args.candidate, args.team, args.workers, args.corpus_limit)
    if corp:
        log(f"  {corp['wins']}W {corp['losses']}L {corp['ties']}T over {corp['games']} episodes "
            f"(errors {corp['errors']})")
        log(f"  candidate mean cash {corp['mean_self']:,.0f} (median {corp['median_self']:,.0f})")
        log(f"  recorded  mean cash {corp['mean_rec']:,.0f}  "
            f"delta {corp['mean_self']-corp['mean_rec']:+,.0f}")
    else:
        log("  (no replays found)")
    log("")
    log(f"elapsed {time.perf_counter()-t0:.0f}s")

    # ---- write committable result ----
    results_dir = ROOT / "results"
    results_dir.mkdir(exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    out_md = results_dir / f"validate-{stamp}.md"
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    # machine-readable companion (kept; small)
    (results_dir / f"validate-{stamp}.json").write_text(json.dumps({
        "candidate": args.candidate, "baseline": args.baseline,
        "closed_loop": agg.to_dict(), "gate_pass": ok, "gate_reasons": reasons,
        "corpus": {k: v for k, v in (corp or {}).items() if k != "detail"},
        "elapsed_s": time.perf_counter() - t0,
    }, indent=2), encoding="utf-8")
    print(f"\nWrote {out_md}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
