#!/usr/bin/env python3
"""Closed-loop Python gate for V18 observable routers on positive/negative teams."""
import argparse,json,statistics,sys
from collections import defaultdict
from pathlib import Path
from kaggle_environments import make
META=Path(__file__).resolve().parents[2];sys.path.insert(0,str(META))
from kaggriculture_lab.agents import resolve
from scripts.benchmark_top30 import build_top30_jobs
TARGET={'SpaTaro','Otter Vibe','c0nrad'}
NEGATIVE={'mtmr_s1','redblackbst','feel the agi'}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--corpus',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--seed',type=int,default=198000);ap.add_argument('--candidate',action='append',required=True);a=ap.parse_args()
 cs={};
 for x in a.candidate:
  n,p=x.split('=',1);cs[n]=str(Path(p).resolve())
 template,meta=build_top30_jobs(a.corpus.resolve(),Path(next(iter(cs.values()))),12)
 # one best-listed replay per selected team, independent fresh simulation seed
 rec=[];seen=set()
 for i in range(0,len(template),2):
  m=meta[i]
  if m['team'] not in TARGET|NEGATIVE or m['team'] in seen or not m['best_listed_submission']:continue
  seen.add(m['team']);rec.append((template[i][2],m))
 rows=[]
 for name,path in cs.items():
  for j,(opp_spec,m) in enumerate(rec):
   for seat in (0,1):
    cand=resolve(path);opp=resolve(opp_spec);agents=[cand,opp] if seat==0 else [opp,cand]
    env=make('kaggriculture',configuration={'episodeSteps':720,'seed':a.seed},debug=False);env.run(agents)
    rr=[env.state[x].reward for x in range(2)];rc,ro=(rr[0],rr[1]) if seat==0 else (rr[1],rr[0])
    rows.append({'candidate':name,'team':m['team'],'class':'target' if m['team'] in TARGET else 'negative','seat':seat,'self_reward':rc,'opp_reward':ro,'margin':rc-ro,'outcome':'W' if rc>ro else ('L' if rc<ro else 'T')})
 def stat(z):return {'games':len(z),'wins':sum(x['margin']>0 for x in z),'losses':sum(x['margin']<0 for x in z),'mean_margin':statistics.mean(x['margin'] for x in z),'mean_reward':statistics.mean(x['self_reward'] for x in z)}
 summary={n:{k:stat([r for r in rows if r['candidate']==n and (k=='all' or r['class']==k)]) for k in ('target','negative','all')} for n in cs}
 out={'format':'v18-observable-router-targeted-gate-v1','seed':a.seed,'teams':sorted(seen),'summary':summary,'rows':rows};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
