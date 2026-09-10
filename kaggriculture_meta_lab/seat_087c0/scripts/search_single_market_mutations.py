#!/usr/bin/env python3
"""Scan every single V2 market action transplanted into V7 on two broad corpora."""
from __future__ import annotations
import argparse,copy,json,statistics,sys,tempfile
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'rust_port/tools')]
from benchmark_top30 import build_top30_jobs
from kaggriculture_lab.rust_backend import _source
from rust_client import Job,replay_many

def stats(rows):
 m=[a-b for a,b in rows];n=len(m);w=sum(x>0 for x in m);t=sum(x==0 for x in m)
 return {'games':n,'wins':w,'losses':n-w-t,'ties':t,'score_rate':(w+.5*t)/n,'mean_reward':statistics.mean(a for a,_ in rows),'mean_margin':statistics.mean(m)}
def evaluate(variants,opponents,seeds,binary,threads,td):
 jobs=[];labels=[]
 for name,tape in variants:
  p=td/(name+'.json');p.write_text(json.dumps(tape))
  for group,opp in opponents:
   for seed in seeds:
    for rev in (False,True):jobs.append(Job(seed,p,opp,reverse=rev));labels.append((name,group))
 rows=replay_many(jobs,binary=binary,steps=720,threads=threads,trim_hands_a=True,trim_hands_b=False,allow_errors=True,timeout=1500);g=defaultdict(list)
 for r,k in zip(rows,labels):
  if r.get('errors') or r.get('rewards') is None:raise RuntimeError(r.get('errors'))
  g[k].append(tuple(map(float,r['rewards'])))
 groups=list(dict.fromkeys(x for x,_ in opponents));out=[]
 for name,_ in variants:
  gs={x:stats(g[(name,x)]) for x in groups};allrows=sum((g[(name,x)] for x in groups),[]);out.append({'name':name,**stats(allrows),'groups':gs})
 ident=next(x for x in out if x['name']=='identity')
 for x in out:
  ds=[x['groups'][q]['score_rate']-ident['groups'][q]['score_rate'] for q in groups];x['regressed_groups']=sum(v<0 for v in ds);x['worst_group_delta']=min(ds);x['fitness']=[-x['regressed_groups'],x['worst_group_delta'],x['score_rate'],x['mean_reward'],x['mean_margin']]
 return sorted(out,key=lambda x:x['fitness'],reverse=True),len(jobs)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--top7',type=Path,required=True);ap.add_argument('--top15',type=Path,required=True);ap.add_argument('--binary',type=Path,required=True);ap.add_argument('--v7',type=Path,required=True);ap.add_argument('--v2',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--threads',type=int,default=4);a=ap.parse_args()
 v7=_source(str(a.v7.resolve())).actions;v2=_source(str(a.v2.resolve())).actions;variants=[('identity',v7)]
 for step in range(min(len(v7[0]),len(v2[0]))):
  if any(v7[s][step].get('market',[])!=v2[s][step].get('market',[]) for s in (0,1)):
   t=copy.deepcopy(v7)
   for s in (0,1):t[s][step]['market']=copy.deepcopy(v2[s][step].get('market',[]))
   variants.append((f'step-{step}',t))
 with tempfile.TemporaryDirectory(prefix='market-scan-') as raw:
  td=Path(raw);opps=[]
  for corpus,root in [('new7',a.top7),('full15',a.top15)]:
   jobs,meta=build_top30_jobs(root.resolve(),a.v7.resolve(),99)
   for i in range(0,len(jobs),2):
    p=td/f'{corpus}-{i//2}.json';p.write_text(json.dumps(_source(jobs[i][2]).actions));opps.append((corpus+'::'+meta[i]['team'],p))
  screen,j1=evaluate(variants,opps,range(139000,139002),a.binary,a.threads,td)
  names={'identity'}|{x['name'] for x in screen[:31]};finals=[x for x in variants if x[0] in names]
  hold,j2=evaluate(finals,opps,range(140000,140008),a.binary,a.threads,td)
 report={'format':'single-v2-market-mutation-scan-v1','policies':len(opps),'mutations':len(variants)-1,'screen_seeds':[139000,139001],'holdout_seeds':[140000,140007],'jobs':j1+j2,'screen_top':screen[:50],'holdout':hold}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'mutations':report['mutations'],'jobs':report['jobs'],'holdout':hold[:10]},indent=2)[:30000])
if __name__=='__main__':main()
