#!/usr/bin/env python3
"""Screen one executable agent against one latest tape from every TOP49 player."""
from __future__ import annotations
import argparse,gzip,importlib.util,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PASS={"farmer":["PASS"],"hands":[],"market":[]}
def load(path):
 s=importlib.util.spec_from_file_location('top49_agent',path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return getattr(m,'agent',m.act)
def main():
 p=argparse.ArgumentParser();p.add_argument('--agent',required=True);p.add_argument('--shard',type=int,default=0);p.add_argument('--shards',type=int,default=1);a=p.parse_args()
 from kaggle_environments import make
 agent=load((ROOT/a.agent).resolve()); manifest=json.loads((ROOT/'kaggriculture/research/top49_latest_episodes.json').read_text(encoding='utf8'))
 rows=[]
 for item in manifest['players'][a.shard::a.shards]:
  player=item['player'];episode=item['episode']
  with gzip.open(ROOT/f'kaggriculture/top49_full/{episode}/replay.json.gz','rt') as f:r=json.load(f)
  side=r['info']['TeamNames'].index(player); tape=[x[side].get('action') or PASS for x in r['steps']]
  def opponent(obs,cfg,t=tape):return t[min(int(obs.get('step',0))+1,len(t)-1)]
  games=[]
  for ours in (0,1):
   cfg=dict(r['configuration']);cfg['seed']=r['info']['seed']; agents=[opponent,opponent];agents[ours]=agent
   env=make('kaggriculture',configuration=cfg);env.run(agents);x=float(env.state[ours].reward or 0);y=float(env.state[1-ours].reward or 0);games.append({'side':ours,'ours':x,'theirs':y,'win':x>y})
  row={'player':player,'episode':episode,'wins':sum(x['win'] for x in games),'games':2,'our_mean':statistics.mean(x['ours'] for x in games),'opponent_mean':statistics.mean(x['theirs'] for x in games),'margin_mean':statistics.mean(x['ours']-x['theirs'] for x in games),'details':games};rows.append(row);print('PLAYER_JSON='+json.dumps(row,ensure_ascii=False,separators=(',',':')))
 print('SHARD_JSON='+json.dumps({'agent':a.agent,'shard':a.shard,'players':len(rows),'wins':sum(x['wins'] for x in rows),'games':2*len(rows),'margin_mean':statistics.mean(x['margin_mean'] for x in rows),'rows':rows},ensure_ascii=False,separators=(',',':')))
if __name__=='__main__':main()
