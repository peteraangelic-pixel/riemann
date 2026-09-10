#!/usr/bin/env python3
"""Joint evolution of peer V4's German opening and our evolved market timing."""
from __future__ import annotations
import argparse,base64,json,random,statistics,sys,tempfile,zlib
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'rust_port/tools')]
from kaggriculture_lab.rust_backend import _source
from rust_client import Job,replay_many
STEPS=719;BLOCK=6;N=(STEPS+BLOCK-1)//BLOCK
OURS=(0,)+(0,)*N;PEER=(9,)+(1,)*N

def sources():
 def s(p):x=_source(str(ROOT/p));assert x;return x.actions
 return {'ours':s('agents/candidates/v3_market_genetic_holdout_winner.py'),'peer':s('agents/candidates/peer_v4_german9_kanno_v3.py'),'v3':s('agents/candidates/top7_kanno_ep107381285_v3_sibling.py'),'german':s('agents/candidates/champion_tape_germanjurado1.py')}
def materialize(g,src):
 cut=g[0];out=[];markets=[src['ours'],src['peer'],src['v3']]
 for seat in (0,1):
  stream=[]
  for step in range(STEPS):
   unit=src['german'][seat][step] if step//24<cut else src['v3'][seat][step];market=markets[g[1+step//BLOCK]][seat][step].get('market',[])
   stream.append({'farmer':unit.get('farmer',['PASS']),'hands':unit.get('hands',[]),'market':market})
  out.append(stream)
 return out
def initial(n,seed):
 rng=random.Random(seed);out=[OURS,PEER]
 for cut in range(13):
  for d in range(3):out.append((cut,)+(d,)*N)
 while len(out)<n:
  cut=rng.randrange(13);g=[]
  for i in range(N):
   day=(i*BLOCK)//24
   if day<cut:g.append(1 if rng.random()<.82 else rng.randrange(3))
   else:g.append(0 if rng.random()<.72 else rng.randrange(3))
  out.append((cut,*g))
 return unique(out,n,rng)
def unique(out,n,rng):
 seen=set();res=[]
 for x in out:
  if x not in seen:seen.add(x);res.append(x)
 while len(res)<n:
  x=(rng.randrange(13),*(rng.randrange(3) for _ in range(N)))
  if x not in seen:seen.add(x);res.append(x)
 return res
def breed(elite,n,seed):
 rng=random.Random(seed);out=list(elite);seen=set(out)
 while len(out)<n:
  a,b=rng.sample(elite,2);cut=a[0] if rng.random()<.5 else b[0]
  if rng.random()<.08:cut=max(0,min(12,cut+rng.choice([-1,1])))
  g=[];use=a
  for i in range(N):
   if i%4==0 and rng.random()<.2:use=b if use is a else a
   x=use[i+1]
   if rng.random()<.02:x=rng.randrange(3)
   g.append(x)
  child=(cut,*g)
  if child not in seen:seen.add(child);out.append(child)
 return out
def summary(m):
 n=len(m);w=sum(x>0 for x in m);l=sum(x<0 for x in m);t=n-w-l
 return {'games':n,'wins':w,'losses':l,'ties':t,'score_rate':(w+.5*t)/n,'mean_margin':statistics.mean(m),'worst_margin':min(m)}
def evaluate(pop,src,controls,seeds,binary,threads,td,tag):
 ps=[]
 for i,g in enumerate(pop):p=td/f'{tag}-{i}.json';p.write_text(json.dumps(materialize(g,src)));ps.append(p)
 jobs=[];meta=[]
 for i,p in enumerate(ps):
  for name,(op,ov) in controls.items():
   for seed in seeds:
    for seat in (0,1):jobs.append(Job(seed,p,op,reverse=bool(seat),overlay_b=ov));meta.append((i,name))
 rows=replay_many(jobs,binary=binary,steps=720,threads=threads,trim_hands_a=True,trim_hands_b=True,allow_errors=True,timeout=1200);d=defaultdict(list)
 for r,k in zip(rows,meta):
  if r.get('errors') or r.get('rewards') is None:raise RuntimeError(r.get('errors'))
  d[k].append(float(r['rewards'][0])-float(r['rewards'][1]))
 return [{k:summary(d[(i,k)]) for k in controls} for i in range(len(pop))],len(jobs)
def fit(s,floors):
 direct=min(s['ours']['score_rate'],s['peer']['score_rate']);dm=min(s['ours']['mean_margin'],s['peer']['mean_margin'])
 keys=[k for k in s if k not in ('ours','peer')];gs=min(s[k]['score_rate']-floors[k]['score_rate'] for k in keys);gm=min(s[k]['mean_margin']-floors[k]['mean_margin'] for k in keys)
 return (gs,gm,direct,dm,statistics.mean(s[k]['mean_margin'] for k in keys))
def render(a,note):
 b=base64.b85encode(zlib.compress(json.dumps(a,separators=(',',':')).encode(),9)).decode()
 return f'''# Hybrid of peer V4 opening and evolved Kanno market. {note}\nimport base64,copy,json,zlib\nACTIONS=json.loads(zlib.decompress(base64.b85decode({b!r})))\ndef agent(observation, configuration):\n    p=int(observation.get("player",0));step=min(int(observation.get("step",0)),len(ACTIONS[p])-1)\n    action=copy.deepcopy(ACTIONS[p][step]);action["hands"]=action.get("hands",[])[:len(observation["farms"][p]["hands"])]\n    return action\nact=agent\n'''
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--binary',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--agent-output',type=Path,required=True);ap.add_argument('--population',type=int,default=512);ap.add_argument('--generations',type=int,default=4);ap.add_argument('--threads',type=int,default=4);a=ap.parse_args();src=sources()
 paths={'ours':'agents/candidates/v3_market_genetic_holdout_winner.py','peer':'agents/candidates/peer_v4_german9_kanno_v3.py','v3':'agents/candidates/top7_kanno_ep107381285_v3_sibling.py','v16':'agents/variants/agent_v16_kanno_top7_champion.py','german':'agents/candidates/champion_tape_germanjurado1.py','b21':'agents/current/agent_v9_b21_s16.py','g2':'agents/variants/agent_v10_subin_106845775.py','yusuke':'agents/candidates/top7_yusuke_best_ep107377081.py'}
 with tempfile.TemporaryDirectory(prefix='ours-peer-hybrid-') as raw:
  td=Path(raw);g2=td/'g2.json';g2.write_text(json.dumps({'enabled':True,'start_day':6,'cash_reserve':250,'milk_reserve':1}));controls={}
  for i,(k,pth) in enumerate(paths.items()):x=_source(str(ROOT/pth));assert x;p=td/f'control-{i}.json';p.write_text(json.dumps(x.actions));controls[k]=(p,g2 if k=='g2' else None)
  pop=initial(a.population,20260910);hist=[];total=0
  for gen in range(a.generations):
   seeds=range(95000+gen*101,95008+gen*101);stats,j=evaluate(pop,src,controls,seeds,a.binary,a.threads,td,f'g{gen}');total+=j;so=stats[pop.index(OURS)];sp=stats[pop.index(PEER)];floors={k:{'score_rate':min(so[k]['score_rate'],sp[k]['score_rate']),'mean_margin':min(so[k]['mean_margin'],sp[k]['mean_margin'])} for k in controls};rank=sorted(range(len(pop)),key=lambda i:fit(stats[i],floors),reverse=True);hist.append({'generation':gen,'best_genome':list(pop[rank[0]]),'best':stats[rank[0]],'fitness':list(fit(stats[rank[0]],floors))});elite=[pop[i] for i in rank[:48]]
   if gen+1<a.generations:pop=breed(elite,a.population,20260920+gen);pop[0]=OURS;pop[1]=PEER
  finalists=[pop[i] for i in rank[:24]]
  for p in (OURS,PEER):
   if p not in finalists:finalists.append(p)
  hs,j=evaluate(finalists,src,controls,range(96000,96064),a.binary,a.threads,td,'holdout');total+=j;bo=hs[finalists.index(OURS)];bp=hs[finalists.index(PEER)];eligible=[]
  for i,s in enumerate(hs):
   direct=all(s[k]['score_rate']>.55 and s[k]['mean_margin']>100 for k in ('ours','peer'))
   guard=all(s[k]['score_rate']>=min(bo[k]['score_rate'],bp[k]['score_rate'])-.01 and s[k]['mean_margin']>=min(bo[k]['mean_margin'],bp[k]['mean_margin'])-250 for k in s if k not in ('ours','peer'))
   if direct and guard:eligible.append(i)
  floors={k:{'score_rate':min(bo[k]['score_rate'],bp[k]['score_rate']),'mean_margin':min(bo[k]['mean_margin'],bp[k]['mean_margin'])} for k in controls};winner=max(eligible,key=lambda i:fit(hs[i],floors)) if eligible else max(range(len(finalists)),key=lambda i:fit(hs[i],floors));emitted=bool(eligible)
  out={'format':'ours-peer-v4-hybrid-v1','population':a.population,'generations':a.generations,'total_jobs':total,'history':hist,'holdout_seeds':[96000,96063],'ours_baseline':bo,'peer_baseline':bp,'finalists':[{'genome':list(g),'stats':s,'fitness':list(fit(s,floors))} for g,s in zip(finalists,hs)],'eligible':eligible,'winner_index':winner,'winner_genome':list(finalists[winner]),'winner':hs[winner],'emitted':emitted}
  a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2)+'\n')
  if emitted:a.agent_output.parent.mkdir(parents=True,exist_ok=True);a.agent_output.write_text(render(materialize(finalists[winner],src),f'cut={finalists[winner][0]}, holdout 96000-96063'))
  print(json.dumps({k:out[k] for k in ('total_jobs','eligible','winner_index','emitted')},indent=2));print(json.dumps(hs[winner],indent=2))
if __name__=='__main__':main()
