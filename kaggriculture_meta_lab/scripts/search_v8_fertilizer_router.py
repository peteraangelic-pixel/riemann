#!/usr/bin/env python3
"""Evolve a fail-closed public-state router for the isolated step-153 pulse."""
from __future__ import annotations
import argparse,base64,copy,json,random,statistics,sys,tempfile,zlib
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'rust_port/tools'),str(ROOT/'scripts')]
from kaggriculture_lab.rust_backend import _source
from benchmark_top30 import build_top30_jobs
from rust_client import Job,replay_many
# gene: money mode (0 ignore, 1 <=, 2 >=), threshold; fertilizer inventory mode/threshold; qty

def profile(g):
 mm,mt,im,it,qty=g
 d={'enabled':True}
 if qty:
  d.update(pulse_turn=153,pulse_fertilizer_qty=qty)
  if mm==1:d['pulse_opponent_money_max']=mt
  if mm==2:d['pulse_opponent_money_min']=mt
  if im==1:d['pulse_market_inventory_max']=it
  if im==2:d['pulse_market_inventory_min']=it
 return d

def initial(n,seed):
 r=random.Random(seed);out=[(0,0,0,0,0)];seen=set(out)
 money=list(range(0,2101,50));inv=list(range(10025,10066))
 while len(out)<n:
  g=(r.choice((0,1,2)),r.choice(money),r.choice((0,1,2)),r.choice(inv),r.choice((1,2,3,4,5)))
  if g not in seen:seen.add(g);out.append(g)
 return out

def breed(elites,n,seed):
 r=random.Random(seed);identity=(0,0,0,0,0);out=list(dict.fromkeys([identity,*elites]));seen=set(out)
 while len(out)<n:
  a=list(r.choice(elites[:min(28,len(elites))]))
  if r.random()<.25:a[0]=r.choice((0,1,2))
  if r.random()<.25:a[2]=r.choice((0,1,2))
  if r.random()<.7:a[1]=max(0,min(3000,a[1]+r.choice((-200,-100,-50,50,100,200))))
  if r.random()<.7:a[3]=max(9900,min(10150,a[3]+r.choice((-3,-2,-1,1,2,3))))
  if r.random()<.35:a[4]=max(1,min(8,a[4]+r.choice((-2,-1,1,2))))
  g=tuple(a)
  if g not in seen:seen.add(g);out.append(g)
 return out

def evaluate(pop,candidate,opponents,seeds,binary,threads,td,tag):
 profiles=[]
 for i,g in enumerate(pop):
  p=td/f'{tag}-p{i}.json';p.write_text(json.dumps(profile(g)));profiles.append(p)
 jobs=[];meta=[]
 for i,p in enumerate(profiles):
  for team,op in opponents:
   for seed in seeds:
    for seat in (0,1):jobs.append(Job(seed,candidate,op,reverse=bool(seat),overlay_a=p));meta.append((i,team))
 rows=replay_many(jobs,binary=binary,steps=720,threads=threads,trim_hands_a=True,trim_hands_b=False,allow_errors=True,timeout=1500)
 group=defaultdict(list)
 for row,key in zip(rows,meta):
  if row.get('errors') or row.get('rewards') is None:raise RuntimeError(row.get('errors'))
  a,b=map(float,row['rewards']);group[key].append((a,b))
 out=[];team_names=list(dict.fromkeys(t for t,_ in opponents))
 for i,g in enumerate(pop):
  teams={};vals=[]
  for team in team_names:
   v=group[(i,team)];vals.extend(v);m=[a-b for a,b in v];w=sum(x>0 for x in m);t=sum(x==0 for x in m)
   teams[team]={'games':len(v),'wins':w,'score_rate':(w+.5*t)/len(v),'mean_reward':statistics.mean(a for a,_ in v),'mean_margin':statistics.mean(m)}
  margins=sorted(a-b for a,b in vals);w=sum(x>0 for x in margins);t=sum(x==0 for x in margins)
  out.append({'gene':list(g),'profile':profile(g),'games':len(vals),'wins':w,'losses':len(vals)-w-t,'ties':t,'score_rate':(w+.5*t)/len(vals),'mean_reward':statistics.mean(a for a,_ in vals),'mean_margin':statistics.mean(margins),'margin_q10':margins[len(margins)//10],'worst_team_score':min(v['score_rate'] for v in teams.values()),'teams':teams})
 return out,len(jobs)

def fit(s,base):
 deltas=[s['teams'][k]['score_rate']-base['teams'][k]['score_rate'] for k in base['teams']]
 floor=min(deltas)
 return (floor>=0,floor,s['wins'],s['margin_q10'],s['mean_margin'],s['mean_reward'])

def emit(path,v7,g,summary):
 blob=base64.b85encode(zlib.compress(json.dumps(v7,separators=(',',':')).encode(),9)).decode();mm,mt,im,it,qty=g
 text=f'''\"\"\"V8 LAB: fail-closed state-gated fertilizer pulse.\"\"\"\nimport base64,copy,json,zlib\nACTIONS=json.loads(zlib.decompress(base64.b85decode({blob!r})))\ndef agent(observation,configuration=None):\n p=int(observation.get("player",0));step=min(int(observation.get("step",0)),718);action=copy.deepcopy(ACTIONS[p][step]);use=False\n if step==153 and {qty}>0:\n  try:\n   money=float(observation["farms"][1-p]["money"]);inv=float(observation["market"]["inventory"]["FERTILIZER"])\n   use=({mm}==0 or ({mm}==1 and money<={mt}) or ({mm}==2 and money>={mt})) and ({im}==0 or ({im}==1 and inv<={it}) or ({im}==2 and inv>={it}))\n  except Exception:use=False\n if use:action.setdefault("market",[]).append(["SELL","FERTILIZER",{qty}])\n action["hands"]=action.get("hands",[])[:len(observation["farms"][p]["hands"])]\n return action\nact=agent\n'''
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--corpus',type=Path,required=True);ap.add_argument('--binary',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--agent-output',type=Path,required=True);ap.add_argument('--population',type=int,default=192);ap.add_argument('--generations',type=int,default=4);ap.add_argument('--threads',type=int,default=4);ap.add_argument('--seed',type=int,default=20260910);a=ap.parse_args()
 v7=_source(str(ROOT/'agents/candidates/agent_v7_market_probe.py')).actions;template,meta=build_top30_jobs(a.corpus.resolve(),ROOT/'agents/candidates/agent_v7_market_probe.py',15)
 with tempfile.TemporaryDirectory(prefix='v8-pulse-router-') as raw:
  td=Path(raw);candidate=td/'v7.json';candidate.write_text(json.dumps(v7));opponents=[]
  for i in range(0,len(template),2):
   tape=_source(template[i][2]);p=td/f'opp-{i//2}.json';p.write_text(json.dumps(tape.actions));opponents.append((meta[i]['team'],p))
  pop=initial(a.population,a.seed);history=[];jobs=0
  for gen in range(a.generations):
   stats,n=evaluate(pop,candidate,opponents,range(140000+4*gen,140004+4*gen),a.binary,a.threads,td,f'g{gen}');jobs+=n;base=next(s for s in stats if s['gene']==[0,0,0,0,0]);order=sorted(range(len(pop)),key=lambda i:fit(stats[i],base),reverse=True);history.append({'generation':gen,'identity':base,'top':[stats[i] for i in order[:28]]});pop=breed([pop[i] for i in order[:40]],a.population,a.seed+gen+1)
  finals=[]
  for h in history:
   for s in h['top']:
    g=tuple(s['gene'])
    if g not in finals:finals.append(g)
  identity=(0,0,0,0,0)
  finals=[identity]+[g for g in finals if g!=identity][:47]
  hold,n=evaluate(finals,candidate,opponents,range(141000,141012),a.binary,a.threads,td,'hold');jobs+=n;base=next(s for s in hold if s['gene']==list(identity));rank=sorted(range(len(finals)),key=lambda i:fit(hold[i],base),reverse=True);win=rank[0];emit(a.agent_output,v7,finals[win],hold[win]);report={'format':'v8-fertilizer-router-evolution-v1','population':a.population,'generations':a.generations,'total_jobs':jobs,'holdout_seeds':[141000,141011],'history':history,'finalists':[hold[i] for i in rank],'identity':base,'winner_gene':list(finals[win]),'winner':hold[win]};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('total_jobs','winner_gene','winner','identity')},indent=2)[:16000])
if __name__=='__main__':main()
