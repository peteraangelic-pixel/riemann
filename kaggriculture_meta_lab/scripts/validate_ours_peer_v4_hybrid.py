#!/usr/bin/env python3
"""Large disjoint paired gate for the hybrid against both parent champions."""
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
 variants={'hybrid':ROOT/'agents/candidates/ours_peer_v4_hybrid_holdout_winner.py','ours':ROOT/'agents/candidates/v3_market_genetic_holdout_winner.py','peer':ROOT/'agents/candidates/peer_v4_german9_kanno_v3.py'}
 controls={'v3':ROOT/'agents/candidates/top7_kanno_ep107381285_v3_sibling.py','v16':ROOT/'agents/variants/agent_v16_kanno_top7_champion.py','german':ROOT/'agents/candidates/champion_tape_germanjurado1.py','b21':ROOT/'agents/current/agent_v9_b21_s16.py','yusuke':ROOT/'agents/candidates/top7_yusuke_best_ep107377081.py','g2':ROOT/'agents/variants/agent_v10_subin_106845775.py'}
 sv={k:_source(str(p)) for k,p in variants.items()};sc={k:_source(str(p)) for k,p in controls.items()};assert all(sv.values()) and all(sc.values())
 with tempfile.TemporaryDirectory(prefix='hybrid-gate-') as raw:
  td=Path(raw);vp={};cp={};gp=td/'g2.json';gp.write_text(json.dumps({'enabled':True,'start_day':6,'cash_reserve':250,'milk_reserve':1}))
  for k,s in sv.items():p=td/f'v-{k}.json';p.write_text(json.dumps(s.actions));vp[k]=p
  for k,s in sc.items():p=td/f'c-{k}.json';p.write_text(json.dumps(s.actions));cp[k]=p
  jobs=[];meta=[]
  for v in variants:
   for c in controls:
    for seed in range(97000,97256):
     for seat in (0,1):jobs.append(Job(seed,vp[v],cp[c],reverse=bool(seat),overlay_b=gp if c=='g2' else None));meta.append((v,c))
  for parent in ('ours','peer'):
   for seed in range(97000,97256):
    for seat in (0,1):jobs.append(Job(seed,vp['hybrid'],vp[parent],reverse=bool(seat)));meta.append(('direct',parent))
  rows=replay_many(jobs,binary=a.binary,steps=720,threads=a.threads,trim_hands_a=True,trim_hands_b=True,allow_errors=True,timeout=1200);d=defaultdict(list)
  for r,k in zip(rows,meta):
   if r.get('errors') or r.get('rewards') is None:raise RuntimeError(r.get('errors'))
   d[k].append(float(r['rewards'][0])-float(r['rewards'][1]))
 summary={f'{v}:{c}':stat(m) for (v,c),m in d.items()};deltas={p:{c:{'score_rate':summary[f'hybrid:{c}']['score_rate']-summary[f'{p}:{c}']['score_rate'],'mean_margin':summary[f'hybrid:{c}']['mean_margin']-summary[f'{p}:{c}']['mean_margin']} for c in controls} for p in ('ours','peer')}
 direct={p:summary[f'direct:{p}'] for p in ('ours','peer')};passed=all(x['score_rate']>.55 and x['mean_margin']>100 for x in direct.values()) and all(summary[f'hybrid:{c}']['score_rate']>=min(summary[f'ours:{c}']['score_rate'],summary[f'peer:{c}']['score_rate'])-.01 and summary[f'hybrid:{c}']['mean_margin']>=min(summary[f'ours:{c}']['mean_margin'],summary[f'peer:{c}']['mean_margin'])-250 for c in controls)
 out={'format':'ours-peer-v4-hybrid-independent-v1','seeds':[97000,97255],'jobs':len(jobs),'zero_errors':True,'direct':direct,'summary':summary,'deltas':deltas,'passes_strict_gate':passed};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
