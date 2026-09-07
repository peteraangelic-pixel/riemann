#!/usr/bin/env python3
"""Screen one frozen agent on all five public tapes per TOP49 player, both seats."""
from __future__ import annotations
import argparse,gzip,importlib.util,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'kaggriculture'))
from replay_benchmark import load_environment,load_agent,scripted_agent,score_pair

def main():
 p=argparse.ArgumentParser();p.add_argument('--agent',type=Path,required=True);p.add_argument('--shard',type=int,required=True);p.add_argument('--shards',type=int,default=7);a=p.parse_args()
 players=json.load(open(ROOT/'kaggriculture/research/top49_all_episodes.json',encoding='utf8'))['players'];players=[x for i,x in enumerate(players) if i%a.shards==a.shard];agent=load_agent(ROOT/a.agent)
 rows=[]
 for item in players:
  for episode in item['episodes']:
   with gzip.open(ROOT/f'kaggriculture/top49_full/{episode}/replay.json.gz','rt') as f:r=json.load(f)
   target=r['info']['TeamNames'].index(item['player'])
   actions=[step[target].get('action') or {} for step in r['steps'][1:]]
   opp=scripted_agent(actions);scores=[]
   for seat in (0,1):
    env=load_environment();env.run([agent,opp] if seat==0 else [opp,agent]);pair=score_pair(env);scores.append(pair if seat==0 else (pair[1],pair[0]))
   row={'player':item['player'],'episode':episode,'wins':sum(x>y for x,y in scores),'our_mean':statistics.mean(x for x,y in scores),'opponent_mean':statistics.mean(y for x,y in scores),'margin_mean':statistics.mean(x-y for x,y in scores)};rows.append(row);print('EPISODE_JSON='+json.dumps(row,ensure_ascii=False,separators=(',',':')))
 out={'players':len(players),'episodes':len(rows),'games':2*len(rows),'wins':sum(x['wins'] for x in rows),'our_mean':statistics.mean(x['our_mean'] for x in rows),'opponent_mean':statistics.mean(x['opponent_mean'] for x in rows),'margin_mean':statistics.mean(x['margin_mean'] for x in rows)}
 print('SHARD_JSON='+json.dumps(out,separators=(',',':')))
if __name__=='__main__':main()
