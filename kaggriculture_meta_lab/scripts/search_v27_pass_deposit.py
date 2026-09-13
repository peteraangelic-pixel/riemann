#!/usr/bin/env python3
"""Search a prefix-safe V2 logistics overlay on live, TOP12, G2, and V2 cohorts."""
from __future__ import annotations
import argparse,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'rust_port/tools'),str(ROOT/'scripts')]
from benchmark_top30 import build_top30_jobs
from kaggriculture_lab.rust_backend import _source
from search_v24_live_dynamic_market import live_records,run

def profiles():
 out=[{'enabled':False}]
 for day in (0,5,10,15,20,24,27):
  for qty in (1,2,3,5,8,13,21,34,55):
   out.append({'enabled':True,'pass_deposit_start_day':day,'pass_deposit_min_qty':qty})
 return out

def cohort(spec,name,seeds):return [(spec,seed,name) for seed in seeds]
def key(v):return v['wins'],v['mean_reward'],v['mean_margin']
def promotion(v):
 groups=v['groups'];live=[q for g,q in groups.items() if g.startswith('live-')]
 return (sum(q['wins'] for q in live),groups['current-top12']['wins'],groups['g2']['wins'],
         groups['v2']['wins'],statistics.mean(q['mean_reward'] for q in live),v['mean_reward'])
def main():
 p=argparse.ArgumentParser();p.add_argument('--live',type=Path,required=True);p.add_argument('--corpus',type=Path,required=True);p.add_argument('--binary',type=Path,required=True);p.add_argument('--threads',type=int,default=4);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 base_path=ROOT/'agents/variants/agent_v16_kanno_top7_champion.py';g2=str((ROOT/'agents/candidates/agent_v8_control_g2_open_loop.py').resolve());v2=str(base_path.resolve())
 base=_source(v2);assert base;ps=profiles();live=live_records(a.live)
 train_records=live[::2]+cohort(g2,'g2',range(200000,200004))+cohort(v2,'v2',range(200000,200004))
 train,tj=run(base,ps,train_records,a.binary,a.threads);finalists=sorted(train,key=lambda i:key(train[i]),reverse=True)[:16];finalists=list(dict.fromkeys(finalists+[0]))
 jobs,_=build_top30_jobs(a.corpus.resolve(),base_path,12);current=[(jobs[i][2],jobs[i][0],'current-top12') for i in range(0,len(jobs),2)]
 hold_records=live[1::2]+current+cohort(g2,'g2',range(201000,201012))+cohort(v2,'v2',range(201000,201012))
 hold,hj=run(base,[ps[i] for i in finalists],hold_records,a.binary,a.threads);mapped={finalists[i]:v for i,v in hold.items()};baseline=mapped[0];bp=promotion(baseline)
 eligible=[]
 for i,v in mapped.items():
  if i==0:continue
  vp=promotion(v);groups=v['groups'];bg=baseline['groups']
  no_material_regression=all(groups[g]['wins']>=bg[g]['wins']-2 for g in ('current-top12','g2','v2'))
  if no_material_regression and vp>bp and v['wins']>=baseline['wins']+2:eligible.append(i)
 winner=max(eligible,key=lambda i:promotion(mapped[i])) if eligible else 0
 report={'format':'v27-pass-deposit-search-v1','profiles':len(ps),'live_records':len(live),'train_jobs':tj,'holdout_jobs':hj,'finalists':finalists,'baseline':baseline,'baseline_promotion':bp,'winner':winner,'winner_profile':ps[winner],'winner_holdout':mapped[winner],'winner_promotion':promotion(mapped[winner]),'top_train':[{'index':i,'profile':ps[i],'summary':train[i]} for i in sorted(train,key=lambda i:key(train[i]),reverse=True)[:24]],'holdout':[{'index':i,'profile':ps[i],'promotion':promotion(mapped[i]),'summary':mapped[i]} for i in finalists]}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('profiles','live_records','train_jobs','holdout_jobs','winner','winner_profile','baseline_promotion','winner_promotion')},indent=2))
if __name__=='__main__':main()
