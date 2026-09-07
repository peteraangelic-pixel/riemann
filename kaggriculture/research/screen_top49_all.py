#!/usr/bin/env python3
"""Screen one frozen agent on all five public tapes per TOP49 player, both seats."""
from __future__ import annotations
import argparse,gzip,importlib.util,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];PASS={'farmer':['PASS'],'hands':[],'market':[]}
def load(path):
 s=importlib.util.spec_from_file_location('all5_agent',path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return getattr(m,'agent',m.act)
def main():
 p=argparse.ArgumentParser();p.add_argument('--agent',required=True);p.add_argument('--shard',type=int,required=True);p.add_argument('--shards',type=int,default=7);a=p.parse_args()
 from kaggle_environments import make
 agent=load((ROOT/a.agent).resolve());players=json.load(open(ROOT/'kaggriculture/research/top49_all_episodes.json',encoding='utf8'))['players'];players=players[a.shard::a.shards];rows=[]
 for item in players:
  for episode in item['episodes']:
   with gzip.open(ROOT/f'kaggriculture/top49_full/{episode}/replay.json.gz','rt') as f:r=json.load(f)
   side=r['info']['TeamNames'].index(item['player']);tape=[x[side].get('action') or PASS for x in r['steps']]
   def opponent(obs,cfg,t=tape):return t[min(int(obs.get('step',0))+1,len(t)-1)]
   scores=[]
   for ours in (0,1):
    cfg=dict(r['configuration']);cfg['seed']=r['info']['seed'];agents=[opponent,opponent];agents[ours]=agent;env=make('kaggriculture',configuration=cfg);env.run(agents);scores.append((float(env.state[ours].reward or 0),float(env.state[1-ours].reward or 0)))
   row={'player':item['player'],'episode':episode,'wins':sum(x>y for x,y in scores),'our_mean':statistics.mean(x for x,y in scores),'opponent_mean':statistics.mean(y for x,y in scores),'margin_mean':statistics.mean(x-y for x,y in scores)};rows.append(row);print('EPISODE_JSON='+json.dumps(row,ensure_ascii=False,separators=(',',':')))
 out={'players':len(players),'episodes':len(rows),'games':2*len(rows),'wins':sum(x['wins'] for x in rows),'our_mean':statistics.mean(x['our_mean'] for x in rows),'opponent_mean':statistics.mean(x['opponent_mean'] for x in rows),'margin_mean':statistics.mean(x['margin_mean'] for x in rows)};print('SHARD_JSON='+json.dumps(out,separators=(',',':')))
if __name__=='__main__':main()
