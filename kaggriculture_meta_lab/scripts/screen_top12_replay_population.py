#!/usr/bin/env python3
"""Broad fresh-seed screen of every TOP12 replay policy as a structural parent."""
from __future__ import annotations
import argparse,json,statistics,sys
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kaggriculture_lab import rust_backend
from benchmark_top30 import build_top30_jobs

def stat(rows):
 n=len(rows);w=sum(r['margin']>0 for r in rows);l=sum(r['margin']<0 for r in rows)
 return {'games':n,'wins':w,'losses':l,'ties':n-w-l,'score_rate':(w+.5*(n-w-l))/n,
         'mean_reward':statistics.mean(r['self_reward'] for r in rows),'mean_margin':statistics.mean(r['margin'] for r in rows),
         'seat0_wins':sum(r['margin']>0 and r['candidate_seat']==0 for r in rows),'seat1_wins':sum(r['margin']>0 and r['candidate_seat']==1 for r in rows)}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--corpus',type=Path,required=True);ap.add_argument('--template',type=Path,required=True);ap.add_argument('--seeds',type=int,default=2);ap.add_argument('--seed-start',type=int,default=180000);ap.add_argument('--workers',type=int,default=4);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 template,meta=build_top30_jobs(a.corpus.resolve(),a.template.resolve(),12)
 records=[(template[i][2],meta[i]) for i in range(0,len(template),2)]
 # Every selected replay policy becomes a neutral candidate id. Internal provenance is retained for audit only.
 candidates=[]
 for i,(spec,m) in enumerate(records):candidates.append((f'p{i:03d}',spec,m))
 jobs=[];labels=[]
 for cid,spec,provenance in candidates:
  for oid,(opp,ometa) in enumerate(records):
   for seed in range(a.seed_start,a.seed_start+a.seeds):
    for seat in (0,1):
     jobs.append((seed,spec,opp,seat,720,f'{cid}-o{oid:03d}'));labels.append((cid,provenance,ometa,seat))
 rows=rust_backend.run_rust(jobs,a.workers,progress_every=2000)
 enriched=[]
 for r,(cid,prov,opp,seat) in zip(rows,labels):enriched.append({**r,'candidate_id':cid,'candidate_provenance':prov,'opponent_rank':opp['rank'],'opponent_team':opp['team'],'candidate_seat':seat})
 failed=[r for r in enriched if r.get('error')]
 if failed:raise RuntimeError(f'{len(failed)} failed games: {failed[:3]}')
 ranked=[]
 for cid,spec,prov in candidates:
  rr=[r for r in enriched if r['candidate_id']==cid]; ranked.append({'candidate_id':cid,'source_spec':spec,'provenance':prov,**stat(rr)})
 ranked.sort(key=lambda r:(r['wins'],r['mean_reward'],r['mean_margin']),reverse=True)
 out={'format':'top12-replay-parent-population-screen-v1','purpose':'structural parent discovery; not approval to submit another team replay unchanged','seeds':[a.seed_start,a.seed_start+a.seeds-1],'policies':len(records),'jobs':len(jobs),'ranking':ranked,'top_candidate_rows':[r for r in enriched if r['candidate_id'] in {x['candidate_id'] for x in ranked[:12]}]}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(ranked[:20],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
