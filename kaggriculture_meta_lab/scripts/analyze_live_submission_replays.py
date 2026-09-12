#!/usr/bin/env python3
"""Summarize actual Kaggle episodes for two submission-id directories."""
from __future__ import annotations
import argparse,collections,json,statistics
from pathlib import Path

def load(path):
 with path.open(encoding='utf-8-sig') as f:return json.load(f)
def team_for(replays):
 counts=collections.Counter()
 for r in replays:
  counts.update(set(r.get('info',{}).get('TeamNames') or []))
 if not counts:raise ValueError('no TeamNames in replays')
 return counts.most_common(1)[0][0]
def op_name(a):return a[0] if isinstance(a,list) and a and isinstance(a[0],str) else 'NONE'
def summarize(folder,submission_id):
 files=sorted(folder.rglob('*.json'));replays=[load(p) for p in files];team=team_for(replays);games=[]
 for path,r in zip(files,replays):
  names=r.get('info',{}).get('TeamNames') or [];steps=r.get('steps') or []
  seats=[i for i,n in enumerate(names) if n==team]
  if not seats or not steps:continue
  for seat in seats:
   opp=names[1-seat] if len(names)>1 else '?';actions=[]
   for row in steps[1:]:
    a=row[seat].get('action') if isinstance(row,list) and len(row)>seat else None
    actions.append(a if isinstance(a,dict) else {})
   counts=collections.Counter();markets=collections.Counter()
   for a in actions:
    counts[op_name(a.get('farmer'))]+=1
    for h in a.get('hands',[]) or []:counts[op_name(h)]+=1
    for m in a.get('market',[]) or []:markets[op_name(m)]+=1
   rewards=[steps[-1][i].get('reward') for i in range(min(2,len(steps[-1])))]
   own=float(rewards[seat] or 0);other=float(rewards[1-seat] or 0)
   statuses=collections.Counter(str(row[seat].get('status')) for row in steps if isinstance(row,list) and len(row)>seat)
   last_obs=next((row[seat].get('observation') for row in reversed(steps) if isinstance(row,list) and len(row)>seat and isinstance(row[seat].get('observation'),dict)),{})
   farm=(last_obs.get('farms') or [{},{}])[seat] if last_obs else {};tiles=farm.get('tiles') or [];animals=collections.Counter();crops=collections.Counter();weed=0
   for col in tiles:
    if not isinstance(col,list):continue
    for tile in col:
     if isinstance(tile,dict):
      if tile.get('animal'):animals[tile['animal']]+=1
      if tile.get('kind')=='PLANT':crops[tile.get('crop','?')]+=1
      if tile.get('kind')=='WEED':weed+=1
   routed=None
   if len(steps)>2:
    o=steps[2][seat].get('observation') or {}
    try:routed=len(o['farms'][1-seat]['hands'])==0 and float(o['market']['inventory']['WHEAT'])>=9986
    except Exception:pass
   games.append({'episode_id':r.get('info',{}).get('EpisodeId'),'file':path.name,'seat':seat,'opponent':opp,'own_reward':own,'opponent_reward':other,'margin':own-other,'win':own>other,'status_counts':dict(statuses),'router_condition_step1':routed,'unit_actions':dict(counts),'market_actions':dict(markets),'final_money':farm.get('money'),'final_animals':dict(animals),'final_crops':dict(crops),'final_weed':weed})
 if not games:raise ValueError(f'no analyzable games in {folder}')
 losses=[g for g in games if not g['win']]
 return {'submission_id':submission_id,'team':team,'games':len(games),'wins':sum(g['win'] for g in games),'losses':len(losses),'mean_reward':statistics.mean(g['own_reward'] for g in games),'median_reward':statistics.median(g['own_reward'] for g in games),'mean_margin':statistics.mean(g['margin'] for g in games),'router_activations':sum(g['router_condition_step1'] is True for g in games),'zero_or_failed_rewards':sum(g['own_reward']<=0 for g in games),'games_detail':games}
def main():
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--submission',action='append',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out={'format':'live-submission-replay-analysis-v1','submissions':{sid:summarize(a.input/sid,sid) for sid in a.submission}}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({sid:{k:v[k] for k in ('games','wins','losses','mean_reward','mean_margin','router_activations','zero_or_failed_rewards')} for sid,v in out['submissions'].items()},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
