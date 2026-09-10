#!/usr/bin/env python3
"""Independent fresh-seed validation of peer branch's Kanno episode 107381285."""
from __future__ import annotations
import argparse,json,statistics,sys,tempfile
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'rust_port/tools')]
from kaggriculture_lab.rust_backend import _source
from rust_client import Job,replay_many

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--binary',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--threads',type=int,default=4);a=ap.parse_args()
 candidate=ROOT/'agents/candidates/top7_kanno_ep107381285_v3_sibling.py'
 specs={'v16':ROOT/'agents/variants/agent_v16_kanno_top7_champion.py','german':ROOT/'agents/candidates/champion_tape_germanjurado1.py','b21':ROOT/'agents/current/agent_v9_b21_s16.py','kanno_lower':ROOT/'agents/candidates/top7_kanno_ep107377838.py','yusuke':ROOT/'agents/candidates/top7_yusuke_best_ep107377081.py','himanshu':ROOT/'agents/candidates/top7_himanshu_best_ep107382217.py','g2':ROOT/'agents/variants/agent_v10_subin_106845775.py'}
 cand=_source(str(candidate));opps={k:_source(str(v)) for k,v in specs.items()};assert cand and all(opps.values())
 g2={'enabled':True,'start_day':6,'cash_reserve':250,'milk_reserve':1}
 with tempfile.TemporaryDirectory(prefix='peer-v3-valid-') as raw:
  td=Path(raw);cp=td/'candidate.json';cp.write_text(json.dumps(cand.actions));gp=td/'g2.json';gp.write_text(json.dumps(g2));paths={}
  for i,(name,src) in enumerate(opps.items()):p=td/f'opp-{i}.json';p.write_text(json.dumps(src.actions));paths[name]=p
  jobs=[];meta=[]
  for name in opps:
   for seed in range(90000,90128):
    for seat in (0,1):jobs.append(Job(seed,cp,paths[name],reverse=bool(seat),overlay_b=gp if name=='g2' else None));meta.append(name)
  results=replay_many(jobs,binary=a.binary,steps=720,threads=a.threads,trim_hands_a=True,trim_hands_b=True,allow_errors=True,timeout=900)
 grouped=defaultdict(list)
 for result,name in zip(results,meta):
  if result.get('errors') or result.get('rewards') is None:raise RuntimeError(result.get('errors'))
  grouped[name].append(float(result['rewards'][0])-float(result['rewards'][1]))
 summary={name:{'games':len(m),'wins':sum(x>0 for x in m),'losses':sum(x<0 for x in m),'ties':sum(x==0 for x in m),'score_rate':(sum(x>0 for x in m)+.5*sum(x==0 for x in m))/len(m),'mean_margin':statistics.mean(m),'worst_margin':min(m)} for name,m in grouped.items()}
 out={'format':'peer-v3-sibling-independent-v1','source_branch':'arena/01a087c0-riemann','source_commit':'9cecb65','source_episode':107381285,'seeds':[90000,90127],'jobs':len(jobs),'zero_errors':True,'summary':summary}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
