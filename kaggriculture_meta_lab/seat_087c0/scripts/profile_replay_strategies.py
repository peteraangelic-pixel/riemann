#!/usr/bin/env python3
"""Profile timing and action mix of replay policies, split by team and seat."""
from __future__ import annotations
import argparse, collections, json
from pathlib import Path

KEYS=('BUY_LAND','BUILD_PASTURE','BUY_COW','BUY_SHEEP','BUY_GOOSE','PLACE','FEED','CARE','COLLECT','PLANT','WATER','HARVEST','BUY','SELL','HIRE','FIRE')
PRODUCTS=('WHEAT','CARROT','STRAWBERRY','TOMATO','MELON','FERTILIZER','MILK','WOOL','EGG','COW','SHEEP','GOOSE')

def flat(action):
    if not isinstance(action,dict): return []
    commands=[]
    farmer=action.get('farmer')
    if isinstance(farmer,list) and farmer: commands.append(farmer)
    for channel in ('hands','market'):
        for cmd in action.get(channel,[]) or []:
            if isinstance(cmd,list) and cmd: commands.append(cmd)
    return [' '.join(map(str,cmd)) for cmd in commands]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('corpus',type=Path); ap.add_argument('--output',type=Path,required=True); ap.add_argument('--min-score',type=float,default=3000)
    a=ap.parse_args(); report={'corpus':str(a.corpus),'min_score':a.min_score,'teams':[]}
    for mp in sorted(a.corpus.glob('*/manifest.json')):
        man=json.loads(mp.read_text()); score=float(man.get('leaderboard_score',0) or 0)
        if score<a.min_score: continue
        selected={int(x['episode_id']):x for x in man.get('selected_episodes',[])}
        team={'name':man['team_name'],'score':score,'team_id':man.get('team_id'),'episodes':[]}
        for rp in sorted(mp.parent.glob('replay_*.json')):
            d=json.loads(rp.read_text()); eid=int((d.get('info') or {}).get('EpisodeId') or rp.stem.rsplit('_',1)[-1]); meta=selected.get(eid,{})
            seat=meta.get('seat')
            if seat is None:
                names=(d.get('info') or {}).get('TeamNames',[])
                seat=next((i for i,n in enumerate(names) if n==man['team_name']),None)
            if seat is None: continue
            counts=collections.Counter(); first={}; last={}; by_day=collections.Counter()
            for t,step in enumerate(d.get('steps',[])):
                if seat>=len(step): continue
                obs=step[seat].get('observation') or {}; day=int(obs.get('day',t//24)); hour=int(obs.get('hour',t%24))
                for cmd in flat(step[seat].get('action')):
                    head=cmd.split()[0] if cmd else ''
                    counts[head]+=1; by_day[f'{day}:{head}']+=1
                    first.setdefault(head,{'t':t,'day':day,'hour':hour,'cmd':cmd}); last[head]={'t':t,'day':day,'hour':hour,'cmd':cmd}
                    for p in PRODUCTS:
                        if p in cmd: counts[f'{head}_{p}']+=1
            team['episodes'].append({'episode_id':eid,'seat':seat,'reward':meta.get('reward'),'opponent':meta.get('opponent_team_name'),
              'counts':dict(counts),'first':first,'last':last,'by_day':dict(by_day)})
        # Aggregate medians/min/max are left transparent as per-episode values plus totals.
        totals=collections.Counter()
        for e in team['episodes']: totals.update(e['counts'])
        team['totals']=dict(totals); report['teams'].append(team)
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)); print(json.dumps([{'name':t['name'],'score':t['score'],'episodes':len(t['episodes']),'totals':t['totals']} for t in report['teams']],ensure_ascii=False,indent=2))
if __name__=='__main__': main()
