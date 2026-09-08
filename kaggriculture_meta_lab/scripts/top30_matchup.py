"""Run B21 (or another agent) against recorded TOP30 replay opponents.

This is an open-loop diagnostic: the recorded opponent does not react to the
candidate. It is useful for finding market/production divergences, but is not
a closed-loop strength claim.
"""
from __future__ import annotations
import argparse, json, importlib.util, statistics
from pathlib import Path
from kaggriculture_lab.engine import play_game
from kaggriculture_lab.corpus import tape_agent
from kaggriculture_lab.agents import _find_steps

def load_agent(path: Path):
    spec = importlib.util.spec_from_file_location("top30_candidate", path)
    if spec is None or spec.loader is None: raise ImportError(path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return getattr(mod, "act", getattr(mod, "agent"))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path, help="extracted TOP30 directory")
    ap.add_argument("--candidate", type=Path, default=Path("agents/current/agent_v9_b21_s16.py"))
    ap.add_argument("--team", action="append", help="team(s), default all")
    ap.add_argument("--out", type=Path, default=Path("reports/top30_matchups.json"))
    args = ap.parse_args(); candidate = load_agent(args.candidate)
    teams = args.team or sorted(p.name for p in args.source.iterdir() if p.is_dir() and p.name != "per_replay")
    rows=[]
    for team in teams:
        for path in sorted((args.source/team).glob("replay_*.json")):
            replay=json.loads(path.read_text(encoding="utf-8")); steps=_find_steps(replay)
            names=replay.get("info",{}).get("TeamNames",[])
            if team not in names: continue
            seat=names.index(team); opp=tape_agent(steps,1-seat)
            seed=replay.get("info",{}).get("seed") or replay.get("configuration",{}).get("seed") or 0
            a0,a1=(candidate,opp) if seat==0 else (opp,candidate)
            result=play_game(a0,a1,int(seed),steps=len(steps))
            self_reward=result["rewards"][seat]; opp_reward=result["rewards"][1-seat]
            rows.append({"team":team,"replay":path.name,"seat":seat,"seed":seed,
                         "self_reward":self_reward,"opp_reward":opp_reward,
                         "margin":self_reward-opp_reward,
                         "outcome":"W" if self_reward>opp_reward else "L" if self_reward<opp_reward else "T",
                         "error":result.get("error")})
    args.out.parent.mkdir(parents=True,exist_ok=True); args.out.write_text(json.dumps(rows,indent=2)+"\n")
    for team in teams:
        q=[r for r in rows if r["team"]==team]
        if q: print(team,sum(r["outcome"]=="W" for r in q),sum(r["outcome"]=="L" for r in q),round(statistics.mean(r["margin"] for r in q),1))
if __name__ == "__main__": main()
