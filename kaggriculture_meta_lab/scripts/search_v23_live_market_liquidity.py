#!/usr/bin/env python3
"""Deterministic market-liquidity population search using exact live opponents."""
from __future__ import annotations
import argparse,copy,json,random,statistics,sys,tempfile,base64,zlib,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'rust_port/tools'),str(ROOT/'scripts')]
from kaggriculture_lab.rust_backend import _source
from benchmark_top30 import build_top30_jobs
from rust_client import Job,replay_many

def load(p):
 with p.open(encoding='utf-8-sig') as f:return json.load(f)
def live_records(root):
 out=[]
 for folder in sorted(x for x in root.iterdir() if x.is_dir()):
  rr=[(f,load(f)) for f in sorted(folder.rglob('*.json'))];cnt=collections.Counter()
  for _,r in rr:cnt.update(set(r.get('info',{}).get('TeamNames') or []))
  team=cnt.most_common(1)[0][0]
  for f,r in rr:
   names=r.get('info',{}).get('TeamNames') or [];seats=[i for i,n in enumerate(names) if n==team]
   if len(seats)!=1:continue
   seed=r.get('info',{}).get('seed',0);seed=seed if isinstance(seed,int) and not isinstance(seed,bool) else 0
   out.append((f'tape:{f.resolve()}#{1-seats[0]}',seed,f'live-{folder.name}'))
 return out
def configs(n):
 rng=random.Random(20260912);products=['WHEAT','CARROT','TOMATO','STRAWBERRY','MELON','EGG','MILK','WOOL','FERTILIZER'];out=[{'mode':'base','days':[],'products':products}]
 presets=[list(range(a,30)) for a in (10,14,18,20,22,24,26,28,29)]
 for mode in ('duplicate','scale'):
  for days in presets:
   for ps in (products,['FERTILIZER'],['MILK','WOOL','EGG'],['WHEAT','CARROT','MELON','STRAWBERRY']):out.append({'mode':mode,'days':days,'products':ps})
 while len(out)<n:
  start=rng.randint(8,29);days=[d for d in range(start,30) if rng.random()<rng.uniform(.25,.9)]
  ps=rng.sample(products,rng.randint(1,len(products)));out.append({'mode':rng.choice(['duplicate','scale']),'days':days,'products':ps})
 return out[:n]
def mutate(base,cfg):
 a=copy.deepcopy(base)
 if cfg['mode']=='base':return a
 days=set(cfg['days']);products=set(cfg['products'])
 for seat in (0,1):
  for t,action in enumerate(a[seat]):
   if t//24 not in days:continue
   market=action.get('market') or []
   if cfg['mode']=='scale':
    for order in market:
     if len(order)>=3 and order[0]=='SELL' and order[1] in products and isinstance(order[2],int):order[2]=min(1000,max(1,order[2]*2))
   else:
    extra=[]
    for order in market:
     if order and order[0]=='SELL' and len(order)>1 and order[1] in products and len(market)+len(extra)<10:extra.append(copy.deepcopy(order))
    market.extend(extra);action['market']=market
 return a
def run(tapes,records,binary,threads):
 with tempfile.TemporaryDirectory(prefix='v23-market-') as td:
  td=Path(td);cp=[];op=[]
  for i,a in enumerate(tapes):p=td/f'c{i}.json';p.write_text(json.dumps(a));cp.append(p)
  for i,(spec,seed,group) in enumerate(records):src=_source(spec);p=td/f'o{i}.json';p.write_text(json.dumps(src.actions));op.append((p,seed,group))
  jobs=[];labels=[]
  for ci,c in enumerate(cp):
   for p,seed,g in op:
    for seat in (0,1):jobs.append(Job(seed,c,p,reverse=bool(seat)));labels.append((ci,g))
  raw=replay_many(jobs,binary=binary,steps=720,threads=threads,trim_hands_a=True,trim_hands_b=False,allow_errors=True,timeout=1500)
 rows=[]
 for r,(ci,g) in zip(raw,labels):
  if r.get('errors') or r.get('rewards') is None:raise RuntimeError(r.get('errors'))
  sr,orr=map(float,r['rewards']);rows.append((ci,g,sr,orr,sr-orr))
 out={}
 for ci in range(len(tapes)):
  z=[r for r in rows if r[0]==ci];groups={}
  for g in sorted(set(r[1] for r in z)):
   q=[r for r in z if r[1]==g];groups[g]={'games':len(q),'wins':sum(r[4]>0 for r in q),'mean_reward':statistics.mean(r[2] for r in q),'mean_margin':statistics.mean(r[4] for r in q)}
  out[ci]={'games':len(z),'wins':sum(r[4]>0 for r in z),'losses':sum(r[4]<0 for r in z),'mean_reward':statistics.mean(r[2] for r in z),'mean_margin':statistics.mean(r[4] for r in z),'groups':groups}
 return out,len(jobs)
def key(x):return x['wins'],x['mean_reward'],x['mean_margin']
def emit(path,actions):
 blob=base64.b85encode(zlib.compress(json.dumps(actions,separators=(',',':')).encode(),9));text=f'''\"\"\"V23 live-opponent-qualified market liquidity policy.\"\"\"\nimport base64,copy,json,zlib\nACTIONS=json.loads(zlib.decompress(base64.b85decode({blob!r})))\ndef agent(observation, configuration):\n    p=int(observation.get("player",0));step=min(int(observation.get("step",0)),len(ACTIONS[p])-1)\n    action=copy.deepcopy(ACTIONS[p][step]);action["hands"]=action.get("hands",[])[:len(observation["farms"][p]["hands"])]\n    return action\nact=agent\n''';path.write_text(text)
def main():
 p=argparse.ArgumentParser();p.add_argument('--live',type=Path,required=True);p.add_argument('--corpus',type=Path,required=True);p.add_argument('--binary',type=Path,required=True);p.add_argument('--population',type=int,default=256);p.add_argument('--threads',type=int,default=4);p.add_argument('--output',type=Path,required=True);p.add_argument('--agent-output',type=Path,required=True);a=p.parse_args()
 base=_source(str((ROOT/'agents/variants/agent_v16_kanno_top7_champion.py').resolve()));assert base
 cc=configs(a.population);tapes=[mutate(base.actions,c) for c in cc];live=live_records(a.live);train_live=live[::2];hold_live=live[1::2]
 train,tj=run(tapes,train_live,a.binary,a.threads);finalists=sorted(train,key=lambda i:key(train[i]),reverse=True)[:16];finalists=list(dict.fromkeys(finalists+[0]))
 temp,meta=build_top30_jobs(a.corpus.resolve(),ROOT/'agents/variants/agent_v16_kanno_top7_champion.py',12);current=[]
 for i in range(0,len(temp),2):current.append((temp[i][2],198000,'current-top12'))
 hold_records=hold_live+current;hold,hj=run([tapes[i] for i in finalists],hold_records,a.binary,a.threads);mapped={finalists[i]:v for i,v in hold.items()};baseh=mapped[0]
 elig=[]
 for i,v in mapped.items():
  if i==0:continue
  lv=v['groups'].get(hold_live[0][2],{}) if hold_live else {};bl=baseh['groups'].get(hold_live[0][2],{}) if hold_live else {}
  # Global improvement with no material loss in the newest-current block.
  cur=v['groups']['current-top12'];bcur=baseh['groups']['current-top12']
  live_groups=[q for g,q in v['groups'].items() if g.startswith('live-')];base_live=[q for g,q in baseh['groups'].items() if g.startswith('live-')]
  live_key=(sum(q['wins'] for q in live_groups),statistics.mean(q['mean_reward'] for q in live_groups),statistics.mean(q['mean_margin'] for q in live_groups))
  base_live_key=(sum(q['wins'] for q in base_live),statistics.mean(q['mean_reward'] for q in base_live),statistics.mean(q['mean_margin'] for q in base_live))
  if live_key>base_live_key and cur['wins']>=bcur['wins']-4:elig.append(i)
 def promotion(i):
  v=mapped[i];lg=[q for g,q in v['groups'].items() if g.startswith('live-')];cur=v['groups']['current-top12']
  return (sum(q['wins'] for q in lg),cur['wins'],statistics.mean(q['mean_reward'] for q in lg),cur['mean_reward'],v['mean_margin'])
 winner=max(elig,key=promotion) if elig else 0;emit(a.agent_output,tapes[winner])
 report={'format':'v23-live-market-liquidity-search-v1','population':len(tapes),'live_records':len(live),'train_jobs':tj,'holdout_jobs':hj,'finalists':finalists,'baseline':baseh,'winner':winner,'winner_config':cc[winner],'winner_holdout':mapped[winner],'top_train':[{'index':i,'config':cc[i],'summary':train[i]} for i in sorted(train,key=lambda i:key(train[i]),reverse=True)[:20]],'holdout':[{'index':i,'config':cc[i],'summary':mapped[i]} for i in finalists]};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('population','live_records','train_jobs','holdout_jobs','winner','winner_config')},indent=2))
if __name__=='__main__':main()
