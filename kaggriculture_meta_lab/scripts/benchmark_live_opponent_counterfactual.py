#!/usr/bin/env python3
"""Counterfactual static-agent panel against exact recent live opponent tapes."""
from __future__ import annotations
import argparse,collections,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kaggriculture_lab import rust_backend

def load(p):
 with p.open(encoding='utf-8-sig') as f:return json.load(f)
def common_team(replays):
 c=collections.Counter()
 for _,r in replays:c.update(set(r.get('info',{}).get('TeamNames') or []))
 return c.most_common(1)[0][0]
def stat(rows):
 return {'games':len(rows),'wins':sum(r['margin']>0 for r in rows),'losses':sum(r['margin']<0 for r in rows),'ties':sum(r['margin']==0 for r in rows),'mean_reward':statistics.mean(r['self_reward'] for r in rows),'mean_margin':statistics.mean(r['margin'] for r in rows),'seat0_wins':sum(r['margin']>0 and r['candidate_seat']==0 for r in rows),'seat1_wins':sum(r['margin']>0 and r['candidate_seat']==1 for r in rows)}
def main():
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--candidate',action='append',required=True);p.add_argument('--workers',type=int,default=4);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 candidates={};
 for spec in a.candidate:
  n,sep,path=spec.partition('=');
  if not sep:raise ValueError(spec)
  candidates[n]=Path(path).resolve()
 records=[]
 for folder in sorted(x for x in a.input.iterdir() if x.is_dir()):
  rr=[(f,load(f)) for f in sorted(folder.rglob('*.json'))];team=common_team(rr)
  for f,r in rr:
   names=r.get('info',{}).get('TeamNames') or [];seats=[i for i,n in enumerate(names) if n==team]
   if len(seats)!=1:continue
   own=seats[0];seed=r.get('info',{}).get('seed',0)
   if not isinstance(seed,int) or isinstance(seed,bool):seed=0
   records.append({'submission':folder.name,'episode_id':r.get('info',{}).get('EpisodeId'),'recorded_own_seat':own,'opponent':names[1-own],'seed':seed,'spec':f'tape:{f.resolve()}#{1-own}'})
 jobs=[];labels=[]
 for name,path in candidates.items():
  for rec in records:
   for seat in (0,1):jobs.append((rec['seed'],str(path),rec['spec'],seat,720,rec['submission']));labels.append((name,rec,seat))
 rows=rust_backend.run_rust(jobs,a.workers,progress_every=50);outrows=[]
 for r,(name,rec,seat) in zip(rows,labels):outrows.append({**r,'candidate':name,'source_submission':rec['submission'],'source_episode_id':rec['episode_id'],'opponent_team':rec['opponent'],'candidate_seat':seat,'matches_recorded_seat':seat==rec['recorded_own_seat']})
 failed=[r for r in outrows if r.get('error')]
 if failed:raise RuntimeError(f'{len(failed)} failed games: {failed[:2]}')
 summary={}
 for name in candidates:
  cr=[r for r in outrows if r['candidate']==name];summary[name]={'all':stat(cr),'by_source_submission':{sid:stat([r for r in cr if r['source_submission']==sid]) for sid in sorted({r['source_submission'] for r in cr})},'recorded_seat_only':stat([r for r in cr if r['matches_recorded_seat']])}
 out={'format':'live-opponent-counterfactual-v1','records':len(records),'jobs':len(jobs),'summary':summary,'rows':outrows};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
