#!/usr/bin/env python3
"""Contrast episode-level control outcomes with executed TOP49 opponent actions."""
from __future__ import annotations
import collections,gzip,json,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'kaggriculture/research'
def won(row): return row['wins']>0
def features(player,episode):
 with gzip.open(ROOT/f'kaggriculture/top49_full/{episode}/replay.json.gz','rt') as f:r=json.load(f)
 side=r['info']['TeamNames'].index(player);acts=[x[side].get('action') or {} for x in r['steps'][1:]];out={}
 for h in (1,2,5,20,720):
  c=collections.Counter()
  for a in acts[:h]:
   for o in a.get('market',[]):
    typ=o[0];c[typ]+=1
    if len(o)>2 and isinstance(o[2],(int,float)):c[f'{typ}:{o[1]}']+=o[2]
  keys=('BUY_PRODUCT:WHEAT','SELL:WHEAT','BUY_PRODUCT:FERTILIZER','SELL:FERTILIZER','SELL:MILK','SELL:WOOL','SELL:STRAWBERRY','SELL:MELON','HIRE','BUY_ANIMAL:COW','BUY_ANIMAL:SHEEP','BUY_ANIMAL:GOOSE')
  if h==720: keys=('HIRE','BUY_ANIMAL:COW','BUY_ANIMAL:SHEEP','BUY_ANIMAL:GOOSE')
  for key in keys: out[f't{h}:{key}']=c[key]
 return out
def main():
 d=json.load(open(R/'TOP49_ALL5_EPISODES.json',encoding='utf8'));maps={a:{(x['player'],x['episode']):x for x in rows} for a,rows in d.items()};keys=sorted(maps['v8_aastik']);groups=collections.defaultdict(list)
 for k in keys:
  a=won(maps['v8_aastik'][k]);h=won(maps['v8_hybrid'][k]);v7=won(maps['v7_scripted'][k]);v9=won(maps['v9_b11_s07'][k]);f=features(*k)
  groups['both_win' if a and h else 'aastik_only' if a else 'hybrid_only' if h else 'both_lose'].append((k,f))
  if v7 and not v9:groups['v7_only'].append((k,f))
  if v9 and not v7:groups['v9_only'].append((k,f))
  if not v7 and not v9:groups['v7_v9_both_lose'].append((k,f))
 def contrasts(left,right):
  fs=sorted(next(iter(groups[left]))[1]);rows=[]
  for f in fs:
   x=[z[f] for _,z in groups[left]];y=[z[f] for _,z in groups[right]];allv=x+y;sd=statistics.pstdev(allv) or 1
   rows.append({'feature':f,'left_mean':statistics.mean(x),'right_mean':statistics.mean(y),'standardized_delta':(statistics.mean(x)-statistics.mean(y))/sd})
  return sorted(rows,key=lambda x:abs(x['standardized_delta']),reverse=True)[:15]
 out={'counts':{k:len(v) for k,v in groups.items()},'v7_only_players':collections.Counter(k[0] for k,_ in groups['v7_only']).most_common(),'v9_only_players':collections.Counter(k[0] for k,_ in groups['v9_only']).most_common(),'contrasts':{'v7_only_vs_v9_only':contrasts('v7_only','v9_only'),'both_lose_vs_both_win':contrasts('both_lose','both_win')}}
 json.dump(out,open(R/'V9_CONTRAST.json','w'),ensure_ascii=False,indent=2)
 lines=['# V9 episode-level contrast report','',f"Analyzed **{len(keys)}** TOP49 player-tapes, with both seats retained in each outcome row.",'','## Outcome funnel','']
 for k in ('both_win','aastik_only','hybrid_only','both_lose','v7_only','v9_only','v7_v9_both_lose'):lines.append(f'- `{k}`: **{out["counts"].get(k,0)}** episodes')
 for title,key in [('V7-only versus B11/S07-only','v7_only_vs_v9_only'),('Aastik/hybrid common losses versus common wins','both_lose_vs_both_win')]:
  lines += ['',f'## {title}','','| feature | left mean | right mean | standardized delta |','|---|---:|---:|---:|']
  for x in out['contrasts'][key]:lines.append(f"| {x['feature']} | {x['left_mean']:.2f} | {x['right_mean']:.2f} | {x['standardized_delta']:+.2f} |")
 lines += ['','These are diagnostic associations from opponent-emitted replay actions, not causal promotion evidence. Any mutation still requires observation-level checks, identical-seed controls, and fresh holdouts.','']
 (R/'V9_CONTRAST_REPORT.md').write_text('\n'.join(lines),encoding='utf8')
 print('\n'.join(lines[:20]))
if __name__=='__main__':main()
