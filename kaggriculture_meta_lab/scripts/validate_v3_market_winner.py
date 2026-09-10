#!/usr/bin/env python3
"""Independent large fresh gate for the V3 market-evolution winner."""
from __future__ import annotations
import argparse,json,statistics,sys,tempfile
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'rust_port/tools')]
from kaggriculture_lab.rust_backend import _source
from rust_client import Job,replay_many

def stat(m):
 n=len(m);w=sum(x>0 for x in m);l=sum(x<0 for x in m);t=n-w-l
 return {'games':n,'wins':w,'losses':l,'ties':t,'score_rate':(w+.5*t)/n,'mean_margin':statistics.mean(m),'worst_margin':min(m)}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--binary',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--threads',type=int,default=4);a=ap.parse_args()
 variants={'winner':ROOT/'agents/candidates/v3_market_genetic_holdout_winner.py','v3':ROOT/'agents/candidates/top7_kanno_ep107381285_v3_sibling.py'}
 controls={'v16':ROOT/'agents/variants/agent_v16_kanno_top7_champion.py','german':ROOT/'agents/candidates/champion_tape_germanjurado1.py','b21':ROOT/'agents/current/agent_v9_b21_s16.py','yusuke':ROOT/'agents/candidates/top7_yusuke_best_ep107377081.py','himanshu':ROOT/'agents/candidates/top7_himanshu_best_ep107382217.py','g2':ROOT/'agents/variants/agent_v10_subin_106845775.py'}
 srcv={k:_source(str(v)) for k,v in variants.items()};srcc={k:_source(str(v)) for k,v in controls.items()};assert all(srcv.values()) and all(srcc.values())
 with tempfile.TemporaryDirectory(prefix='v3-winner-gate-') as raw:
  td=Path(raw);vp={};cp={};g2=td/'g2.json';g2.write_text(json.dumps({'enabled':True,'start_day':6,'cash_reserve':250,'milk_reserve':1}))
  for k,s in srcv.items():p=td/f'v-{k}.json';p.write_text(json.dumps(s.actions));vp[k]=p
  for k,s in srcc.items():p=td/f'c-{k}.json';p.write_text(json.dumps(s.actions));cp[k]=p
  jobs=[];meta=[]
  for variant in variants:
   for control in controls:
    for seed in range(93000,93256):
     for seat in (0,1):jobs.append(Job(seed,vp[variant],cp[control],reverse=bool(seat),overlay_b=g2 if control=='g2' else None));meta.append((variant,control))
  for seed in range(93000,93256):
   for seat in (0,1):jobs.append(Job(seed,vp['winner'],vp['v3'],reverse=bool(seat)));meta.append(('direct','v3'))
  rows=replay_many(jobs,binary=a.binary,steps=720,threads=a.threads,trim_hands_a=True,trim_hands_b=True,allow_errors=True,timeout=1200)
 grouped=defaultdict(list)
 for r,key in zip(rows,meta):
  if r.get('errors') or r.get('rewards') is None:raise RuntimeError(r.get('errors'))
  grouped[key].append(float(r['rewards'][0])-float(r['rewards'][1]))
 summary={f'{v}:{c}':stat(m) for (v,c),m in grouped.items()};deltas={c:{'score_rate':summary[f'winner:{c}']['score_rate']-summary[f'v3:{c}']['score_rate'],'mean_margin':summary[f'winner:{c}']['mean_margin']-summary[f'v3:{c}']['mean_margin']} for c in controls}
 direct=summary['direct:v3'];passed=direct['score_rate']>.55 and direct['mean_margin']>100 and all(x['score_rate']>=-.01 and x['mean_margin']>=-250 for x in deltas.values())
 out={'format':'v3-market-winner-independent-gate-v1','seeds':[93000,93255],'jobs':len(jobs),'zero_errors':True,'summary':summary,'deltas':deltas,'passes_strict_gate':passed}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
