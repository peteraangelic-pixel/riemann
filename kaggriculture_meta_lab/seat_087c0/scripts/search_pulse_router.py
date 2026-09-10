#!/usr/bin/env python3
"""Search shallow fail-closed state gates for the isolated t153 fertilizer pulse."""
from __future__ import annotations
import argparse, json, statistics, sys, tempfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "rust_port/tools")]
from benchmark_top30 import build_top30_jobs
from kaggriculture_lab.rust_backend import _source
from rust_client import Job, replay_many


def profiles():
    base = {"enabled": True, "pulse_turn": 153, "pulse_fertilizer_qty": 3}
    out = [("identity", {"enabled": True})]
    money = [100, 250, 500, 750, 1000, 1500, 2500, 4000, 7000, 12000, 20000]
    inv = [9900, 9950, 9980, 10000, 10020, 10050, 10100]
    for own in (1, 2, 3):
        for x in money:
            out.append((f"money-ge-{x}-own{own}", {**base, "pulse_opponent_money_min": x, "pulse_own_fertilizer_min": own}))
            out.append((f"money-le-{x}-own{own}", {**base, "pulse_opponent_money_max": x, "pulse_own_fertilizer_min": own}))
        for x in inv:
            out.append((f"inv-ge-{x}-own{own}", {**base, "pulse_market_inventory_min": x, "pulse_own_fertilizer_min": own}))
            out.append((f"inv-le-{x}-own{own}", {**base, "pulse_market_inventory_max": x, "pulse_own_fertilizer_min": own}))
        # Depth-2 trees: one money bound AND one market-inventory bound.
        for m in money[2::2]:
            for iv in inv[1::2]:
                out.append((f"mge{m}-ige{iv}-o{own}", {**base, "pulse_opponent_money_min": m, "pulse_market_inventory_min": iv, "pulse_own_fertilizer_min": own}))
                out.append((f"mle{m}-ile{iv}-o{own}", {**base, "pulse_opponent_money_max": m, "pulse_market_inventory_max": iv, "pulse_own_fertilizer_min": own}))
    return out


def stat(rows):
    margins = [a-b for a,b in rows]
    w = sum(x > 0 for x in margins); t = sum(x == 0 for x in margins); n = len(rows)
    return {"games": n, "wins": w, "losses": n-w-t, "ties": t,
            "score_rate": (w+.5*t)/n, "mean_reward": statistics.mean(a for a,_ in rows),
            "mean_margin": statistics.mean(margins)}


def evaluate(pool, candidate, opponents, seeds, binary, threads, directory):
    jobs=[]; labels=[]
    for name, profile in pool:
        pp=directory/(name+".json"); pp.write_text(json.dumps(profile))
        for team, op in opponents:
            for seed in seeds:
                for reverse in (False, True):
                    jobs.append(Job(seed, candidate, op, reverse=reverse, overlay_a=pp)); labels.append((name,team))
    rows=replay_many(jobs,binary=binary,steps=720,threads=threads,trim_hands_a=True,
                     trim_hands_b=False,allow_errors=True,timeout=1500)
    grouped=defaultdict(list)
    for row,key in zip(rows,labels):
        if row.get("errors") or row.get("rewards") is None: raise RuntimeError(row.get("errors"))
        grouped[key].append(tuple(map(float,row["rewards"])))
    teams=list(dict.fromkeys(t for t,_ in opponents)); result=[]
    for name,profile in pool:
        team_stats={t:stat(grouped[(name,t)]) for t in teams}; allrows=sum((grouped[(name,t)] for t in teams),[])
        result.append({"name":name,"profile":profile,**stat(allrows),"teams":team_stats})
    identity=next(x for x in result if x["name"]=="identity")
    for x in result:
        deltas=[x["teams"][t]["score_rate"]-identity["teams"][t]["score_rate"] for t in teams]
        x["regressed_teams"]=sum(d < 0 for d in deltas)
        x["worst_team_delta"]=min(deltas)
        x["fitness"]=[-x["regressed_teams"],x["worst_team_delta"],x["score_rate"],x["mean_reward"],x["mean_margin"]]
    return sorted(result,key=lambda x:x["fitness"],reverse=True),len(jobs)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--corpus",type=Path,required=True); ap.add_argument("--binary",type=Path,required=True)
    ap.add_argument("--candidate",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); ap.add_argument("--threads",type=int,default=4)
    a=ap.parse_args(); template,meta=build_top30_jobs(a.corpus.resolve(),a.candidate.resolve(),99)
    with tempfile.TemporaryDirectory(prefix="pulse-router-") as raw:
        td=Path(raw); cand=td/"candidate.json"; cand.write_text(json.dumps(_source(str(a.candidate.resolve())).actions))
        opponents=[]
        for i in range(0,len(template),2):
            src=_source(template[i][2]); p=td/f"opp-{i//2}.json"; p.write_text(json.dumps(src.actions)); opponents.append((meta[i]["team"],p))
        screen,j1=evaluate(profiles(),cand,opponents,range(136000,136002),a.binary,a.threads,td)
        finalists=[("identity",{"enabled":True})]
        for x in screen:
            if x["name"]!="identity" and len(finalists)<25: finalists.append((x["name"],x["profile"]))
        hold,j2=evaluate(finalists,cand,opponents,range(137000,137008),a.binary,a.threads,td)
    report={"format":"pulse-router-search-v1","policies":len(opponents),"screen_seeds":[136000,136001],"holdout_seeds":[137000,137007],
            "total_jobs":j1+j2,"screen_top":screen[:40],"holdout":hold,"winner":hold[0]}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"total_jobs":j1+j2,"winner":hold[0],"holdout_top":hold[:8]},indent=2)[:30000])
if __name__=="__main__": main()
