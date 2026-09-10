#!/usr/bin/env python3
"""Compose a preregistered latched V7/hybrid router from matched static rows."""
from __future__ import annotations
import argparse,json,statistics
from collections import defaultdict
from pathlib import Path

LOW=3000.0
HIGH=3010.0

def summary(rows):
 margins=[r['margin'] for r in rows];wins=sum(r['outcome']=='win' for r in rows);ties=sum(r['outcome']=='tie' for r in rows)
 return {'games':len(rows),'wins':wins,'losses':len(rows)-wins-ties,'ties':ties,'errors':sum(bool(r.get('error')) for r in rows),'score_rate':(wins+.5*ties)/len(rows),'mean_reward':statistics.mean(r['self_reward'] for r in rows),'mean_margin':statistics.mean(margins),'q10_margin':sorted(margins)[max(0,int(.1*len(margins))-1)]}

def main():
 p=argparse.ArgumentParser();p.add_argument('--matched',type=Path,required=True);p.add_argument('--fingerprints',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 d=json.load(open(a.matched));f=json.load(open(a.fingerprints));fm={(x['team'],int(x['episode_id']),int(x['candidate_seat'])):x for x in f['rows']}
 by=defaultdict(dict)
 for r in d['rows']:
  if r['candidate'] in ('v7','hybrid'):
   key=(r['team'],int(r['source_episode_id']),int(r['seat']),int(r['seed']));by[key][r['candidate']]=r
 rows=[];activation_keys=set()
 for key,q in by.items():
  if set(q)!= {'v7','hybrid'}:raise RuntimeError(f'unmatched rows: {key}')
  fk=key[:3];x=fm[fk];use=LOW<=float(x['own_money'])<=HIGH
  src=q['hybrid'] if use else q['v7'];rows.append({**src,'candidate':'router','router_used_hybrid':use,'route_own_money':x['own_money']})
  if use:activation_keys.add(fk)
 controls={c:[r for r in d['rows'] if r['candidate']==c] for c in ('v7','hybrid')}
 result={'format':'v8-latched-tail-router-composite-v1','rule':{'decision_turn':1,'hybrid_from_turn':2,'own_money_min':LOW,'own_money_max':HIGH,'default':'v7'},'activation_policy_seats':len(activation_keys),'summary':{'router':summary(rows),**{c:summary(v) for c,v in controls.items()}},'teams':{},'rows':rows}
 for team in sorted({r['team'] for r in rows}):result['teams'][team]={c:summary([r for r in rr if r['team']==team]) for c,rr in [('router',rows),*controls.items()]}
 if any(v['errors'] for v in result['summary'].values()):raise RuntimeError('failed games')
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('rule','activation_policy_seats','summary')},indent=2))
if __name__=='__main__':main()
