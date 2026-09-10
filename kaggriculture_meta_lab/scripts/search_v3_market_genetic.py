#!/usr/bin/env python3
"""Evolve Kanno-family market timing while freezing V3 farmer and hands.

Unlike the earlier all-action splice, every donor admitted here has exactly the
same 719-step farmer+hands trajectory as V3. Genes therefore alter only six-hour
market blocks. Fitness uses changing seeds, both physical seats, full G2 and
per-control baseline-relative guards; final promotion uses a disjoint holdout.
"""
from __future__ import annotations
import argparse,base64,json,random,statistics,sys,tempfile,zlib
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'rust_port/tools')]
from kaggriculture_lab.rust_backend import _source
from rust_client import Job,replay_many
BLOCK=6; STEPS=719; GENES=(STEPS+BLOCK-1)//BLOCK

def load_donors(corpus:Path):
 base=_source(str(ROOT/'agents/candidates/top7_kanno_ep107381285_v3_sibling.py')).actions[0]
 donors=[base];labels=['ep107381285-s0']
 for replay in sorted((corpus/'kanno').glob('replay_*.json')):
  data=json.load(open(replay))
  for seat in (0,1):
   actions=[row[seat].get('action') or {'farmer':['PASS'],'hands':[],'market':[]} for row in data['steps'][1:]]
   if len(actions)==STEPS and all(actions[i].get('farmer')==base[i].get('farmer') and actions[i].get('hands')==base[i].get('hands') for i in range(STEPS)):
    if actions not in donors:donors.append(actions);labels.append(f'{replay.stem}-s{seat}')
 return donors,labels

def materialize(g,donors):
 base=donors[0];return [[{'farmer':base[s].get('farmer',['PASS']),'hands':base[s].get('hands',[]),'market':donors[g[min(s//BLOCK,GENES-1)]][s].get('market',[])} for s in range(STEPS)]]*2

def initial(n,k,seed):
 rng=random.Random(seed);out=[(0,)*GENES]
 for d in range(1,k):out.append((d,)*GENES)
 # Day-coherent and six-hour mosaics, biased toward proven V3.
 while len(out)<n:
  g=[]
  if rng.random()<.45:
   for _day in range(30):
    d=0 if rng.random()<.55 else rng.randrange(k);g.extend([d]*4)
   g=g[:GENES]
  else:g=[0 if rng.random()<.55 else rng.randrange(k) for _ in range(GENES)]
  out.append(tuple(g))
 return list(dict.fromkeys(out)) if len(set(out))==len(out) else unique_fill(out,n,k,rng)

def unique_fill(out,n,k,rng):
 seen=set(out);out=list(seen)
 while len(out)<n:
  g=tuple(0 if rng.random()<.55 else rng.randrange(k) for _ in range(GENES))
  if g not in seen:seen.add(g);out.append(g)
 return out

def breed(elite,n,k,seed):
 rng=random.Random(seed);out=list(elite);seen=set(out)
 while len(out)<n:
  a,b=rng.sample(elite,min(2,len(elite)));use=a;g=[]
  for i in range(GENES):
   if i%4==0 and rng.random()<.22:use=b if use is a else a
   x=use[i]
   if rng.random()<.025:x=rng.randrange(k)
   g.append(x)
  child=tuple(g)
  if child not in seen:seen.add(child);out.append(child)
 return out

def summarize(rows):
 m=[r for r in rows];n=len(m);w=sum(x>0 for x in m);l=sum(x<0 for x in m);t=n-w-l
 return {'games':n,'wins':w,'losses':l,'ties':t,'score_rate':(w+.5*t)/n,'mean_margin':statistics.mean(m),'worst_margin':min(m)}

def evaluate(pop,donors,controls,seeds,binary,threads,tmp,prefix):
 paths=[]
 for i,g in enumerate(pop):p=tmp/f'{prefix}-cand-{i}.json';p.write_text(json.dumps(materialize(g,donors)));paths.append(p)
 jobs=[];meta=[]
 for i,p in enumerate(paths):
  for name,(op,overlay) in controls.items():
   for seed in seeds:
    for seat in (0,1):jobs.append(Job(seed,p,op,reverse=bool(seat),overlay_b=overlay));meta.append((i,name))
 raw=replay_many(jobs,binary=binary,steps=720,threads=threads,trim_hands_a=True,trim_hands_b=True,allow_errors=True,timeout=1200)
 grouped=defaultdict(list)
 for r,key in zip(raw,meta):
  if r.get('errors') or r.get('rewards') is None:raise RuntimeError(r.get('errors'))
  grouped[key].append(float(r['rewards'][0])-float(r['rewards'][1]))
 return [{name:summarize(grouped[(i,name)]) for name in controls} for i in range(len(pop))],len(jobs)

def fitness(stats,base):
 guards=[stats[k]['score_rate']-base[k]['score_rate'] for k in stats if k!='v3']
 margins=[stats[k]['mean_margin']-base[k]['mean_margin'] for k in stats if k!='v3']
 return (min(guards),stats['v3']['score_rate'],min(margins),statistics.mean(x['score_rate'] for x in stats.values()),statistics.mean(x['mean_margin'] for x in stats.values()))

def render(actions,provenance):
 blob=base64.b85encode(zlib.compress(json.dumps(actions,separators=(',',':')).encode(),9)).decode()
 return f'''# V3 Kanno-family market evolution candidate. {provenance}\nimport base64,copy,json,zlib\nACTIONS=json.loads(zlib.decompress(base64.b85decode({blob!r})))\ndef agent(observation, configuration):\n    p=int(observation.get("player",0))\n    step=min(int(observation.get("step",0)),len(ACTIONS[p])-1)\n    action=copy.deepcopy(ACTIONS[p][step])\n    action["hands"]=action.get("hands",[])[:len(observation["farms"][p]["hands"])]\n    return action\nact=agent\n'''

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--corpus',type=Path,required=True);ap.add_argument('--binary',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--agent-output',type=Path,required=True);ap.add_argument('--population',type=int,default=768);ap.add_argument('--generations',type=int,default=5);ap.add_argument('--threads',type=int,default=4);a=ap.parse_args()
 donors,labels=load_donors(a.corpus);assert len(donors)>=8,(len(donors),labels)
 specs={'v3':ROOT/'agents/candidates/top7_kanno_ep107381285_v3_sibling.py','v16':ROOT/'agents/variants/agent_v16_kanno_top7_champion.py','german':ROOT/'agents/candidates/champion_tape_germanjurado1.py','b21':ROOT/'agents/current/agent_v9_b21_s16.py','yusuke':ROOT/'agents/candidates/top7_yusuke_best_ep107377081.py','himanshu':ROOT/'agents/candidates/top7_himanshu_best_ep107382217.py','g2':ROOT/'agents/variants/agent_v10_subin_106845775.py'}
 with tempfile.TemporaryDirectory(prefix='v3-market-genetic-') as raw:
  td=Path(raw);controls={};g2p=td/'g2.json';g2p.write_text(json.dumps({'enabled':True,'start_day':6,'cash_reserve':250,'milk_reserve':1}))
  for i,(name,path) in enumerate(specs.items()):src=_source(str(path));assert src;p=td/f'control-{i}.json';p.write_text(json.dumps(src.actions));controls[name]=(p,g2p if name=='g2' else None)
  pop=initial(a.population,len(donors),20260910);history=[];total=0
  for gen in range(a.generations):
   seeds=range(91000+gen*101,91008+gen*101);stats,j=evaluate(pop,donors,controls,seeds,a.binary,a.threads,td,f'g{gen}');total+=j;base=stats[pop.index((0,)*GENES) if (0,)*GENES in pop else 0];rank=sorted(range(len(pop)),key=lambda i:fitness(stats[i],base),reverse=True);history.append({'generation':gen,'seeds':[seeds.start,seeds.stop-1],'best_genes':list(pop[rank[0]]),'best':stats[rank[0]],'baseline':base,'top_fitness':[list(fitness(stats[i],base)) for i in rank[:12]]});elite=[pop[i] for i in rank[:48]]
   if gen+1<a.generations:pop=breed(elite,a.population,len(donors),20260911+gen);pop[0]=(0,)*GENES
  finalists=[pop[i] for i in rank[:24]]
  if (0,)*GENES not in finalists:finalists.append((0,)*GENES)
  hs,hj=evaluate(finalists,donors,controls,range(92000,92064),a.binary,a.threads,td,'holdout');total+=hj;base=hs[finalists.index((0,)*GENES)]
  eligible=[]
  for i,s in enumerate(hs):
   guard=all(s[k]['score_rate']>=base[k]['score_rate']-.01 and s[k]['mean_margin']>=base[k]['mean_margin']-250 for k in s if k!='v3')
   if guard and s['v3']['score_rate']>.55 and s['v3']['mean_margin']>100:eligible.append(i)
  winner=max(eligible,key=lambda i:fitness(hs[i],base)) if eligible else finalists.index((0,)*GENES);emitted=bool(eligible)
  out={'format':'v3-market-genetic-v1','donors':labels,'population':a.population,'generations':a.generations,'block_hours':BLOCK,'total_jobs':total,'history':history,'holdout_seeds':[92000,92063],'baseline':base,'finalists':[{'genes':list(g),'stats':s,'fitness':list(fitness(s,base))} for g,s in zip(finalists,hs)],'eligible':eligible,'winner_index':winner,'winner_genes':list(finalists[winner]),'winner':hs[winner],'emitted':emitted}
  a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2)+'\n')
  if emitted:a.agent_output.parent.mkdir(parents=True,exist_ok=True);a.agent_output.write_text(render(materialize(finalists[winner],donors),f'LAB holdout 92000-92063; donors={labels}'))
  print(json.dumps({k:out[k] for k in ('total_jobs','eligible','winner_index','emitted')},indent=2));print(json.dumps(hs[winner],indent=2))
if __name__=='__main__':main()
