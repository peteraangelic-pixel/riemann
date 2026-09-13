#!/usr/bin/env python3
"""Search state-aware market overlays on exact live opponents plus newest TOP12."""
from __future__ import annotations
import argparse,collections,json,statistics,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'rust_port/tools'),str(ROOT/'scripts')]
from kaggriculture_lab.rust_backend import _source
from benchmark_top30 import build_top30_jobs
from generate_market_overlays import generate_profiles
from rust_client import Job,replay_many

def load(p):
 with p.open(encoding='utf-8-sig') as f:return json.load(f)
def live_records(root):
 out=[]
 for folder in sorted(x for x in root.iterdir() if x.is_dir()):
  rr=[(f,load(f)) for f in sorted(folder.rglob('*.json'))];c=collections.Counter()
  for _,r in rr:c.update(set(r.get('info',{}).get('TeamNames') or []))
  team=c.most_common(1)[0][0]
  for f,r in rr:
   names=r.get('info',{}).get('TeamNames') or [];seat=[i for i,n in enumerate(names) if n==team]
   if len(seat)!=1:continue
   seed=r.get('info',{}).get('seed',0);seed=seed if isinstance(seed,int) and not isinstance(seed,bool) else 0
   out.append((f'tape:{f.resolve()}#{1-seat[0]}',seed,f'live-{folder.name}'))
 return out
def run(base,profiles,records,binary,threads):
 with tempfile.TemporaryDirectory(prefix='v24-overlay-') as td:
  td=Path(td);cp=td/'candidate.json';cp.write_text(json.dumps(base.actions));pps=[];ops=[]
  for i,pf in enumerate(profiles):p=td/f'p{i}.json';p.write_text(json.dumps(pf));pps.append(p)
  for i,(spec,seed,g) in enumerate(records):src=_source(spec);p=td/f'o{i}.json';p.write_text(json.dumps(src.actions));ops.append((p,seed,g))
  jobs=[];labels=[]
  for pi,pp in enumerate(pps):
   for op,seed,g in ops:
    for seat in (0,1):jobs.append(Job(seed,cp,op,reverse=bool(seat),overlay_a=pp));labels.append((pi,g))
  raw=replay_many(jobs,binary=binary,steps=720,threads=threads,trim_hands_a=True,trim_hands_b=False,allow_errors=True,timeout=1500)
 rows=[]
 for r,(pi,g) in zip(raw,labels):
  if r.get('errors') or r.get('rewards') is None:raise RuntimeError(r.get('errors'))
  a,b=map(float,r['rewards']);rows.append((pi,g,a,b,a-b))
 out={}
 for pi in range(len(profiles)):
  z=[r for r in rows if r[0]==pi];groups={}
  for g in sorted(set(r[1] for r in z)):
   q=[r for r in z if r[1]==g];groups[g]={'games':len(q),'wins':sum(r[4]>0 for r in q),'mean_reward':statistics.mean(r[2] for r in q),'mean_margin':statistics.mean(r[4] for r in q)}
  out[pi]={'games':len(z),'wins':sum(r[4]>0 for r in z),'losses':sum(r[4]<0 for r in z),'mean_reward':statistics.mean(r[2] for r in z),'mean_margin':statistics.mean(r[4] for r in z),'groups':groups}
 return out,len(jobs)
def key(v):return v['wins'],v['mean_reward'],v['mean_margin']
def main():
 p=argparse.ArgumentParser();p.add_argument('--live',type=Path,required=True);p.add_argument('--corpus',type=Path,required=True);p.add_argument('--binary',type=Path,required=True);p.add_argument('--population',type=int,default=1000);p.add_argument('--threads',type=int,default=4);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 base=_source(str((ROOT/'agents/variants/agent_v16_kanno_top7_champion.py').resolve()));assert base
 profiles=generate_profiles(a.population,20260913);profiles.insert(1,{'enabled':True});profiles=profiles[:a.population]
 live=live_records(a.live);train,tj=run(base,profiles,live[::2],a.binary,a.threads);finalists=sorted(train,key=lambda i:key(train[i]),reverse=True)[:20];finalists=list(dict.fromkeys(finalists+[0,1]))
 temp,meta=build_top30_jobs(a.corpus.resolve(),ROOT/'agents/variants/agent_v16_kanno_top7_champion.py',12);current=[(temp[i][2],temp[i][0],'current-top12') for i in range(0,len(temp),2)]
 hold,hj=run(base,[profiles[i] for i in finalists],live[1::2]+current,a.binary,a.threads);mapped={finalists[i]:v for i,v in hold.items()};baseline=mapped[0]
 def promo(i):
  v=mapped[i];lg=[q for g,q in v['groups'].items() if g.startswith('live-')];c=v['groups']['current-top12'];return (sum(q['wins'] for q in lg),c['wins'],statistics.mean(q['mean_reward'] for q in lg),c['mean_reward'],v['mean_margin'])
 basep=promo(0);eligible=[i for i in finalists if i and promo(i)>basep and mapped[i]['groups']['current-top12']['wins']>=baseline['groups']['current-top12']['wins']-4]
 winner=max(eligible,key=promo) if eligible else 0
 report={'format':'v24-live-dynamic-market-search-v1','population':len(profiles),'live_records':len(live),'train_jobs':tj,'holdout_jobs':hj,'finalists':finalists,'baseline':baseline,'winner':winner,'winner_profile':profiles[winner],'winner_holdout':mapped[winner],'top_train':[{'index':i,'profile':profiles[i],'summary':train[i]} for i in sorted(train,key=lambda i:key(train[i]),reverse=True)[:30]],'holdout':[{'index':i,'profile':profiles[i],'summary':mapped[i]} for i in finalists]};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('population','live_records','train_jobs','holdout_jobs','winner','winner_profile')},indent=2))
if __name__=='__main__':main()
