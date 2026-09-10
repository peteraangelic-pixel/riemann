#!/usr/bin/env python3
"""Matched fresh-seed TOP15 stress test for V16, V3, V4 and V5."""
from __future__ import annotations
import argparse,json,statistics,sys
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kaggriculture_lab import rust_backend
from benchmark_top30 import build_top30_jobs

def stat(rows):
 n=len(rows);w=sum(r['margin']>0 for r in rows);l=sum(r['margin']<0 for r in rows);t=n-w-l
 return {'games':n,'wins':w,'losses':l,'ties':t,'score_rate':(w+.5*t)/n,'mean_margin':statistics.mean(r['margin'] for r in rows),'mean_candidate_reward':statistics.mean(r['self_reward'] for r in rows),'mean_tape_reward':statistics.mean(r['opp_reward'] for r in rows),'errors':sum(bool(r.get('error')) for r in rows)}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--corpus',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--workers',type=int,default=4);ap.add_argument('--seeds',type=int,default=8);a=ap.parse_args()
 candidates={'v16':ROOT/'agents/variants/agent_v16_kanno_top7_champion.py','v3':ROOT/'agents/candidates/top7_kanno_ep107381285_v3_sibling.py','v4':ROOT/'agents/candidates/peer_v4_german9_kanno_v3.py','v5':ROOT/'agents/candidates/peer_v5_evolved.py'}
 template,meta=build_top30_jobs(a.corpus.resolve(),candidates['v16'].resolve(),15);records=[]
 for i in range(0,len(template),2):records.append((template[i][2],meta[i]))
 jobs=[];labels=[]
 for cname,cpath in candidates.items():
  for rid,(opp,m) in enumerate(records):
   for seed in range(101000,101000+a.seeds):
    for seat in (0,1):jobs.append((seed,str(cpath.resolve()),opp,seat,720,f'{cname}-r{rid}'));labels.append((cname,m))
 rows=rust_backend.run_rust(jobs,a.workers)
 enriched=[]
 for row,(c,m) in zip(rows,labels):enriched.append({**row,'candidate':c,'rank':m['rank'],'team':m['team'],'best_listed_submission':m['best_listed_submission'],'source_episode_id':m['episode_id']})
 if any(r.get('error') for r in enriched):raise RuntimeError(f"{sum(bool(r.get('error')) for r in enriched)} failed games")
 summary={}
 for c in candidates:
  cr=[r for r in enriched if r['candidate']==c];summary[c]={}
  for limit in (5,10,15):
   selected=[r for r in cr if r['rank']<=limit];best=[r for r in selected if r['best_listed_submission']]
   summary[c][f'top{limit}']={'all_selected':stat(selected),'best_listed_only':stat(best),'teams':len({r['team'] for r in selected})}
 # Matched paired deltas use identical team tape, seed and physical seat ordering.
 paired={}
 byc={c:[r for r in enriched if r['candidate']==c] for c in candidates}
 for a1 in candidates:
  for b1 in candidates:
   if a1>=b1:continue
   d=[x['margin']-y['margin'] for x,y in zip(byc[a1],byc[b1])]
   paired[f'{a1}-minus-{b1}']={'games':len(d),'better':sum(x>0 for x in d),'worse':sum(x<0 for x in d),'equal':sum(x==0 for x in d),'mean_margin_delta':statistics.mean(d),'mean_reward_delta':statistics.mean(x['self_reward']-y['self_reward'] for x,y in zip(byc[a1],byc[b1]))}
 out={'format':'champions-top15-fresh-matched-v1','mode':'all 180 selected TOP15 policy tapes; 8 common fresh seeds; candidate both seats','seeds':[101000,101000+a.seeds-1],'jobs':len(jobs),'candidates':{k:str(v.relative_to(ROOT)) for k,v in candidates.items()},'summary':summary,'paired':paired,'rows':enriched};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'jobs':len(jobs),'summary':summary,'paired':paired},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
