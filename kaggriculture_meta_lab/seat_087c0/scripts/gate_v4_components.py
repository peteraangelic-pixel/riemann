#!/usr/bin/env python3
"""Fixed independent gate for preregistered V4 components."""
import argparse,copy,json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'rust_port/tools'),str(Path(__file__).parent)]
from benchmark_top30 import build_top30_jobs
from kaggriculture_lab.rust_backend import _source
from search_single_market_mutations import evaluate
ap=argparse.ArgumentParser();ap.add_argument('--top7',type=Path,required=True);ap.add_argument('--top15',type=Path,required=True);ap.add_argument('--binary',type=Path,required=True);ap.add_argument('--v7',type=Path,required=True);ap.add_argument('--v4',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
v7=_source(str(a.v7.resolve())).actions;v4=_source(str(a.v4.resolve())).actions;variants=[]
for name,steps in [('v7',()),('m401',(401,)),('m409',(409,)),('m401409',(401,409)),('m360',(360,))]:
 t=copy.deepcopy(v7)
 for seat in (0,1):
  for step in steps:t[seat][step]['market']=copy.deepcopy(v4[seat][step]['market'])
 variants.append((name,t))
with tempfile.TemporaryDirectory(prefix='v4-fixed-gate-') as raw:
 td=Path(raw);opps=[]
 for corpus,root in [('new7',a.top7),('full15',a.top15)]:
  jobs,meta=build_top30_jobs(root.resolve(),a.v7.resolve(),99)
  for i in range(0,len(jobs),2):
   p=td/f'{corpus}-{i//2}.json';p.write_text(json.dumps(_source(jobs[i][2]).actions));opps.append((corpus+'::'+meta[i]['team'],p))
 result,jobs=evaluate(variants,opps,range(144000,144016),a.binary,4,td)
out={'format':'v4-fixed-component-gate-v1','policies':len(opps),'seeds':[144000,144015],'jobs':jobs,'results':result};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2)[:30000])
