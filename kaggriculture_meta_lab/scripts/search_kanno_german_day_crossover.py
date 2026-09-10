#!/usr/bin/env python3
"""Rust screen of coherent day-level crossovers between Kanno V16 and German V15.

The search swaps complete 24-turn days, never individual market/unit fields.  A
fresh holdout and per-opponent regression guard prevent a train-only winner from
being emitted.  This is static-policy research; full G2 validation remains a
separate promotion gate.
"""
from __future__ import annotations

import argparse
import base64
import json
import math
import random
import statistics
import sys
import tempfile
import zlib
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "rust_port/tools")]
from kaggriculture_lab.rust_backend import _source  # noqa: E402
from rust_client import Job, replay_many  # noqa: E402


def masks(population: int, seed: int) -> list[tuple[bool, ...]]:
    rng = random.Random(seed); out = [(False,) * 30, (True,) * 30]; seen = set(out)
    for cut in range(1, 30):
        for value in ((False,) * cut + (True,) * (30-cut),
                      (True,) * cut + (False,) * (30-cut)):
            if value not in seen: seen.add(value); out.append(value)
    while len(out) < population:
        value = [False] * 30
        for day in rng.sample(range(30), rng.randint(1, 10)): value[day] = True
        value = tuple(value)
        if value not in seen: seen.add(value); out.append(value)
    return out[:population]


def crossover(kanno, german, mask):
    return [[(german.actions[seat] if mask[min(step // 24, 29)] else kanno.actions[seat])[step]
             for step in range(min(len(kanno.actions[seat]), len(german.actions[seat])))]
            for seat in range(2)]


def summarize(results, owners, opponent_names):
    grouped = defaultdict(lambda: defaultdict(list))
    for result, owner, opponent in zip(results, owners, opponent_names):
        errors = result.get("errors") or []
        rewards = result.get("rewards")
        if errors or rewards is None: raise RuntimeError(f"native game failed: {errors}")
        grouped[owner][opponent].append(float(rewards[0]) - float(rewards[1]))
    summaries = {}
    for owner, by_opp in grouped.items():
        controls = {}
        for opponent, margins in by_opp.items():
            controls[opponent] = {"games": len(margins), "wins": sum(x > 0 for x in margins),
                                  "losses": sum(x < 0 for x in margins), "ties": sum(x == 0 for x in margins),
                                  "score_rate": (sum(x > 0 for x in margins) + .5 * sum(x == 0 for x in margins)) / len(margins),
                                  "mean_margin": statistics.mean(margins), "worst_margin": min(margins)}
        summaries[owner] = {"controls": controls,
                            "worst_score_rate": min(x["score_rate"] for x in controls.values()),
                            "mean_score_rate": statistics.mean(x["score_rate"] for x in controls.values()),
                            "mean_margin": statistics.mean(x["mean_margin"] for x in controls.values())}
    return summaries


def rank_key(summary):
    return summary["worst_score_rate"], summary["mean_score_rate"], summary["mean_margin"]


def run_phase(tapes, opponents, seeds, binary, threads):
    with tempfile.TemporaryDirectory(prefix="kg-day-cross-") as td:
        td = Path(td); candidate_paths=[]; opponent_paths=[]
        for i,tape in enumerate(tapes):
            p=td/f"candidate-{i}.json";p.write_text(json.dumps(tape));candidate_paths.append(p)
        for i,(_,source) in enumerate(opponents):
            p=td/f"opponent-{i}.json";p.write_text(json.dumps(source.actions));opponent_paths.append(p)
        jobs=[];owners=[];names=[]
        for owner,path in enumerate(candidate_paths):
            for oi,(name,source) in enumerate(opponents):
                for seed in seeds:
                    for seat in (0,1):
                        jobs.append(Job(seed,path,opponent_paths[oi],reverse=bool(seat)))
                        owners.append(owner);names.append(name)
        results=replay_many(jobs,binary=binary,steps=720,threads=threads,
                            trim_hands_a=True,trim_hands_b=True,allow_errors=True,timeout=900)
    return summarize(results,owners,names),len(jobs)


def write_agent(path: Path, actions) -> None:
    payload=base64.b85encode(zlib.compress(json.dumps(actions,separators=(",",":")).encode(),9)).decode()
    source='''# Generated day-level Kanno/German crossover; holdout-qualified laboratory candidate.\nimport base64, copy, json, zlib\nACTIONS=json.loads(zlib.decompress(base64.b85decode(%r)))\ndef agent(observation, configuration):\n    p = int(observation.get("player", 0))\n    step = min(int(observation.get("step", 0)), len(ACTIONS[p]) - 1)\n    action = copy.deepcopy(ACTIONS[p][step])\n    action["hands"] = action.get("hands", [])[:len(observation["farms"][p]["hands"])]\n    return action\nact=agent\n''' % payload
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(source)


def main() -> int:
    ap=argparse.ArgumentParser();ap.add_argument("--binary",type=Path,required=True);ap.add_argument("--population",type=int,default=256)
    ap.add_argument("--seed",type=int,default=20260910);ap.add_argument("--threads",type=int,default=4);ap.add_argument("--output",type=Path,required=True);ap.add_argument("--agent-output",type=Path,required=True);args=ap.parse_args()
    refs={
      "kanno":ROOT/"agents/candidates/top7_kanno_bestsub_ep107384200.py",
      "german":ROOT/"agents/candidates/champion_tape_germanjurado1.py",
      "b21":ROOT/"agents/current/agent_v9_b21_s16.py",
      "german_alt":ROOT/"agents/candidates/champion_tape_germanjurado1_ep107212592.py",
      "kanno_lower":ROOT/"agents/candidates/top7_kanno_ep107377838.py"}
    sources={name:_source(str(path)) for name,path in refs.items()}
    if any(v is None for v in sources.values()): raise SystemExit("all search policies must be audited static tapes")
    mm=masks(args.population,args.seed);tapes=[crossover(sources["kanno"],sources["german"],m) for m in mm]
    opponents=[(n,sources[n]) for n in ("german","b21","german_alt","kanno_lower")]
    train,train_jobs=run_phase(tapes,opponents,range(80000,80008),args.binary,args.threads)
    finalists=sorted(train,key=lambda i:rank_key(train[i]),reverse=True)[:16]
    hold_tapes=[tapes[i] for i in finalists]
    hold,hold_jobs=run_phase(hold_tapes,opponents,range(81000,81032),args.binary,args.threads)
    mapped={finalists[i]:summary for i,summary in hold.items()};baseline=mapped.get(0)
    if baseline is None:
        # Always evaluate the pure Kanno parent on holdout for an exact gate.
        extra,jobs=run_phase([tapes[0]],opponents,range(81000,81032),args.binary,args.threads);baseline=extra[0];hold_jobs+=jobs
    eligible=[]
    for index,summary in mapped.items():
        if index==0:continue
        no_regression=all(summary["controls"][name]["score_rate"] >= baseline["controls"][name]["score_rate"]-.03 for name,_ in opponents)
        if no_regression and rank_key(summary)>rank_key(baseline):eligible.append(index)
    winner=max(eligible,key=lambda i:rank_key(mapped[i])) if eligible else 0
    emitted=winner!=0
    if emitted:write_agent(args.agent_output,tapes[winner])
    elif args.agent_output.exists():args.agent_output.unlink()
    report={"format":"kaggriculture-day-crossover-search-v1","population":len(tapes),"mask_seed":args.seed,
            "true_means_german_day":True,"train_seeds":[80000,80007],"holdout_seeds":[81000,81031],
            "opponents":[n for n,_ in opponents],"train_jobs":train_jobs,"holdout_jobs":hold_jobs,
            "finalists":finalists,"baseline_holdout":baseline,"winner_index":winner,"winner_mask":"".join("G" if x else "K" for x in mm[winner]),
            "winner_holdout":mapped.get(winner,baseline),"emitted":emitted,
            "top_train":[{"index":i,"mask":"".join("G" if x else "K" for x in mm[i]),"summary":train[i]} for i in sorted(train,key=lambda i:rank_key(train[i]),reverse=True)[:20]],
            "holdout":[{"index":i,"mask":"".join("G" if x else "K" for x in mm[i]),"summary":mapped[i]} for i in finalists]}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:report[k] for k in ("population","train_jobs","holdout_jobs","winner_index","winner_mask","emitted")},indent=2))
    return 0

if __name__=="__main__":raise SystemExit(main())
