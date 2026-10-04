#!/usr/bin/env python3
"""Tune bounded state-aware markets on robust refreshed-meta structural tapes."""
from __future__ import annotations
import argparse,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'rust_port/tools'),str(ROOT/'scripts')]
from benchmark_top30 import build_top30_jobs
from generate_market_overlays import generate_profiles
from kaggriculture_lab.rust_backend import _source
from search_v24_live_dynamic_market import live_records,run

def key(v):return v['wins']+.5*v.get('ties',0),v['mean_reward'],v['mean_margin']
def main():
 p=argparse.ArgumentParser();p.add_argument('--corpus',type=Path,required=True);p.add_argument('--live',type=Path,required=True);p.add_argument('--binary',type=Path,required=True);p.add_argument('--threads',type=int,default=4);p.add_argument('--population',type=int,default=500);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 v2=ROOT/'agents/variants/agent_v16_kanno_top7_champion.py';jobs,meta=build_top30_jobs(a.corpus.resolve(),v2,12)
 records=[(jobs[i][2],jobs[i][0],f"rank{meta[i]['rank']:02d}") for i in range(0,len(jobs),2)]
 donors=[]
 for idx in (37,70,97,106):
  src=_source(records[idx][0]);assert src;donors.append((idx,src))
 # Independent seeds against one best-listed source per rank, plus half exact-live.
 best=[];seen=set()
 for i in range(0,len(jobs),2):
  m=meta[i]
  if m['best_listed_submission'] and m['rank'] not in seen:seen.add(m['rank']);best.append((jobs[i][2],220000+i//2,'train-current'))
 live=live_records(a.live);train_records=best+[(s,se,g) for s,se,g in live[::2]]
 profiles=generate_profiles(a.population,20261004);final=[];train_jobs=0
 for di,(idx,src) in enumerate(donors):
  tr,n=run(src,profiles,train_records,a.binary,a.threads);train_jobs+=n
  ids=sorted(tr,key=lambda i:key(tr[i]),reverse=True)[:5];ids=list(dict.fromkeys(ids+[0]))
  final.append((idx,src,tr,ids))
 hold_records=records+live+[(str(v2.resolve()),221000+i,'v2') for i in range(8)]+[(str((ROOT/'agents/candidates/agent_v8_control_g2_open_loop.py').resolve()),221000+i,'g2') for i in range(8)]
 rows=[];hold_jobs=0
 for idx,src,tr,ids in final:
  h,n=run(src,[profiles[i] for i in ids],hold_records,a.binary,a.threads);hold_jobs+=n
  for j,pid in enumerate(ids):rows.append({'donor_index':idx,'profile_index':pid,'profile':profiles[pid],'train':tr[pid],'holdout':h[j]})
 baseline=json.loads((ROOT/'results/v31-new-top12-structural-20261004.json').read_text())['controls']['v2']
 def counts(v,prefix):return sum(q['wins'] for g,q in v['groups'].items() if g.startswith(prefix))
 eligible=[]
 for r in rows:
  v=r['holdout'];
  if key(v)>key(baseline) and counts(v,'rank')>=counts(baseline,'rank')+4 and counts(v,'live-')>=counts(baseline,'live-') and v['groups']['g2']['wins']>=baseline['groups']['g2']['wins']-2:eligible.append(r)
 winner=max(eligible,key=lambda r:key(r['holdout'])) if eligible else None
 report={'format':'v32-structural-market-search-v1','population_per_donor':len(profiles),'donors':[x[0] for x in donors],'train_jobs':train_jobs,'holdout_jobs':hold_jobs,'baseline_v2':baseline,'eligible_count':len(eligible),'winner':winner,'finalists':rows}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'train_jobs':train_jobs,'holdout_jobs':hold_jobs,'eligible_count':len(eligible),'winner':None if winner is None else {'donor':winner['donor_index'],'profile':winner['profile_index'],'summary':winner['holdout']}},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
