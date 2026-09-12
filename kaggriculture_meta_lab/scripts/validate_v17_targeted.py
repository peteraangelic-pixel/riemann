#!/usr/bin/env python3
"""Small closed-loop check of V17 routing against target and adjacent classes."""
import argparse,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kaggriculture_lab import rust_backend
from benchmark_top30 import build_top30_jobs
def stat(rs):
 return {'games':len(rs),'wins':sum(r['margin']>0 for r in rs),'losses':sum(r['margin']<0 for r in rs),'mean_reward':statistics.mean(r['self_reward'] for r in rs),'mean_margin':statistics.mean(r['margin'] for r in rs)}
def main():
 p=argparse.ArgumentParser();p.add_argument('--corpus',type=Path,required=True);p.add_argument('--safe',type=Path,required=True);p.add_argument('--router',type=Path,required=True);p.add_argument('--workers',type=int,default=4);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 temp,meta=build_top30_jobs(a.corpus.resolve(),a.safe.resolve(),12);records=[]
 for i in range(0,len(temp),2):
  if meta[i]['rank'] in (7,8,11,12):records.append((temp[i][2],meta[i],'target' if meta[i]['rank']==8 else 'negative'))
 jobs=[];labels=[]
 for name,path in [('safe',a.safe),('router',a.router)]:
  for spec,m,kind in records:
   for seat in (0,1):jobs.append((195000,str(path.resolve()),spec,seat,720,kind));labels.append((name,m,kind))
 rows=rust_backend.run_rust(jobs,a.workers,progress_every=20);out=[]
 for r,(name,m,kind) in zip(rows,labels):out.append({**r,'candidate':name,'rank':m['rank'],'class':kind})
 failed=[r for r in out if r.get('error')]
 if failed:raise RuntimeError(f'{len(failed)} failures: {failed[:2]}')
 summary={n:{k:stat([r for r in out if r['candidate']==n and r['class']==k]) for k in ('target','negative')} for n in ('safe','router')}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps({'format':'v17-targeted-closed-loop-v1','summary':summary,'rows':out},indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
