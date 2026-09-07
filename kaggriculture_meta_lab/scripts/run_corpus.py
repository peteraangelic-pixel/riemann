"""Open-loop benchmark against a corpus of real elite replays.

Runs a candidate vs each replay's recorded opponent (in the original seed/seat).
With the *submitted* agent this reproduces Kaggle scores; with a candidate it
shows the change against realistic market pressure. Shard with --shard/--shards
for parallel CI jobs.

    python scripts/run_corpus.py --candidate agents/ref/agent_v7.py \
        --corpus corpus/sample --team "Lauresowe" --workers 8
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kaggriculture_lab.corpus import iter_episodes, load_replay, score_episode  # noqa: E402


def _worker_init() -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))


def _job(args):
    replay_path, candidate_spec, team_substrings = args
    try:
        from kaggriculture_lab.agents import resolve
        cand = resolve(candidate_spec)
        replay = load_replay(Path(replay_path))
        # seat: our team if identifiable, else seat 0
        seat = None
        names = replay.get("info", {}).get("TeamNames")
        if names:
            for i, name in enumerate(names):
                if any(t.lower() in str(name).lower() for t in team_substrings):
                    seat = i
                    break
        if seat is None:
            seat = 0
        res = score_episode(cand, replay, seat)
        res["episode"] = Path(replay_path).parent.name
        return res
    except Exception as exc:
        return {"episode": Path(replay_path).parent.name, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--corpus", default="corpus/sample")
    ap.add_argument("--team", action="append", default=["Lauresowe"],
                    help="team-name substring identifying our seat (repeatable)")
    ap.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 4))
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--shards", type=int, default=1)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    episodes = list(iter_episodes(ROOT / args.corpus))
    episodes = episodes[args.shard::args.shards]
    if args.limit:
        episodes = episodes[: args.limit]
    if not episodes:
        print(f"No replays under {args.corpus}")
        return 1

    jobs = [(str(p), args.candidate, tuple(args.team)) for p in episodes]
    t0 = time.perf_counter()
    results = []
    with ProcessPoolExecutor(max_workers=args.workers, initializer=_worker_init) as pool:
        for fut in as_completed([pool.submit(_job, j) for j in jobs]):
            results.append(fut.result())

    good = [r for r in results if not r.get("error")]
    wins = sum(r["outcome"] == "win" for r in good)
    losses = sum(r["outcome"] == "loss" for r in good)
    ties = len(good) - wins - losses
    means = [r["self"] for r in good]
    rec = [r.get("rec_self", 0.0) for r in good]
    print(f"\ncorpus={args.corpus} shard={args.shard}/{args.shards} games={len(good)} "
          f"(errors {len(results)-len(good)})")
    print(f"  W/L/T: {wins}/{losses}/{ties}")
    if means:
        print(f"  candidate mean cash: {statistics.mean(means):,.0f} "
              f"(median {statistics.median(means):,.0f})")
        print(f"  recorded  mean cash: {statistics.mean(rec):,.0f}")
        print(f"  delta vs recorded:  {statistics.mean(means)-statistics.mean(rec):+,.0f}")
        # exact-reproduction check: candidate should match recorded if it IS the submitted agent
        exact = sum(abs(r["self"] - r.get("rec_self", -1)) < 1.0 for r in good)
        print(f"  episodes reproducing recorded score exactly: {exact}/{len(good)}")
    out = {"candidate": args.candidate, "corpus": args.corpus, "shard": args.shard,
           "elapsed": time.perf_counter() - t0,
           "wins": wins, "losses": losses, "ties": ties,
           "mean_self": statistics.mean(means) if means else 0,
           "mean_rec": statistics.mean(rec) if rec else 0,
           "results": results}
    (ROOT / "reports").mkdir(exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    (ROOT / "reports" / f"corpus-{stamp}.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"elapsed {out['elapsed']:.0f}s -> reports/corpus-{stamp}.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
