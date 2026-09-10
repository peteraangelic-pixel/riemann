#!/usr/bin/env python3
"""Iterative native LAB search around V16 using coherent six-hour action blocks.

Unlike the first day-crossover pilot this includes full G2 via its validated
Rust market overlay, uses several TOP7 donors, changes seed blocks each
iteration, and applies a strict fresh-holdout per-control gate.
"""
from __future__ import annotations
import argparse,base64,json,random,statistics,sys,tempfile,zlib
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"rust_port/tools")]
from kaggriculture_lab.rust_backend import _source
from rust_client import Job,replay_many
BLOCKS=120

def initial_population(n,donors,seed):
 r=random.Random(seed);base=(0,)*BLOCKS;out=[base];seen={base}
 for d in range(1,len(donors)):
  x=(d,)*BLOCKS
  if x not in seen:seen.add(x);out.append(x)
 while len(out)<n:
  x=[0]*BLOCKS
  for _ in range(r.randint(1,18)):
   start=r.randrange(BLOCKS);length=r.randint(1,6);d=r.randrange(1,len(donors))
   for j in range(start,min(BLOCKS,start+length)):x[j]=d
  x=tuple(x)
  if x not in seen:seen.add(x);out.append(x)
 return out

def breed(elites,n,donors,seed):
 r=random.Random(seed);base=(0,)*BLOCKS;out=[base];seen={base}
 for x in elites:
  if x not in seen:seen.add(x);out.append(x)
 while len(out)<n:
  a,b=r.sample(elites[:min(24,len(elites))],2);cuts=sorted(r.sample(range(1,BLOCKS),r.randint(1,5)));x=[];use=a;last=0
  for cut in cuts+[BLOCKS]:x.extend(use[last:cut]);use=b if use is a else a;last=cut
  for _ in range(r.randint(1,8)):
   start=r.randrange(BLOCKS);length=r.randint(1,5);d=r.randrange(len(donors))
   for j in range(start,min(BLOCKS,start+length)):x[j]=d
  x=tuple(x)
  if x not in seen:seen.add(x);out.append(x)
 return out

def materialize(genes,donors):
 return [[donors[genes[min(step//6,BLOCKS-1)]].actions[seat][step] for step in range(719)] for seat in range(2)]

def summarize(results,owners,names):
 g=defaultdict(lambda:defaultdict(list))
 for result,owner,name in zip(results,owners,names):
  if result.get('errors') or result.get('rewards') is None:raise RuntimeError(result.get('errors'))
  a,b=map(float,result['rewards']);g[owner][name].append(a-b)
 out={}
 for owner,by in g.items():
  controls={}
  for name,m in by.items():controls[name]={'games':len(m),'wins':sum(x>0 for x in m),'losses':sum(x<0 for x in m),'ties':sum(x==0 for x in m),'score_rate':(sum(x>0 for x in m)+.5*sum(x==0 for x in m))/len(m),'mean_margin':statistics.mean(m),'worst_margin':min(m)}
  out[owner]={'controls':controls,'worst_score_rate':min(x['score_rate'] for x in controls.values()),'mean_score_rate':statistics.mean(x['score_rate'] for x in controls.values()),'mean_margin':statistics.mean(x['mean_margin'] for x in controls.values())}
 return out

def key(s):return s['worst_score_rate'],s['mean_score_rate'],s['mean_margin']

def phase(population,donors,opponents,seeds,binary,threads):
 tapes=[materialize(g,donors) for g in population]
 with tempfile.TemporaryDirectory(prefix='v16-genetic-') as raw:
  td=Path(raw);cps=[];ops=[];profiles=[]
  for i,t in enumerate(tapes):p=td/f'c{i}.json';p.write_text(json.dumps(t));cps.append(p)
  for i,(name,source,profile) in enumerate(opponents):
   p=td/f'o{i}.json';p.write_text(json.dumps(source.actions));ops.append(p)
   if profile is not None:q=td/f'p{i}.json';q.write_text(json.dumps(profile));profiles.append(q)
   else:profiles.append(None)
  jobs=[];owners=[];names=[]
  for owner,cp in enumerate(cps):
   for oi,(name,source,profile) in enumerate(opponents):
    for seed in seeds:
     for seat in (0,1):jobs.append(Job(seed,cp,ops[oi],reverse=bool(seat),overlay_b=profiles[oi]));owners.append(owner);names.append(name)
  results=replay_many(jobs,binary=binary,steps=720,threads=threads,trim_hands_a=True,trim_hands_b=True,allow_errors=True,timeout=900)
 return summarize(results,owners,names),len(jobs)

def emit(path,actions):
 blob=base64.b85encode(zlib.compress(json.dumps(actions,separators=(',',':')).encode(),9)).decode()
 text='''# V16 iterative genetic block winner; LAB candidate only.\nimport base64, copy, json, zlib\nACTIONS=json.loads(zlib.decompress(base64.b85decode(%r)))\ndef agent(observation, configuration):\n p=int(observation.get("player",0));step=min(int(observation.get("step",0)),len(ACTIONS[p])-1);action=copy.deepcopy(ACTIONS[p][step]);action["hands"]=action.get("hands",[])[:len(observation["farms"][p]["hands"])];return action\nact=agent\n'''%blob
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--binary',type=Path,required=True);ap.add_argument('--population',type=int,default=384);ap.add_argument('--generations',type=int,default=4);ap.add_argument('--threads',type=int,default=4);ap.add_argument('--seed',type=int,default=20260910);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--agent-output',type=Path,required=True);a=ap.parse_args()
 paths=[ROOT/'agents/variants/agent_v16_kanno_top7_champion.py',ROOT/'agents/candidates/champion_tape_germanjurado1.py',ROOT/'agents/candidates/top7_kanno_ep107377838.py',ROOT/'agents/candidates/top7_yusuke_best_ep107377081.py',ROOT/'agents/candidates/top7_himanshu_best_ep107382217.py',ROOT/'agents/candidates/top7_spataro_best_ep107362641.py',ROOT/'agents/candidates/top7_binghua_best_ep107365958.py']
 donors=[_source(str(p)) for p in paths]
 controls=[('parent',donors[0],None),('german',donors[1],None),('kanno_lower',donors[2],None),('b21',_source(str(ROOT/'agents/current/agent_v9_b21_s16.py')),None),('g2',_source(str(ROOT/'agents/variants/agent_v10_subin_106845775.py')),{'enabled':True,'start_day':6,'cash_reserve':250,'milk_reserve':1})]
 if any(x is None for x in donors) or any(x[1] is None for x in controls):raise SystemExit('uncompilable donor/control')
 pop=initial_population(a.population,donors,a.seed);history=[];jobs=0
 for generation in range(a.generations):
  stats,n=phase(pop,donors,controls,range(84000+generation*8,84008+generation*8),a.binary,a.threads);jobs+=n
  order=sorted(range(len(pop)),key=lambda i:key(stats[i]),reverse=True);history.append({'generation':generation,'seeds':[84000+generation*8,84007+generation*8],'best':[{'genes':pop[i],'summary':stats[i]} for i in order[:12]]})
  pop=breed([pop[i] for i in order[:32]],a.population,donors,a.seed+generation+1)
 # Union final elites plus pure parent; deduplicate.
 finalists=[(0,)*BLOCKS]
 for h in history:
  for e in h['best']:
   x=tuple(e['genes'])
   if x not in finalists:finalists.append(x)
 finalists=finalists[:32]
 hold,n=phase(finalists,donors,controls,range(85000,85032),a.binary,a.threads);jobs+=n;base=hold[0];eligible=[]
 for i,s in hold.items():
  if i==0:continue
  c=s['controls'];bc=base['controls'];strict=all(c[name]['score_rate']>=bc[name]['score_rate'] and c[name]['mean_margin']>=bc[name]['mean_margin']-250 for name,_,_ in controls)
  if strict and c['parent']['score_rate']>.55 and s['mean_margin']>base['mean_margin']+100:eligible.append(i)
 winner=max(eligible,key=lambda i:key(hold[i])) if eligible else 0;emitted=winner!=0
 if emitted:emit(a.agent_output,materialize(finalists[winner],donors))
 elif a.agent_output.exists():a.agent_output.unlink()
 report={'format':'v16-iterative-genetic-block-search-v1','population':a.population,'generations':a.generations,'blocks':BLOCKS,'donors':[p.name for p in paths],'controls':[x[0] for x in controls],'total_jobs':jobs,'history':history,'holdout_seeds':[85000,85031],'baseline':base,'winner_index':winner,'winner_genes':finalists[winner],'winner':hold[winner],'eligible':eligible,'emitted':emitted}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('total_jobs','winner_index','eligible','emitted')},indent=2))
if __name__=='__main__':main()
