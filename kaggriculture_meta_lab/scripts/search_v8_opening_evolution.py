#!/usr/bin/env python3
"""Evolve the only policy feature separating V6 and V7: turn-1 wheat clearing.

The parents are identical on 718/719 turns. This LAB therefore searches the
actual causal interaction rather than pretending that unrelated blocks differ.
Every generation is screened against all selected TOP15 replay policies in both
physical seats; finalists receive a disjoint eight-seed holdout.
"""
from __future__ import annotations
import argparse,base64,copy,json,random,statistics,sys,tempfile,zlib
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'rust_port/tools'),str(ROOT/'scripts')]
from kaggriculture_lab.rust_backend import _source
from benchmark_top30 import build_top30_jobs
from rust_client import Job,replay_many

# order: 0=BUY(s),SELL; 1=SELL,BUY(s); 2=BUY1,SELL,BUY2
# A zero quantity suppresses that operation. Special V6 = (1,0,0,13).
Gene=tuple[int,int,int,int]


def source(path: Path):
 x=_source(str(path));
 if x is None: raise ValueError(f'uncompilable tape: {path}')
 return x.actions


def orders(g: Gene):
 order,b1,b2,sell=g
 buys=[['BUY_PRODUCT','WHEAT',q] for q in (b1,b2) if q>0]
 sale=[['SELL','WHEAT',sell]] if sell>0 else []
 if order==0:return buys+sale
 if order==1:return sale+buys
 return (buys[:1]+sale+buys[1:])


def materialize(base,g: Gene):
 out=copy.deepcopy(base)
 tail=[['BUY_PRODUCT','WHEAT',5],*([['HIRE']]*5),['BUY_ANIMAL','COW',2],['BUY_ANIMAL','SHEEP',2]]
 for seat in (0,1):out[seat][1]['market']=orders(g)+tail
 return out


def initial(n:int,seed:int):
 exact=[(1,0,0,13),(0,60,0,90)]
 buys=[0,5,7,10,13,20,27,40,60,75,85]
 sells=[13,30,45,60,75,90,105,120]
 genes=list(exact)
 for order in range(3):
  for b in buys:
   for s in sells:genes.append((order,b,0,s))
 for order in range(3):
  for b1,b2 in ((5,7),(7,13),(7,20),(13,20),(13,27),(20,40),(27,60),(40,45)):
   for s in sells:genes.append((order,b1,b2,s))
 genes=list(dict.fromkeys(genes));r=random.Random(seed);r.shuffle(genes)
 # Parents can never be shuffled out.
 genes=exact+[g for g in genes if g not in exact]
 return genes[:n]


def breed(elites:list[Gene],n:int,seed:int):
 r=random.Random(seed);out=list(dict.fromkeys([(1,0,0,13),(0,60,0,90),*elites]));seen=set(out)
 amounts=[0,5,7,10,13,15,20,27,30,40,45,60,75,85,90,105,120]
 while len(out)<n:
  a=list(r.choice(elites[:min(24,len(elites))]))
  if r.random()<.3:a[0]=r.randrange(3)
  for j in range(1,4):
   if r.random()<.55:
    if r.random()<.6:
     near=sorted(amounts,key=lambda x:abs(x-a[j]))[:6];a[j]=r.choice(near)
    else:a[j]=r.choice(amounts)
  if a[1]==a[2]==a[3]==0:a[3]=13
  g=tuple(a)
  if g not in seen:seen.add(g);out.append(g)
 return out


def evaluate(pop,base,opponents,seeds,binary,threads,td,tag):
 cps=[]
 for i,g in enumerate(pop):
  p=td/f'{tag}-c{i}.json';p.write_text(json.dumps(materialize(base,g)));cps.append(p)
 jobs=[];meta=[]
 for i,p in enumerate(cps):
  for oi,(team,op) in enumerate(opponents):
   for seed in seeds:
    for seat in (0,1):jobs.append(Job(seed,p,op,reverse=bool(seat)));meta.append((i,team))
 rows=replay_many(jobs,binary=binary,steps=720,threads=threads,trim_hands_a=True,trim_hands_b=False,allow_errors=True,timeout=1500)
 grouped=defaultdict(list)
 for row,key in zip(rows,meta):
  if row.get('errors') or row.get('rewards') is None:raise RuntimeError(row.get('errors'))
  a,b=map(float,row['rewards']);grouped[key].append((a,b))
 result=[]
 for i,g in enumerate(pop):
  teams={};all_rows=[]
  for team in dict.fromkeys(team for team,_ in opponents):
   vals=grouped[(i,team)];all_rows.extend(vals)
   margins=[a-b for a,b in vals];w=sum(x>0 for x in margins);t=sum(x==0 for x in margins)
   teams[team]={'games':len(vals),'wins':w,'losses':len(vals)-w-t,'ties':t,'score_rate':(w+.5*t)/len(vals),'mean_reward':statistics.mean(a for a,_ in vals),'mean_margin':statistics.mean(margins)}
  margins=[a-b for a,b in all_rows];w=sum(x>0 for x in margins);t=sum(x==0 for x in margins)
  result.append({'gene':list(g),'games':len(all_rows),'wins':w,'losses':len(all_rows)-w-t,'ties':t,'score_rate':(w+.5*t)/len(all_rows),'mean_reward':statistics.mean(a for a,_ in all_rows),'mean_margin':statistics.mean(margins),'worst_team_score':min(x['score_rate'] for x in teams.values()),'teams':teams})
 return result,len(jobs)


def fit(s):
 # Broad population score leads, then anti-catastrophe floor and absolute economy.
 return (s['score_rate'],s['worst_team_score'],s['mean_reward'],s['mean_margin'])


def emit(path,actions,note):
 blob=base64.b85encode(zlib.compress(json.dumps(actions,separators=(',',':')).encode(),9)).decode()
 text=f'''\"\"\"V8 evolved opening candidate. {note}\"\"\"\nimport base64,copy,json,zlib\nACTIONS=json.loads(zlib.decompress(base64.b85decode({blob!r})))\ndef agent(observation, configuration):\n    p=int(observation.get("player",0))\n    step=min(int(observation.get("step",0)),len(ACTIONS[p])-1)\n    action=copy.deepcopy(ACTIONS[p][step])\n    action["hands"]=action.get("hands",[])[:len(observation["farms"][p]["hands"])]\n    return action\nact=agent\n'''
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--corpus',type=Path,required=True);ap.add_argument('--binary',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--agent-output',type=Path,required=True);ap.add_argument('--population',type=int,default=160);ap.add_argument('--generations',type=int,default=3);ap.add_argument('--threads',type=int,default=4);ap.add_argument('--seed',type=int,default=20260910);a=ap.parse_args()
 v6=source(ROOT/'agents/candidates/agent_v6_safe_opening.py');v7=source(ROOT/'agents/candidates/agent_v7_market_probe.py')
 diffs=[i for i in range(719) if v6[0][i]!=v7[0][i]]
 if diffs!=[1] or any(v6[0][i]!=v6[1][i] or v7[0][i]!=v7[1][i] for i in range(719)):raise SystemExit(f'unexpected parent structure: {diffs}')
 template,meta=build_top30_jobs(a.corpus.resolve(),ROOT/'agents/candidates/agent_v7_market_probe.py',15)
 opponents=[]
 with tempfile.TemporaryDirectory(prefix='v8-opening-evolution-') as raw:
  td=Path(raw)
  # One opponent tape per selected record. Team aggregation prevents a team with
  # many records from masquerading as diversity.
  for i in range(0,len(template),2):
   tape=_source(template[i][2]);
   if tape is None:raise RuntimeError(template[i][2])
   p=td/f'opp-{i//2}.json';p.write_text(json.dumps(tape.actions));opponents.append((meta[i]['team'],p))
  pop=initial(a.population,a.seed);history=[];jobs=0
  for gen in range(a.generations):
   stats,n=evaluate(pop,v7,opponents,range(120000+gen*2,120002+gen*2),a.binary,a.threads,td,f'g{gen}');jobs+=n
   order=sorted(range(len(pop)),key=lambda i:fit(stats[i]),reverse=True)
   history.append({'generation':gen,'seeds':[120000+gen*2,120001+gen*2],'top':[stats[i] for i in order[:24]]})
   pop=breed([pop[i] for i in order[:32]],a.population,a.seed+gen+1)
  finals=[]
  for h in history:
   for s in h['top']:
    g=tuple(s['gene'])
    if g not in finals:finals.append(g)
  for g in ((1,0,0,13),(0,60,0,90)):
   if g not in finals:finals.append(g)
  finals=finals[:40]
  hold,n=evaluate(finals,v7,opponents,range(121000,121008),a.binary,a.threads,td,'holdout');jobs+=n
  rank=sorted(range(len(finals)),key=lambda i:fit(hold[i]),reverse=True);winner=rank[0]
  emit(a.agent_output,materialize(v7,finals[winner]),f'gene={finals[winner]}, holdout seeds 121000-121007')
  report={'format':'v8-v6-v7-opening-evolution-v1','parent_difference_steps':diffs,'gene_schema':['order','buy1','buy2','sell'],'population':a.population,'generations':a.generations,'opponent_policy_records':len(opponents),'total_jobs':jobs,'history':history,'holdout_seeds':[121000,121007],'finalists':[hold[i] for i in rank],'winner_gene':list(finals[winner]),'winner':hold[winner]}
  a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('parent_difference_steps','population','generations','opponent_policy_records','total_jobs','winner_gene')},indent=2));print(json.dumps(hold[winner],indent=2)[:12000])
if __name__=='__main__':main()
