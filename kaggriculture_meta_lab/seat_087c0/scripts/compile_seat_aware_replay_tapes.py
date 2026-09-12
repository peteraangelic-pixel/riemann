#!/usr/bin/env python3
"""Compile best-reward replay separately per seat into a two-stream static tape."""
from __future__ import annotations
import argparse,base64,json,re,zlib
from pathlib import Path
EMPTY={"farmer":["PASS"],"hands":[],"market":[]}
def slug(s): return re.sub(r'[^a-z0-9]+','_',s.casefold()).strip('_') or 'team'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('corpus',type=Path);ap.add_argument('outdir',type=Path);ap.add_argument('--min-score',type=float,default=0);a=ap.parse_args();a.outdir.mkdir(parents=True,exist_ok=True); panel=[]
 for mp in sorted(a.corpus.glob('*/manifest.json')):
  man=json.loads(mp.read_text()); name=man['team_name']; score=float(man.get('leaderboard_score',0) or 0)
  if score<a.min_score: continue
  best={}
  for rp in mp.parent.glob('replay_*.json'):
   d=json.loads(rp.read_text()); names=(d.get('info') or {}).get('TeamNames',[])
   seat=next((i for i,x in enumerate(names) if x.casefold()==name.casefold()),None)
   if seat is None: continue
   reward=(d.get('rewards') or [None,None])[seat]
   actions=[(row[seat].get('action') if len(row)>seat else None) or dict(EMPTY) for row in d['steps'][1:]]
   item={'reward':reward,'episode':(d.get('info') or {}).get('EpisodeId'),'opponent':names[1-seat],'actions':actions}
   if seat not in best or (reward or -1)>(best[seat]['reward'] or -1): best[seat]=item
  if set(best)!={0,1}: print('skip',name,'missing seat',set(best));continue
  streams=[best[0].pop('actions'),best[1].pop('actions')]; assert all(len(x)==719 for x in streams)
  blob=base64.b85encode(zlib.compress(json.dumps(streams,separators=(',',':')).encode(),9)).decode()
  src=f'''"""Seat-aware best-reward tape for {name}, leaderboard {score}."""\nimport base64,copy,json,zlib\nACTIONS=json.loads(zlib.decompress(base64.b85decode({blob!r})).decode())\ndef agent(observation,configuration=None):\n p=int(observation.get("player",0)); step=min(int(observation.get("step",0)),718)\n a=copy.deepcopy(ACTIONS[p][step]); a["hands"]=a.get("hands",[])[:len(observation["farms"][p].get("hands") or [])]\n return a\nact=agent\n'''
  path=a.outdir/(slug(name)+'_seat_aware.py');path.write_text(src); panel.append({'team':name,'score':score,'path':str(path),'seat0':best[0],'seat1':best[1]})
 (a.outdir/'panel.json').write_text(json.dumps(panel,indent=2,ensure_ascii=False));print(json.dumps(panel,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
