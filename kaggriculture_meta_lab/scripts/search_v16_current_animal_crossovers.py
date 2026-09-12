#!/usr/bin/env python3
"""Large day-block crossover search between two current animal-scale parents."""
from __future__ import annotations
import argparse,base64,json,random,statistics,sys,tempfile,zlib
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'rust_port/tools')]
from kaggriculture_lab.rust_backend import _source
from benchmark_top30 import build_top30_jobs
from rust_client import Job,replay_many

def masks(n,seed):
 rng=random.Random(seed);out=[];seen=set()
 def add(x):
  x=tuple(x)
  if x not in seen:seen.add(x);out.append(x)
 add([0]*30);add([1]*30)
 for cut in range(1,30):add([0]*cut+[1]*(30-cut));add([1]*cut+[0]*(30-cut))
 while len(out)<n:
  x=[0]*30
  for d in rng.sample(range(30),rng.randint(2,16)):x[d]=1
  add(x)
 return out[:n]
def cross(a,b,m):
 return [[(b.actions[s] if m[min(t//24,29)] else a.actions[s])[t] for t in range(min(len(a.actions[s]),len(b.actions[s])))] for s in (0,1)]
def phase(tapes,opps,seeds,binary,threads):
 with tempfile.TemporaryDirectory(prefix='v16-cross-') as td:
  td=Path(td);cp=[];op=[]
  for i,x in enumerate(tapes):p=td/f'c{i}.json';p.write_text(json.dumps(x));cp.append(p)
  for i,(_,x,_) in enumerate(opps):p=td/f'o{i}.json';p.write_text(json.dumps(x.actions));op.append(p)
  jobs=[];labels=[]
  for ci,c in enumerate(cp):
   for oi,(name,_,meta) in enumerate(opps):
    for seed in seeds:
     for seat in (0,1):jobs.append(Job(seed,c,op[oi],reverse=bool(seat)));labels.append((ci,name,meta['rank']))
  raw=replay_many(jobs,binary=binary,steps=720,threads=threads,trim_hands_a=True,trim_hands_b=False,allow_errors=True,timeout=1500)
 rows=[]
 for r,(ci,name,rank) in zip(raw,labels):
  if r.get('errors') or r.get('rewards') is None:raise RuntimeError(r.get('errors'))
  sr,orr=map(float,r['rewards']);rows.append((ci,name,rank,sr,orr,sr-orr))
 out={}
 for ci in range(len(tapes)):
  z=[r for r in rows if r[0]==ci];teams=defaultdict(list)
  for r in z:teams[r[1]].append(r)
  out[ci]={'games':len(z),'wins':sum(r[5]>0 for r in z),'losses':sum(r[5]<0 for r in z),'mean_reward':statistics.mean(r[3] for r in z),'mean_margin':statistics.mean(r[5] for r in z),'team_wins':{k:sum(r[5]>0 for r in v) for k,v in teams.items()}}
 return out,len(jobs)
def key(x):return x['wins'],x['mean_reward'],x['mean_margin']
def emit(path,actions):
 blob=base64.b85encode(zlib.compress(json.dumps(actions,separators=(',',':')).encode(),9))
 text=f'''\"\"\"V16 neutral current-animal day-block crossover.\"\"\"\nimport base64,copy,json,zlib\nACTIONS=json.loads(zlib.decompress(base64.b85decode({blob!r})))\ndef agent(observation, configuration):\n    p = int(observation.get("player", 0))\n    step = min(int(observation.get("step", 0)), len(ACTIONS[p]) - 1)\n    action = copy.deepcopy(ACTIONS[p][step])\n    action["hands"] = action.get("hands", [])[:len(observation["farms"][p]["hands"])]\n    return action\nact=agent\n''';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
def main():
 a=argparse.ArgumentParser();a.add_argument('--corpus',type=Path,required=True);a.add_argument('--binary',type=Path,required=True);a.add_argument('--population',type=int,default=128);a.add_argument('--threads',type=int,default=4);a.add_argument('--output',type=Path,required=True);a.add_argument('--agent-output',type=Path,required=True);z=a.parse_args()
 pa=_source(str((ROOT/'agents/v13_parents/p097.py').resolve()));pb=_source(str((ROOT/'agents/v13_parents/p091.py').resolve()));assert pa and pb
 template,meta=build_top30_jobs(z.corpus.resolve(),ROOT/'agents/v13_parents/p097.py',12);opps=[]
 for i in range(0,len(template),2):spec=template[i][2];src=_source(spec);assert src;opps.append((f"r{meta[i]['rank']:02d}",src,meta[i]))
 mm=masks(z.population,20260912);tapes=[cross(pa,pb,m) for m in mm]
 train,tj=phase(tapes,opps,range(191000,191002),z.binary,z.threads);finalists=sorted(train,key=lambda i:key(train[i]),reverse=True)[:16]
 # Include both pure parents regardless of train noise.
 finalists=list(dict.fromkeys(finalists+[0,1]));hold,hj=phase([tapes[i] for i in finalists],opps,range(192000,192008),z.binary,z.threads);mapped={finalists[i]:v for i,v in hold.items()};base=mapped[0]
 eligible=[]
 for i,v in mapped.items():
  regress=max((base['team_wins'][t]-v['team_wins'].get(t,0) for t in base['team_wins']),default=0)
  if i and key(v)>key(base) and regress<=4:eligible.append(i)
 win=max(eligible,key=lambda i:key(mapped[i])) if eligible else 0;emit(z.agent_output,tapes[win])
 report={'format':'v16-current-animal-day-cross-v1','population':len(tapes),'train_seeds':[191000,191001],'holdout_seeds':[192000,192007],'opponents':len(opps),'train_jobs':tj,'holdout_jobs':hj,'finalists':finalists,'baseline':base,'winner':win,'winner_mask':' '.join('B' if q else 'A' for q in mm[win]),'winner_holdout':mapped[win],'top_train':[{'index':i,'summary':train[i]} for i in sorted(train,key=lambda i:key(train[i]),reverse=True)[:20]],'holdout':[{'index':i,'summary':mapped[i]} for i in finalists]}
 z.output.parent.mkdir(parents=True,exist_ok=True);z.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('population','train_jobs','holdout_jobs','winner','winner_mask')},indent=2))
if __name__=='__main__':main()
