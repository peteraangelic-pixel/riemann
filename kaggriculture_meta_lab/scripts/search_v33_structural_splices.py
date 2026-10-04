#!/usr/bin/env python3
"""Fail-closed splice census between refreshed four-quadrant tapes and V2."""
from __future__ import annotations
import argparse,copy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'rust_port/tools'),str(ROOT/'scripts')]
from benchmark_top30 import build_top30_jobs
from kaggriculture_lab.rust_backend import TapeSource,_source
from search_v24_live_dynamic_market import live_records
from search_v31_new_top12_structural import phase,key

def splice(d,v,cut,mode):
 out=[]
 for p in range(2):
  aa=[]
  for s in range(min(len(d.actions[p]),len(v.actions[p]))):
   da,va=copy.deepcopy(d.actions[p][s]),copy.deepcopy(v.actions[p][s])
   if mode=='full':a=da if s<cut else va
   elif mode=='donor-market':
    a=da
    if s>=cut:a['farmer']=va.get('farmer',['PASS']);a['hands']=va.get('hands',[])
   elif mode=='donor-units':
    a=da
    if s>=cut:a['market']=va.get('market',[])
   aa.append(a)
  out.append(aa)
 return TapeSource(actions=out,trim_hands=True)
def main():
 p=argparse.ArgumentParser();p.add_argument('--corpus',type=Path,required=True);p.add_argument('--live',type=Path,required=True);p.add_argument('--binary',type=Path,required=True);p.add_argument('--threads',type=int,default=4);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 v2p=ROOT/'agents/variants/agent_v16_kanno_top7_champion.py';g2p=ROOT/'agents/candidates/agent_v8_control_g2_open_loop.py';v2=_source(str(v2p.resolve()));assert v2
 jobs,meta=build_top30_jobs(a.corpus.resolve(),v2p,12);records=[(jobs[i][2],jobs[i][0],f"rank{meta[i]['rank']:02d}") for i in range(0,len(jobs),2)]
 cand=[]
 for idx in (37,70,97,106):
  d=_source(records[idx][0]);assert d
  cand.append((f'd{idx}-identity',d,{}))
  for day in range(4,25):
   cut=day*24
   for mode in ('full','donor-market','donor-units'):cand.append((f'd{idx}-{mode}-day{day}',splice(d,v2,cut,mode),{}))
 cand.extend([('v2',v2,{}),('g2',_source(str(g2p.resolve())),{})])
 hold=records+live_records(a.live)+[(str(v2p.resolve()),222000+i,'v2') for i in range(8)]+[(str(g2p.resolve()),222000+i,'g2') for i in range(8)]
 result,n=phase(cand,hold,a.binary,a.threads);base=result[len(cand)-2]
 eligible=[]
 def count(v,p):return sum(q['wins'] for g,q in v['groups'].items() if g.startswith(p))
 for i in range(len(cand)-2):
  v=result[i]
  if key(v)>key(base) and count(v,'rank')>=count(base,'rank')+4 and count(v,'live-')>=count(base,'live-') and v['groups']['g2']['wins']>=base['groups']['g2']['wins']-2:eligible.append(i)
 winner=max(eligible,key=lambda i:key(result[i])) if eligible else len(cand)-2
 report={'format':'v33-structural-splice-search-v1','candidates':len(cand),'jobs':n,'baseline_v2':base,'eligible':eligible,'winner_index':winner,'winner_id':cand[winner][0],'winner':result[winner],'ranking':[{'index':i,'id':cand[i][0],'summary':result[i]} for i in sorted(result,key=lambda i:key(result[i]),reverse=True)[:40]]}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('candidates','jobs','eligible','winner_id','winner')},indent=2))
if __name__=='__main__':main()
