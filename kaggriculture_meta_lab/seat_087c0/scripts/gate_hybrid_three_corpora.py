#!/usr/bin/env python3
"""Fixed three-current-corpus gate for full and late V7/V16 market hybrids."""
import argparse,copy,json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'rust_port/tools'),str(Path(__file__).parent)]
from benchmark_top30 import build_top30_jobs
from kaggriculture_lab.rust_backend import _source
from search_single_market_mutations import evaluate
ap=argparse.ArgumentParser();
for n in ('latest','previous','top12'):ap.add_argument('--'+n,type=Path,required=True)
ap.add_argument('--binary',type=Path,required=True);ap.add_argument('--v7',type=Path,required=True);ap.add_argument('--v16',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
v7=_source(str(a.v7.resolve())).actions;v16=_source(str(a.v16.resolve())).actions
def hybrid(start):
 t=copy.deepcopy(v7)
 for s in (0,1):
  for i in range(start,719):t[s][i]['market']=copy.deepcopy(v16[s][i].get('market',[]))
 return t
variants=[('identity',v7),('full',hybrid(2)),('start393',hybrid(393)),('start401',hybrid(401))]
with tempfile.TemporaryDirectory(prefix='hybrid-three-corpora-') as raw:
 td=Path(raw);opps=[]
 for corpus,root in [('latest7',a.latest),('previous7',a.previous),('top12',a.top12)]:
  jobs,meta=build_top30_jobs(root.resolve(),a.v7.resolve(),99)
  for i in range(0,len(jobs),2):
   p=td/f'{corpus}-{i//2}.json';p.write_text(json.dumps(_source(jobs[i][2]).actions));opps.append((corpus+'::'+meta[i]['team'],p))
 result,jobs=evaluate(variants,opps,range(150000,150016),a.binary,4,td)
out={'format':'hybrid-three-current-corpora-gate-v1','policies':len(opps),'seeds':[150000,150015],'jobs':jobs,'results':result};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2)[:30000])
