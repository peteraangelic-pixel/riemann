#!/usr/bin/env python3
"""Fixed independent gate for preregistered late401 reversion combinations."""
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
v7=load_tape(str(a.v7.resolve()));late=load_tape(str(a.late.resolve()))
profiles=[('identity',()),('r619',(619,)),('r610',(610,)),('r610-619',(610,619)),('r619-622',(619,622)),('r610-619-622',(610,619,622)),('r693',(693,)),('r619-693',(619,693))];variants=[]
for name,steps in profiles:
 t=copy.deepcopy(late)
 for s in (0,1):
  for i in steps:t[s][i]['market']=copy.deepcopy(v7[s][i].get('market',[]))
 variants.append((name,t))
with tempfile.TemporaryDirectory(prefix='late-reversion-gate-') as raw:
 td=Path(raw);opps=[]
 for corpus,root in [('latest7',a.latest),('previous7',a.previous),('top12',a.top12)]:
  jobs,meta=build_top30_jobs(root.resolve(),a.v7.resolve(),99)
  for i in range(0,len(jobs),2):
   p=td/f'{corpus}-{i//2}.json';p.write_text(json.dumps(_source(jobs[i][2]).actions));opps.append((corpus+'::'+meta[i]['team'],p))
 results,count=evaluate(variants,opps,range(176000,176016),a.binary,4,td)
out={'format':'late401-reversion-combo-gate-v1','profiles':{k:list(v) for k,v in profiles},'policies':len(opps),'seeds':[176000,176015],'jobs':count,'results':results};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2)[:30000])
