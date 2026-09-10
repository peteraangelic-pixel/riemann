#!/usr/bin/env python3
"""Evaluate decoded late401 tape on the exact peer V9 TOP12 seed panel."""
import argparse,json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'rust_port/tools'),str(Path(__file__).parent)]
from benchmark_top30 import build_top30_jobs
from kaggriculture_lab.rust_backend import _source
from search_single_market_mutations import evaluate
ap=argparse.ArgumentParser();ap.add_argument('--top12',type=Path,required=True);ap.add_argument('--binary',type=Path,required=True);ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
tape=_source(str(a.candidate.resolve())).actions
with tempfile.TemporaryDirectory(prefix='late-v9-panel-') as raw:
 td=Path(raw);jobs,meta=build_top30_jobs(a.top12.resolve(),a.candidate.resolve(),99);opps=[]
 for i in range(0,len(jobs),2):
  p=td/f'opp-{i//2}.json';p.write_text(json.dumps(_source(jobs[i][2]).actions));opps.append(('top12::'+meta[i]['team'],p))
 results,count=evaluate([('identity',tape)],opps,range(158000,158032),a.binary,4,td)
out={'format':'late401-exact-v9-panel-v2','method':'Python decode to pure JSON tape, direct kg_sim','policies':len(opps),'seeds':[158000,158031],'jobs':count,'results':results};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2)[:30000])
