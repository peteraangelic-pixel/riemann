#!/usr/bin/env python3
"""Profile observable state fingerprints for routing V8 -> peer V16.

Labels come only from the matched newest-TOP12 gate.  Features come only from
public observations produced in fresh closed-loop games; team/rank is never an
input feature.  This is an audit/search artifact, not a leaderboard oracle.
"""
from __future__ import annotations
import argparse, importlib.util, json, statistics, sys
from collections import defaultdict
from pathlib import Path
from kaggle_environments import make

ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
from scripts.benchmark_top30 import build_top30_jobs

def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 return m.agent if hasattr(m,'agent') else m.act

def features(o,p):
 q=1-p; f=o['farms'][q]; market=o.get('market',{})
 inv=market.get('inventory',market.get('inventories',{})) or {}
 def count(x): return len(x) if isinstance(x,list) else (sum(x.values()) if isinstance(x,dict) else float(x or 0))
 out={'opp_cash':float(f.get('cash',f.get('bank',0)) or 0),'opp_hands':len(f.get('hands',[])),
      'opp_fields':count(f.get('fields',[])),'opp_pastures':count(f.get('pastures',[])),
      'opp_animals':count(f.get('animals',[]))}
 for k,v in inv.items():
  if isinstance(v,(int,float)): out['market_'+str(k).lower()]=float(v)
 return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--corpus',type=Path,required=True);ap.add_argument('--gate',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--seeds',type=int,default=2);a=ap.parse_args()
 gate=json.loads(a.gate.read_text()); by=defaultdict(dict)
 for r in gate['rows']: by[(r['team'],r['source_episode_id'],r['seed'],r['seat'])][r['candidate']]=r
 delta=defaultdict(list)
 for (team,*_),g in by.items():
  if 'v8' in g and 'peer_v16' in g: delta[team].append(g['peer_v16']['margin']-g['v8']['margin'])
 labels={t:statistics.mean(v)>0 for t,v in delta.items()}
 v8=ROOT/'agents/champion_tape_v8.py'; template,meta=build_top30_jobs(a.corpus.resolve(),v8.resolve(),12)
 records=[(template[i][2],meta[i]) for i in range(0,len(template),2)]
 rows=[]
 for rid,(opp_path,m) in enumerate(records):
  cand=load(v8,f'v8_{rid}');opp=load(opp_path,f'opp_{rid}')
  for seed in range(197000,197000+a.seeds):
   for seat in (0,1):
    snaps={}
    def rec(obs,cfg,cand=cand,seat=seat):
     s=int(obs.get('step',0))
     if s in (24,72,144,240,360,400): snaps[s]=features(obs,seat)
     return cand(obs,cfg)
    agents=[rec,opp] if seat==0 else [opp,rec]
    env=make('kaggriculture',configuration={'episodeSteps':720,'seed':seed},debug=False);env.run(agents)
    rows.append({'team':m['team'],'episode_id':m['episode_id'],'seed':seed,'seat':seat,'v16_beneficial':labels.get(m['team'],False),'gate_mean_delta':statistics.mean(delta[m['team']]),'snapshots':snaps})
 # Exact one-feature threshold screen, evaluated leave-one-episode-out later by the next gate.
 screen=[]
 for step in (24,72,144,240,360,400):
  keys=sorted({k for r in rows for k in r['snapshots'].get(step,{})})
  for key in keys:
   vals=sorted({r['snapshots'].get(step,{}).get(key) for r in rows if key in r['snapshots'].get(step,{})})
   for lo,hi in zip(vals,vals[1:]):
    th=(lo+hi)/2
    for op in ('le','ge'):
     pred=[(r['snapshots'].get(step,{}).get(key,0)<=th) if op=='le' else (r['snapshots'].get(step,{}).get(key,0)>=th) for r in rows]
     y=[r['v16_beneficial'] for r in rows];tp=sum(a and b for a,b in zip(pred,y));fp=sum(a and not b for a,b in zip(pred,y));fn=sum(not a and b for a,b in zip(pred,y));tn=len(y)-tp-fp-fn
     screen.append({'step':step,'feature':key,'op':op,'threshold':th,'tp':tp,'fp':fp,'fn':fn,'tn':tn,'balanced_accuracy':.5*(tp/max(1,tp+fn)+tn/max(1,tn+fp))})
 screen=sorted(screen,key=lambda x:(x['balanced_accuracy'],-x['fp']),reverse=True)[:50]
 out={'format':'observable-v16-router-fingerprint-v1','labels':{t:{'v16_beneficial':labels[t],'mean_margin_delta':statistics.mean(v)} for t,v in delta.items()},'rows':rows,'best_thresholds':screen}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'rows':len(rows),'best':screen[:10]},indent=2))
if __name__=='__main__':main()
