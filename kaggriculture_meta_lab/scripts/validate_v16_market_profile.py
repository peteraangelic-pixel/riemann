#!/usr/bin/env python3
"""Fresh-seed native A/B validation of the leading V16 market profile."""
from __future__ import annotations
import argparse,json,statistics,sys,tempfile
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'rust_port/tools')]
from kaggriculture_lab.rust_backend import _source
from rust_client import Job,replay_many

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--binary',type=Path,required=True);ap.add_argument('--screen',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--threads',type=int,default=4);a=ap.parse_args()
 screen=json.load(open(a.screen));profile=screen['retained_top10'][0]['profile']
 specs={'german':ROOT/'agents/candidates/champion_tape_germanjurado1.py','b21':ROOT/'agents/current/agent_v9_b21_s16.py','kanno_lower':ROOT/'agents/candidates/top7_kanno_ep107377838.py','g2':ROOT/'agents/variants/agent_v10_subin_106845775.py'}
 cand=_source(str(ROOT/'agents/variants/agent_v16_kanno_top7_champion.py'));opps={k:_source(str(v)) for k,v in specs.items()};g2={'enabled':True,'start_day':6,'cash_reserve':250,'milk_reserve':1}
 with tempfile.TemporaryDirectory(prefix='v16-market-valid-') as raw:
  td=Path(raw);cp=td/'candidate.json';cp.write_text(json.dumps(cand.actions));pp=td/'candidate-profile.json';pp.write_text(json.dumps(profile));paths={};g2p=td/'g2.json';g2p.write_text(json.dumps(g2))
  for i,(name,src) in enumerate(opps.items()):p=td/f'opp-{i}.json';p.write_text(json.dumps(src.actions));paths[name]=p
  jobs=[];meta=[]
  for variant,overlay in [('baseline',None),('profile',pp)]:
   for name in opps:
    for seed in range(86000,86128):
     for seat in (0,1):jobs.append(Job(seed,cp,paths[name],reverse=bool(seat),overlay_a=overlay,overlay_b=g2p if name=='g2' else None));meta.append((variant,name))
  results=replay_many(jobs,binary=a.binary,steps=720,threads=a.threads,trim_hands_a=True,trim_hands_b=True,allow_errors=True,timeout=900)
 grouped=defaultdict(list)
 for result,key in zip(results,meta):
  if result.get('errors') or result.get('rewards') is None:raise RuntimeError(result.get('errors'))
  grouped[key].append(float(result['rewards'][0])-float(result['rewards'][1]))
 summary={}
 for (variant,name),m in grouped.items():summary[f'{variant}:{name}']={'games':len(m),'wins':sum(x>0 for x in m),'losses':sum(x<0 for x in m),'ties':sum(x==0 for x in m),'score_rate':(sum(x>0 for x in m)+.5*sum(x==0 for x in m))/len(m),'mean_margin':statistics.mean(m),'worst_margin':min(m)}
 deltas={name:{'score_rate':summary[f'profile:{name}']['score_rate']-summary[f'baseline:{name}']['score_rate'],'mean_margin':summary[f'profile:{name}']['mean_margin']-summary[f'baseline:{name}']['mean_margin']} for name in opps}
 out={'format':'v16-market-profile-fresh-ab-v1','profile':profile,'seeds':[86000,86127],'jobs':len(jobs),'summary':summary,'deltas':deltas,'passes_strict_gate':all(d['score_rate']>=0 and d['mean_margin']>=-250 for d in deltas.values()) and statistics.mean(d['mean_margin'] for d in deltas.values())>100}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
