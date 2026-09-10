#!/usr/bin/env python3
"""Large matched cross-corpus gate for preselected shallow pulse rules."""
from __future__ import annotations
import argparse,json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'rust_port/tools'),str(Path(__file__).parent)]
from benchmark_top30 import build_top30_jobs
from kaggriculture_lab.rust_backend import _source
from search_pulse_router import evaluate

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--top7',type=Path,required=True);ap.add_argument('--top15',type=Path,required=True);ap.add_argument('--binary',type=Path,required=True);ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--threads',type=int,default=4);a=ap.parse_args()
 base={'enabled':True,'pulse_turn':153,'pulse_fertilizer_qty':3,'pulse_own_fertilizer_min':1}
 pool=[('identity',{'enabled':True}),('own1',base),
  ('money-le100',{**base,'pulse_opponent_money_max':100}),('money-le500',{**base,'pulse_opponent_money_max':500}),
  ('money-le2500',{**base,'pulse_opponent_money_max':2500}),('inv-ge10050',{**base,'pulse_market_inventory_min':10050}),
  ('m100-i10050',{**base,'pulse_opponent_money_max':100,'pulse_market_inventory_min':10050}),
  ('m2500-i10050',{**base,'pulse_opponent_money_max':2500,'pulse_market_inventory_min':10050})]
 with tempfile.TemporaryDirectory(prefix='pulse-gate-') as raw:
  td=Path(raw);cand=td/'candidate.json';cand.write_text(json.dumps(_source(str(a.candidate.resolve())).actions));opponents=[]
  for corpus,root in [('new7',a.top7),('full15',a.top15)]:
   jobs,meta=build_top30_jobs(root.resolve(),a.candidate.resolve(),99)
   for i in range(0,len(jobs),2):
    src=_source(jobs[i][2]);p=td/f'{corpus}-{i//2}.json';p.write_text(json.dumps(src.actions));opponents.append((corpus+'::'+meta[i]['team'],p))
  ranked,n=evaluate(pool,cand,opponents,range(138000,138032),a.binary,a.threads,td)
 report={'format':'pulse-router-cross-corpus-gate-v1','seeds':[138000,138031],'policies':len(opponents),'jobs':n,'ranked':ranked}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2)[:30000])
if __name__=='__main__':main()
