#!/usr/bin/env python3
"""Scan every individual post-opening V4 market/hands component on the V7 body."""
from __future__ import annotations
import argparse,copy,json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'rust_port/tools'),str(Path(__file__).parent)]
from benchmark_top30 import build_top30_jobs
from kaggriculture_lab.rust_backend import _source
from search_single_market_mutations import evaluate

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--top7',type=Path,required=True);ap.add_argument('--top15',type=Path,required=True);ap.add_argument('--binary',type=Path,required=True);ap.add_argument('--v7',type=Path,required=True);ap.add_argument('--v4',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--threads',type=int,default=4);a=ap.parse_args()
 v7=_source(str(a.v7.resolve())).actions;v4=_source(str(a.v4.resolve())).actions;variants=[('identity',v7)]
 for step in range(2,min(len(v7[0]),len(v4[0]))):
  for channel in ('market','hands','farmer'):
   if any(v7[s][step].get(channel)!=v4[s][step].get(channel) for s in (0,1)):
    t=copy.deepcopy(v7)
    for seat in (0,1):
     if channel in v4[seat][step]:t[seat][step][channel]=copy.deepcopy(v4[seat][step][channel])
     else:t[seat][step].pop(channel,None)
    variants.append((f'{channel}-{step}',t))
 with tempfile.TemporaryDirectory(prefix='v4-components-') as raw:
  td=Path(raw);opps=[]
  for corpus,root in [('new7',a.top7),('full15',a.top15)]:
   jobs,meta=build_top30_jobs(root.resolve(),a.v7.resolve(),99)
   for i in range(0,len(jobs),2):
    p=td/f'{corpus}-{i//2}.json';p.write_text(json.dumps(_source(jobs[i][2]).actions));opps.append((corpus+'::'+meta[i]['team'],p))
  screen,j1=evaluate(variants,opps,range(142000,142002),a.binary,a.threads,td)
  names={'identity'}|{x['name'] for x in screen[:31]};finals=[x for x in variants if x[0] in names]
  hold,j2=evaluate(finals,opps,range(143000,143008),a.binary,a.threads,td)
 report={'format':'v4-component-scan-v1','policies':len(opps),'components':len(variants)-1,'screen_seeds':[142000,142001],'holdout_seeds':[143000,143007],'jobs':j1+j2,'screen_top':screen[:50],'holdout':hold}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'components':report['components'],'jobs':report['jobs'],'holdout':hold[:12]},indent=2)[:30000])
if __name__=='__main__':main()
