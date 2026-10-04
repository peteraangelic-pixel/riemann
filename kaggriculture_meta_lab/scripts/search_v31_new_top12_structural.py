#!/usr/bin/env python3
"""Search the refreshed TOP12 for a transferable four-quadrant structural parent."""
from __future__ import annotations
import argparse,base64,json,statistics,sys,tempfile,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'rust_port/tools'),str(ROOT/'scripts')]
from benchmark_top30 import build_top30_jobs
from kaggriculture_lab.rust_backend import _source
from rust_client import Job,replay_many
from search_v24_live_dynamic_market import live_records

def phase(candidates,records,binary,threads):
 with tempfile.TemporaryDirectory(prefix='v31-') as td:
  td=Path(td);cp=[];op=[]
  for i,(_,src,_) in enumerate(candidates):p=td/f'c{i}.json';p.write_text(json.dumps(src.actions));cp.append(p)
  for i,(spec,seed,group) in enumerate(records):
   src=_source(spec);assert src is not None
   p=td/f'o{i}.json';p.write_text(json.dumps(src.actions));op.append((p,int(seed),group))
  jobs=[];labels=[]
  for ci,c in enumerate(cp):
   for p,seed,g in op:
    for seat in (0,1):jobs.append(Job(seed,c,p,reverse=bool(seat)));labels.append((ci,g))
  raw=replay_many(jobs,binary=binary,steps=720,threads=threads,trim_hands_a=True,trim_hands_b=False,allow_errors=True,timeout=1500)
 rows=[]
 for r,(ci,g) in zip(raw,labels):
  if r.get('errors') or r.get('rewards') is None:raise RuntimeError(r.get('errors'))
  a,b=map(float,r['rewards']);rows.append((ci,g,a,b,a-b))
 out={}
 for ci in range(len(candidates)):
  z=[r for r in rows if r[0]==ci];groups={}
  for g in sorted(set(r[1] for r in z)):
   q=[r for r in z if r[1]==g];groups[g]={'games':len(q),'wins':sum(r[4]>0 for r in q),'losses':sum(r[4]<0 for r in q),'ties':sum(r[4]==0 for r in q),'mean_reward':statistics.mean(r[2] for r in q),'mean_margin':statistics.mean(r[4] for r in q)}
  out[ci]={'games':len(z),'wins':sum(r[4]>0 for r in z),'losses':sum(r[4]<0 for r in z),'ties':sum(r[4]==0 for r in z),'mean_reward':statistics.mean(r[2] for r in z),'mean_margin':statistics.mean(r[4] for r in z),'groups':groups}
 return out,len(jobs)
def key(v):return v['wins']+.5*v['ties'],v['mean_reward'],v['mean_margin']
def emit(path,actions):
 blob=base64.b85encode(zlib.compress(json.dumps(actions,separators=(',',':')).encode(),9));path.parent.mkdir(parents=True,exist_ok=True);path.write_text(f'''\"\"\"Neutral V31 refreshed-meta structural candidate.\"\"\"\nimport base64,copy,json,zlib\nA=json.loads(zlib.decompress(base64.b85decode({blob!r})))\ndef agent(o,c=None):\n p=int(o.get("player",0));s=min(int(o.get("step",0)),len(A[p])-1);a=copy.deepcopy(A[p][s]);a["hands"]=(a.get("hands") or [])[:len(o["farms"][p].get("hands") or [])];return a\nact=agent\n''')
def main():
 p=argparse.ArgumentParser();p.add_argument('--corpus',type=Path,required=True);p.add_argument('--live',type=Path,required=True);p.add_argument('--binary',type=Path,required=True);p.add_argument('--threads',type=int,default=4);p.add_argument('--output',type=Path,required=True);p.add_argument('--agent-output',type=Path,required=True);a=p.parse_args()
 v2p=ROOT/'agents/variants/agent_v16_kanno_top7_champion.py';g2p=ROOT/'agents/candidates/agent_v8_control_g2_open_loop.py';jobs,meta=build_top30_jobs(a.corpus.resolve(),v2p,12);records=[]
 for i in range(0,len(jobs),2):records.append((jobs[i][2],jobs[i][0],f"rank{meta[i]['rank']:02d}"))
 donors=[]
 for i,(spec,_,_) in enumerate(records):src=_source(spec);assert src;donors.append((f'p{i:03d}',src,meta[2*i] if 2*i<len(meta) else {}))
 best=[];seen=set()
 for i in range(0,len(jobs),2):
  m=meta[i]
  if m['best_listed_submission'] and m['rank'] not in seen:seen.add(m['rank']);best.append((jobs[i][2],210000,'train'))
 train_records=[]
 for spec,_,_ in best:
  for seed in range(210000,210002):train_records.append((spec,seed,'train'))
 train,tj=phase(donors,train_records,a.binary,a.threads);final_ids=sorted(train,key=lambda i:key(train[i]),reverse=True)[:12]
 controls=[]
 for name,path in [('v2',v2p),('g2',g2p)]:src=_source(str(path.resolve()));assert src;controls.append((name,src,{}))
 finalists=[donors[i] for i in final_ids]+controls
 hold_records=records+live_records(a.live)+[(str(v2p.resolve()),211000+i,'v2') for i in range(8)]+[(str(g2p.resolve()),211000+i,'g2') for i in range(8)]
 hold,hj=phase(finalists,hold_records,a.binary,a.threads);v2i=len(finalists)-2;base=hold[v2i]
 eligible=[]
 for i in range(len(final_ids)):
  v=hold[i];live=sum(q['wins'] for g,q in v['groups'].items() if g.startswith('live-'));blive=sum(q['wins'] for g,q in base['groups'].items() if g.startswith('live-'))
  current=sum(q['wins'] for g,q in v['groups'].items() if g.startswith('rank'));bcurrent=sum(q['wins'] for g,q in base['groups'].items() if g.startswith('rank'))
  if key(v)>key(base) and live>=blive and current>=bcurrent+4 and v['groups']['g2']['wins']>=base['groups']['g2']['wins']-2:eligible.append(i)
 winner=max(eligible,key=lambda i:key(hold[i])) if eligible else v2i;emit(a.agent_output,finalists[winner][1].actions)
 report={'format':'v31-new-top12-structural-search-v1','donors':len(donors),'train_jobs':tj,'holdout_jobs':hj,'finalists':[{'source_index':final_ids[i],'candidate_id':finalists[i][0],'train':train[final_ids[i]],'holdout':hold[i]} for i in range(len(final_ids))],'controls':{'v2':base,'g2':hold[len(finalists)-1]},'winner_index':winner,'winner_id':finalists[winner][0],'winner_holdout':hold[winner],'eligible':eligible}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'donors':len(donors),'train_jobs':tj,'holdout_jobs':hj,'winner_id':report['winner_id'],'eligible':eligible,'v2':base,'winner':hold[winner]},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
