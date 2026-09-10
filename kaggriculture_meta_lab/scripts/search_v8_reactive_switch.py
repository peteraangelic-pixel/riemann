#!/usr/bin/env python3
"""Evolve a public-state turn-1 selector between V6 and V7 openings."""
from __future__ import annotations
import argparse,base64,copy,json,random,statistics,sys,tempfile,zlib
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'rust_port/tools'),str(ROOT/'scripts')]
from kaggriculture_lab.rust_backend import _source
from benchmark_top30 import build_top30_jobs
from rust_client import Job,replay_many
# gene: money mode (0 ignore,1 below,2 above), threshold; inventory mode/threshold

def profile(g):
 mm,mt,im,it=g;d={'enabled':True,'opening_switch_enabled':mm!=0 or im!=0}
 if mm==1:d['opening_opponent_money_below']=mt
 if mm==2:d['opening_opponent_money_above']=mt
 if im==1:d['opening_wheat_inventory_below']=it
 if im==2:d['opening_wheat_inventory_above']=it
 return d

def initial(n,seed):
 r=random.Random(seed);out=[(0,0,0,0)];seen=set(out)
 money=list(range(1800,3501,100));inv=list(range(9850,10151,10))
 while len(out)<n:
  g=(r.choice((0,1,2)),r.choice(money),r.choice((0,1,2)),r.choice(inv))
  if g[0]==g[2]==0:continue
  if g not in seen:seen.add(g);out.append(g)
 return out

def breed(elites,n,seed):
 r=random.Random(seed);out=list(dict.fromkeys([(0,0,0,0),*elites]));seen=set(out)
 while len(out)<n:
  a=list(r.choice(elites[:min(24,len(elites))]))
  if r.random()<.3:a[0]=r.choice((0,1,2))
  if r.random()<.3:a[2]=r.choice((0,1,2))
  if r.random()<.7:a[1]=max(1000,min(4500,a[1]+r.choice((-300,-200,-100,100,200,300))))
  if r.random()<.7:a[3]=max(9500,min(10500,a[3]+r.choice((-30,-20,-10,10,20,30))))
  if a[0]==a[2]==0:a[0]=1
  g=tuple(a)
  if g not in seen:seen.add(g);out.append(g)
 return out

def evaluate(pop,candidate,opponents,seeds,binary,threads,td,tag):
 profiles=[]
 for i,g in enumerate(pop):p=td/f'{tag}-p{i}.json';p.write_text(json.dumps(profile(g)));profiles.append(p)
 jobs=[];meta=[]
 for i,p in enumerate(profiles):
  for team,op in opponents:
   for seed in seeds:
    for seat in (0,1):jobs.append(Job(seed,candidate,op,reverse=bool(seat),overlay_a=p));meta.append((i,team))
 rows=replay_many(jobs,binary=binary,steps=720,threads=threads,trim_hands_a=True,trim_hands_b=False,allow_errors=True,timeout=1500);group=defaultdict(list)
 for row,key in zip(rows,meta):
  if row.get('errors') or row.get('rewards') is None:raise RuntimeError(row.get('errors'))
  a,b=map(float,row['rewards']);group[key].append((a,b))
 out=[];team_names=list(dict.fromkeys(t for t,_ in opponents))
 for i,g in enumerate(pop):
  teams={};vals=[]
  for team in team_names:
   v=group[(i,team)];vals.extend(v);m=[a-b for a,b in v];w=sum(x>0 for x in m);t=sum(x==0 for x in m);teams[team]={'games':len(v),'score_rate':(w+.5*t)/len(v),'mean_reward':statistics.mean(a for a,_ in v),'mean_margin':statistics.mean(m)}
  m=[a-b for a,b in vals];w=sum(x>0 for x in m);t=sum(x==0 for x in m);out.append({'gene':list(g),'profile':profile(g),'games':len(vals),'wins':w,'losses':len(vals)-w-t,'ties':t,'score_rate':(w+.5*t)/len(vals),'mean_reward':statistics.mean(a for a,_ in vals),'mean_margin':statistics.mean(m),'worst_team_score':min(v['score_rate'] for v in teams.values()),'teams':teams})
 return out,len(jobs)
def fit(s):return (s['score_rate'],s['worst_team_score'],s['mean_reward'],s['mean_margin'])
def emit(path,v6,v7,g,summary):
 blob=base64.b85encode(zlib.compress(json.dumps({'v6':v6,'v7':v7},separators=(',',':')).encode(),9)).decode();mm,mt,im,it=g
 text=f'''\"\"\"V8 reactive opening selector; holdout score {summary['score_rate']:.6f}.\"\"\"\nimport base64,copy,json,zlib\n_DATA=json.loads(zlib.decompress(base64.b85decode({blob!r})))\nV6,V7=_DATA["v6"],_DATA["v7"]\ndef agent(observation,configuration=None):\n p=int(observation.get("player",0));step=min(int(observation.get("step",0)),718);use=False\n if step==1:\n  try:\n   opp=float(observation["farms"][1-p]["money"]);inv=float(observation["market"]["inventory"]["WHEAT"])\n   use=({mm}==0 or ({mm}==1 and opp<={mt}) or ({mm}==2 and opp>={mt})) and ({im}==0 or ({im}==1 and inv<={it}) or ({im}==2 and inv>={it}))\n  except Exception:use=False\n action=copy.deepcopy((V6 if use else V7)[p][step]);action["hands"]=action.get("hands",[])[:len(observation["farms"][p]["hands"])]\n return action\nact=agent\n''';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--corpus',type=Path,required=True);ap.add_argument('--binary',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--agent-output',type=Path,required=True);ap.add_argument('--population',type=int,default=160);ap.add_argument('--generations',type=int,default=3);ap.add_argument('--threads',type=int,default=4);ap.add_argument('--seed',type=int,default=20260910);a=ap.parse_args()
 v6=_source(str(ROOT/'agents/candidates/agent_v6_safe_opening.py')).actions;v7=_source(str(ROOT/'agents/candidates/agent_v7_market_probe.py')).actions
 template,meta=build_top30_jobs(a.corpus.resolve(),ROOT/'agents/candidates/agent_v7_market_probe.py',15)
 with tempfile.TemporaryDirectory(prefix='v8-reactive-') as raw:
  td=Path(raw);candidate=td/'v7.json';candidate.write_text(json.dumps(v7));opponents=[]
  for i in range(0,len(template),2):
   tape=_source(template[i][2]);p=td/f'opp-{i//2}.json';p.write_text(json.dumps(tape.actions));opponents.append((meta[i]['team'],p))
  pop=initial(a.population,a.seed);history=[];jobs=0
  for gen in range(a.generations):
   stats,n=evaluate(pop,candidate,opponents,range(123000+2*gen,123002+2*gen),a.binary,a.threads,td,f'g{gen}');jobs+=n;order=sorted(range(len(pop)),key=lambda i:fit(stats[i]),reverse=True);history.append({'generation':gen,'top':[stats[i] for i in order[:24]]});pop=breed([pop[i] for i in order[:32]],a.population,a.seed+gen+1)
  finals=[]
  for h in history:
   for s in h['top']:
    g=tuple(s['gene'])
    if g not in finals:finals.append(g)
  if (0,0,0,0) not in finals:finals.append((0,0,0,0))
  finals=finals[:40];hold,n=evaluate(finals,candidate,opponents,range(124000,124008),a.binary,a.threads,td,'hold');jobs+=n;rank=sorted(range(len(finals)),key=lambda i:fit(hold[i]),reverse=True);win=rank[0];emit(a.agent_output,v6,v7,finals[win],hold[win]);report={'format':'v8-reactive-opening-evolution-v1','population':a.population,'generations':a.generations,'total_jobs':jobs,'holdout_seeds':[124000,124007],'history':history,'finalists':[hold[i] for i in rank],'winner_gene':list(finals[win]),'winner':hold[win]};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('total_jobs','winner_gene','winner')},indent=2)[:12000])
if __name__=='__main__':main()
