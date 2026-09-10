#!/usr/bin/env python3
"""Scan each post-401 V16->V7 market reversion on the late401 body."""
import argparse,copy,json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'rust_port/tools'),str(Path(__file__).parent)]
from benchmark_top30 import build_top30_jobs
from kaggriculture_lab.rust_backend import _source
from fast_h2h import load_tape
from search_single_market_mutations import evaluate
ap=argparse.ArgumentParser()
for n in ('latest','previous','top12'):ap.add_argument('--'+n,type=Path,required=True)
ap.add_argument('--binary',type=Path,required=True);ap.add_argument('--v7',type=Path,required=True);ap.add_argument('--late',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
v7=load_tape(str(a.v7.resolve()));late=load_tape(str(a.late.resolve()));variants=[('identity',late)]
turns=sorted({i for s in (0,1) for i in range(401,719) if late[s][i].get('market')!=v7[s][i].get('market')})
for step in turns:
 t=copy.deepcopy(late)
 for s in (0,1):t[s][step]['market']=copy.deepcopy(v7[s][step].get('market',[]))
 variants.append((f'revert-{step}',t))
with tempfile.TemporaryDirectory(prefix='late401-reversions-') as raw:
 td=Path(raw);opps=[]
 for corpus,root in [('latest7',a.latest),('previous7',a.previous),('top12',a.top12)]:
  jobs,meta=build_top30_jobs(root.resolve(),a.v7.resolve(),99)
  for i in range(0,len(jobs),2):
   p=td/f'{corpus}-{i//2}.json';p.write_text(json.dumps(_source(jobs[i][2]).actions));opps.append((corpus+'::'+meta[i]['team'],p))
 screen,j1=evaluate(variants,opps,range(174000,174002),a.binary,4,td)
 names={'identity'}|{x['name'] for x in screen[:24]};finals=[x for x in variants if x[0] in names]
 hold,j2=evaluate(finals,opps,range(175000,175008),a.binary,4,td)
out={'format':'late401-single-reversion-search-v1','policies':len(opps),'different_turns':turns,'variants':len(variants),'screen_seeds':[174000,174001],'holdout_seeds':[175000,175007],'jobs':j1+j2,'screen_top':screen[:50],'holdout':hold};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'variants':len(variants),'jobs':j1+j2,'holdout':hold[:15]},indent=2)[:30000])
