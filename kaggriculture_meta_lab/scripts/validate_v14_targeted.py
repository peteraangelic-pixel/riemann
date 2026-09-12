#!/usr/bin/env python3
"""Closed-loop validation only where V14 can differ from its V8 fallback."""
import argparse,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kaggriculture_lab import rust_backend
from benchmark_top30 import build_top30_jobs

def opening(spec):
 target=spec[5:];path,seat=target.rsplit('#',1);r=json.load(open(path,encoding='utf-8-sig'));return r['steps'][1][int(seat)].get('action') or {}
def cls(a):
 m=a.get('market',[]); ops=[tuple(x[:2]) for x in m]
 if ops[:2]==[('BUY_PRODUCT','WHEAT'),('SELL','WHEAT')] and sum(x==('HIRE',) for x in ops)==6:return 'route-positive'
 if sum(x==('HIRE',) for x in ops)==7 and not any(x and x[0]=='BUY_PRODUCT' for x in ops):return 'near-negative'
 return None
def stat(rs):
 return {'games':len(rs),'wins':sum(r['margin']>0 for r in rs),'losses':sum(r['margin']<0 for r in rs),'mean_reward':statistics.mean(r['self_reward'] for r in rs),'mean_margin':statistics.mean(r['margin'] for r in rs),'routes':sum(r.get('route_expected',False) for r in rs)}
def main():
 a=argparse.ArgumentParser();a.add_argument('--corpus',type=Path,required=True);a.add_argument('--v8',type=Path,required=True);a.add_argument('--v14',type=Path,required=True);a.add_argument('--seeds',type=int,default=4);a.add_argument('--seed-start',type=int,default=186000);a.add_argument('--workers',type=int,default=4);a.add_argument('--output',type=Path,required=True);z=a.parse_args()
 temp,meta=build_top30_jobs(z.corpus.resolve(),z.v8.resolve(),15);records=[]
 for i in range(0,len(temp),2):
  spec=temp[i][2];kind=cls(opening(spec))
  if kind:records.append((spec,meta[i],kind))
 jobs=[];labels=[]
 for name,path in [('v8',z.v8),('v14',z.v14)]:
  for spec,m,kind in records:
   for seed in range(z.seed_start,z.seed_start+z.seeds):
    for seat in (0,1):jobs.append((seed,str(path.resolve()),spec,seat,720,kind));labels.append((name,m,kind))
 rows=rust_backend.run_rust(jobs,z.workers,progress_every=20);outrows=[]
 for r,(name,m,kind) in zip(rows,labels):outrows.append({**r,'candidate':name,'class':kind,'rank':m['rank'],'slot':m['slot'],'route_expected':kind=='route-positive'})
 fail=[r for r in outrows if r.get('error')]
 if fail:raise RuntimeError(f'{len(fail)} errors: {fail[:2]}')
 summary={n:{k:stat([r for r in outrows if r['candidate']==n and r['class']==k]) for k in ('route-positive','near-negative')} for n in ('v8','v14')}
 z.output.parent.mkdir(parents=True,exist_ok=True);z.output.write_text(json.dumps({'format':'v14-targeted-closed-loop-v1','records':len(records),'summary':summary,'rows':outrows},indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
