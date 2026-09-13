#!/usr/bin/env python3
"""Fresh fail-closed gate for a reactive imitation candidate versus V2."""
from __future__ import annotations
import argparse,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from benchmark_top30 import build_top30_jobs
from kaggriculture_lab.stats import aggregate
from kaggriculture_lab.tournament import run
from search_v24_live_dynamic_market import live_records

def summarize(rows):
 a=aggregate(rows)
 return {'games':a.games,'wins':a.wins,'losses':a.losses,'ties':a.ties,'errors':a.errors,'score_rate':a.score_rate,'mean_reward':statistics.mean(r['self_reward'] for r in rows if not r['error']),'mean_margin':a.mean_margin}
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--live',type=Path,required=True);p.add_argument('--corpus',type=Path,required=True);p.add_argument('--workers',type=int,default=4);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 v2=str((ROOT/'agents/variants/agent_v16_kanno_top7_champion.py').resolve());g2=str((ROOT/'agents/candidates/agent_v8_control_g2_open_loop.py').resolve());candidate=str(a.candidate.resolve())
 template,meta=build_top30_jobs(a.corpus.resolve(),Path(v2),12);chosen=[];seen=set()
 for i in range(0,len(template),2):
  m=meta[i];key=m['rank']
  if m['best_listed_submission'] and key not in seen:seen.add(key);chosen.append((template[i][0],template[i][2],'current-top12'))
 records=chosen+live_records(a.live)+[(202000+i,g2,'g2') for i in range(8)]+[(202000+i,v2,'v2') for i in range(8)]
 jobs=[]
 for label,spec in [('candidate',candidate),('control',v2)]:
  for seed,opp,group in records:
   # live_records returns (spec, seed, group), unlike our compact tuples.
   if isinstance(seed,str):seed,opp=opp,seed
   for seat in (0,1):jobs.append((int(seed),spec,opp,seat,720,f'{label}|{group}'))
 rows=run(jobs,a.workers,progress_every=50)
 if any(r.get('error') for r in rows):raise RuntimeError(f"gate has {sum(bool(r.get('error')) for r in rows)} failed games")
 report={'format':'v28-state-imitation-gate-v1','records':len(records),'jobs':len(jobs),'policies':{}}
 for label in ('candidate','control'):
  selected=[r for r in rows if r['tag'].startswith(label+'|')];groups={}
  for group in sorted({r['tag'].split('|',1)[1] for r in selected}):groups[group]=summarize([r for r in selected if r['tag']==f'{label}|{group}'])
  report['policies'][label]={'all':summarize(selected),'groups':groups}
 c=report['policies']['candidate'];b=report['policies']['control'];report['promotion']={'wins_delta':c['all']['wins']-b['all']['wins'],'reward_delta':c['all']['mean_reward']-b['all']['mean_reward'],'margin_delta':c['all']['mean_margin']-b['all']['mean_margin'],'passes':c['all']['wins']>=b['all']['wins']+4 and c['groups']['current-top12']['wins']>=b['groups']['current-top12']['wins'] and c['groups']['g2']['wins']>=b['groups']['g2']['wins']-1 and c['groups']['v2']['wins']>=8}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
