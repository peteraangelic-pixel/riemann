#!/usr/bin/env python3
"""Search V7/V16 market-tail start and end boundaries on two TOP7 generations."""
import argparse,copy,json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'rust_port/tools'),str(Path(__file__).parent)]
from benchmark_top30 import build_top30_jobs
from kaggriculture_lab.rust_backend import _source
from search_single_market_mutations import evaluate
ap=argparse.ArgumentParser();ap.add_argument('--latest',type=Path,required=True);ap.add_argument('--previous',type=Path,required=True);ap.add_argument('--binary',type=Path,required=True);ap.add_argument('--v7',type=Path,required=True);ap.add_argument('--v16',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
v7=_source(str(a.v7.resolve())).actions;v16=_source(str(a.v16.resolve())).actions
turns=sorted({i for s in (0,1) for i in range(2,719) if v7[s][i].get('market')!=v16[s][i].get('market')})
def make(start,end):
 t=copy.deepcopy(v7)
 for s in (0,1):
  for i in range(start,end):t[s][i]['market']=copy.deepcopy(v16[s][i].get('market',[]))
 return t
variants=[('identity',v7),('hybrid-full',make(2,719))]
variants += [(f'start-{i}',make(i,719)) for i in turns if i>2]
variants += [(f'end-{i}',make(2,i)) for i in turns if i>2]
with tempfile.TemporaryDirectory(prefix='hybrid-boundaries-') as raw:
 td=Path(raw);opps=[]
 for corpus,root in [('latest7',a.latest),('previous7',a.previous)]:
  jobs,meta=build_top30_jobs(root.resolve(),a.v7.resolve(),99)
  for i in range(0,len(jobs),2):
   p=td/f'{corpus}-{i//2}.json';p.write_text(json.dumps(_source(jobs[i][2]).actions));opps.append((corpus+'::'+meta[i]['team'],p))
 screen,j1=evaluate(variants,opps,range(147000,147002),a.binary,4,td)
 names={'identity','hybrid-full'}|{x['name'] for x in screen[:30]};finals=[x for x in variants if x[0] in names]
 hold,j2=evaluate(finals,opps,range(148000,148008),a.binary,4,td)
out={'format':'hybrid-boundary-search-v1','policies':len(opps),'different_turns':len(turns),'variants':len(variants),'screen_seeds':[147000,147001],'holdout_seeds':[148000,148007],'jobs':j1+j2,'screen_top':screen[:60],'holdout':hold};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'variants':len(variants),'jobs':j1+j2,'holdout':hold[:15]},indent=2)[:30000])
