#!/usr/bin/env python3
"""Exhaust all combinations of the 14 market steps separating our hybrid and peer V5."""
from __future__ import annotations
import argparse,base64,itertools,json,statistics,sys,tempfile,zlib
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'rust_port/tools')]
from kaggriculture_lab.rust_backend import _source
from rust_client import Job,replay_many

def source(p):x=_source(str(ROOT/p));assert x;return x.actions
def materialize(mask,ours,peer,diffs):
 out=[]
 for seat in (0,1):
  stream=[]
  for i,a in enumerate(ours[seat]):stream.append(peer[seat][i] if i in mask else a)
  out.append(stream)
 return out
def stat(m):
 n=len(m);w=sum(x>0 for x in m);l=sum(x<0 for x in m);t=n-w-l
 return {'games':n,'wins':w,'losses':l,'ties':t,'score_rate':(w+.5*t)/n,'mean_margin':statistics.mean(m),'worst_margin':min(m)}
def evaluate(masks,ours,peer,diffs,controls,seeds,binary,threads,td,tag):
 paths=[]
 for n,m in enumerate(masks):p=td/f'{tag}-{n}.json';p.write_text(json.dumps(materialize(m,ours,peer,diffs)));paths.append(p)
 jobs=[];meta=[]
 for i,p in enumerate(paths):
  for k,(op,ov) in controls.items():
   for seed in seeds:
    for seat in (0,1):jobs.append(Job(seed,p,op,reverse=bool(seat),overlay_b=ov));meta.append((i,k))
 rows=replay_many(jobs,binary=binary,steps=720,threads=threads,trim_hands_a=True,trim_hands_b=True,allow_errors=True,timeout=1200);d=defaultdict(list)
 for r,k in zip(rows,meta):
  if r.get('errors') or r.get('rewards') is None:raise RuntimeError(r.get('errors'))
  d[k].append(float(r['rewards'][0])-float(r['rewards'][1]))
 return [{k:stat(d[(i,k)]) for k in controls} for i in range(len(masks))],len(jobs)
def direct_fit(s):return (min(s['ours']['score_rate'],s['peer']['score_rate']),min(s['ours']['mean_margin'],s['peer']['mean_margin']),statistics.mean(x['mean_margin'] for x in s.values()))
def floor_fit(s,f):
 keys=[k for k in s if k not in ('ours','peer')];return (min(s[k]['score_rate']-f[k]['score_rate'] for k in keys),min(s[k]['mean_margin']-f[k]['mean_margin'] for k in keys),*direct_fit(s))
def render(a,note):
 b=base64.b85encode(zlib.compress(json.dumps(a,separators=(',',':')).encode(),9)).decode()
 return f'''# Exhaustive hybrid of the 14 market deltas between our hybrid and peer V5. {note}\nimport base64,copy,json,zlib\nACTIONS=json.loads(zlib.decompress(base64.b85decode({b!r})))\ndef agent(observation, configuration):\n    p=int(observation.get("player",0));step=min(int(observation.get("step",0)),len(ACTIONS[p])-1)\n    action=copy.deepcopy(ACTIONS[p][step]);action["hands"]=action.get("hands",[])[:len(observation["farms"][p]["hands"])]\n    return action\nact=agent\n'''
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--binary',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--agent-output',type=Path,required=True);ap.add_argument('--threads',type=int,default=4);a=ap.parse_args()
 ours=source('agents/candidates/ours_peer_v4_hybrid_holdout_winner.py');peer=source('agents/candidates/peer_v5_evolved.py');assert all(ours[s][i].get('farmer')==peer[s][i].get('farmer') and ours[s][i].get('hands')==peer[s][i].get('hands') for s in (0,1) for i in range(719));diffs=[i for i in range(719) if ours[0][i].get('market')!=peer[0][i].get('market')];assert len(diffs)==14,diffs
 all_masks=[frozenset(diffs[j] for j in range(len(diffs)) if bits>>j&1) for bits in range(1<<len(diffs))]
 with tempfile.TemporaryDirectory(prefix='v5-delta-exhaust-') as raw:
  td=Path(raw);gp=td/'g2.json';gp.write_text(json.dumps({'enabled':True,'start_day':6,'cash_reserve':250,'milk_reserve':1}));parent_controls={}
  for n,pth in {'ours':'agents/candidates/ours_peer_v4_hybrid_holdout_winner.py','peer':'agents/candidates/peer_v5_evolved.py'}.items():x=source(pth);p=td/f'{n}.json';p.write_text(json.dumps(x));parent_controls[n]=(p,None)
  s1,j1=evaluate(all_masks,ours,peer,diffs,parent_controls,range(98000,98004),a.binary,a.threads,td,'s1');rank=sorted(range(len(all_masks)),key=lambda i:direct_fit(s1[i]),reverse=True);stage2=[all_masks[i] for i in rank[:512]]
  paths={'ours':'agents/candidates/ours_peer_v4_hybrid_holdout_winner.py','peer':'agents/candidates/peer_v5_evolved.py','v3':'agents/candidates/top7_kanno_ep107381285_v3_sibling.py','v16':'agents/variants/agent_v16_kanno_top7_champion.py','german':'agents/candidates/champion_tape_germanjurado1.py','b21':'agents/current/agent_v9_b21_s16.py','g2':'agents/variants/agent_v10_subin_106845775.py','yusuke':'agents/candidates/top7_yusuke_best_ep107377081.py'};controls={}
  for n,pth in paths.items():x=source(pth);p=td/f'c-{n}.json';p.write_text(json.dumps(x));controls[n]=(p,gp if n=='g2' else None)
  s2,j2=evaluate(stage2,ours,peer,diffs,controls,range(98100,98108),a.binary,a.threads,td,'s2');io=stage2.index(frozenset()) if frozenset() in stage2 else None;ip=stage2.index(frozenset(diffs)) if frozenset(diffs) in stage2 else None
  # Parent floors are evaluated explicitly if an endpoint fell outside the direct top 512.
  panel=list(stage2)
  for m in (frozenset(),frozenset(diffs)):
   if m not in panel:panel.append(m)
  if len(panel)!=len(stage2):s2,jx=evaluate(panel,ours,peer,diffs,controls,range(98100,98108),a.binary,a.threads,td,'s2b');j2+=jx
  bo=s2[panel.index(frozenset())];bp=s2[panel.index(frozenset(diffs))];floors={k:{'score_rate':min(bo[k]['score_rate'],bp[k]['score_rate']),'mean_margin':min(bo[k]['mean_margin'],bp[k]['mean_margin'])} for k in controls};rank2=sorted(range(len(stage2)),key=lambda i:floor_fit(s2[i],floors),reverse=True);finals=[stage2[i] for i in rank2[:32]]
  for m in (frozenset(),frozenset(diffs)):
   if m not in finals:finals.append(m)
  hs,j3=evaluate(finals,ours,peer,diffs,controls,range(99000,99064),a.binary,a.threads,td,'holdout');bo=hs[finals.index(frozenset())];bp=hs[finals.index(frozenset(diffs))];floors={k:{'score_rate':min(bo[k]['score_rate'],bp[k]['score_rate']),'mean_margin':min(bo[k]['mean_margin'],bp[k]['mean_margin'])} for k in controls};eligible=[]
  for i,s in enumerate(hs):
   direct=all(s[k]['score_rate']>.55 and s[k]['mean_margin']>5 for k in ('ours','peer'));guard=all(s[k]['score_rate']>=floors[k]['score_rate']-.01 and s[k]['mean_margin']>=floors[k]['mean_margin']-250 for k in controls if k not in ('ours','peer'))
   if direct and guard:eligible.append(i)
  winner=max(eligible,key=lambda i:floor_fit(hs[i],floors)) if eligible else max(range(len(finals)),key=lambda i:floor_fit(hs[i],floors));emitted=bool(eligible);mask=finals[winner]
  out={'format':'peer-v5-14-delta-exhaustive-v1','difference_steps':diffs,'combinations':len(all_masks),'total_jobs':j1+j2+j3,'stage1_top_indexes':rank[:64],'holdout_seeds':[99000,99063],'ours_baseline':bo,'peer_baseline':bp,'finalists':[{'peer_steps':sorted(m),'stats':s,'fitness':list(floor_fit(s,floors))} for m,s in zip(finals,hs)],'eligible':eligible,'winner_index':winner,'winner_peer_steps':sorted(mask),'winner':hs[winner],'emitted':emitted};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2)+'\n')
  if emitted:a.agent_output.parent.mkdir(parents=True,exist_ok=True);a.agent_output.write_text(render(materialize(mask,ours,peer,diffs),f'peer steps={sorted(mask)}, holdout 99000-99063'))
  print(json.dumps({k:out[k] for k in ('combinations','total_jobs','eligible','winner_index','winner_peer_steps','emitted')},indent=2));print(json.dumps(hs[winner],indent=2))
if __name__=='__main__':main()
