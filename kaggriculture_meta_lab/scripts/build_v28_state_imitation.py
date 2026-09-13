#!/usr/bin/env python3
"""Build a neutral reactive nearest-state policy from multiple 3000+ replay trajectories."""
from __future__ import annotations
import argparse,base64,json,zlib
from pathlib import Path
ITEMS=("WHEAT","CARROT","TOMATO","STRAWBERRY","MELON","EGG","MILK","WOOL","FERTILIZER")
CROPS=ITEMS[:5];ANIMALS=("GOOSE","COW","SHEEP")

def feature(obs,seat):
 farms=obs.get('farms') or []; own=farms[seat];opp=farms[1-seat];private=obs.get('private') or {};market=obs.get('market') or {}
 prices=market.get('prices') or {};stock=market.get('inventory') or {};shed=private.get('shed') or {};seeds=private.get('seeds') or {};inventories=private.get('inventories') or []
 board=own.get('tiles') or [];counts={x:0 for x in (*CROPS,*ANIMALS,'WEED')}
 units=[];positions=[own.get('farmer',[4,4]),*(own.get('hands') or [])]
 for i,pos in enumerate(positions):
  inv=inventories[i] if i<len(inventories) and isinstance(inventories[i],dict) else {};x,y=map(int,pos);tile=board[y][x] if 0<=y<len(board) and 0<=x<len(board[y]) else None
  if isinstance(tile,dict):
   local=(str(tile.get('kind') or ''),str(tile.get('crop') or ''),str(tile.get('animal') or ''),int(tile.get('yield_units',0) or 0),int(bool(tile.get('watered_today'))),int(bool(tile.get('fed_today'))),int(bool(tile.get('cared_today'))))
  else:local=(str(tile or ''),'','',0,0,0,0)
  units.append((x,y,sum(int(v or 0) for v in inv.values()),int(inv.get('WHEAT',0) or 0),int(inv.get('FERTILIZER',0) or 0),local))
 for row in board:
  for tile in row:
   if not isinstance(tile,dict):continue
   key=tile.get('crop') or tile.get('animal') or ('WEED' if tile.get('kind')=='WEED' else None)
   if key in counts:counts[key]+=1
 return {'m':round(float(own.get('money',0) or 0),2),'om':round(float(opp.get('money',0) or 0),2),'h':len(own.get('hands') or []),'oh':len(opp.get('hands') or []),'q':len(own.get('unlocked_quadrants') or []),'oq':len(opp.get('unlocked_quadrants') or []),'p':[round(float(prices.get(x,0) or 0),3) for x in ITEMS],'z':[round(float(stock.get(x,0) or 0),2) for x in ITEMS],'s':[int(shed.get(x,0) or 0) for x in ITEMS],'e':[int(seeds.get(x,0) or 0) for x in CROPS],'b':[counts[x] for x in (*CROPS,*ANIMALS,'WEED')],'u':units,'shop':sorted((obs.get('town') or {}).get('unlocked_shops') or [])}

def main():
 p=argparse.ArgumentParser();p.add_argument('--corpus',type=Path,required=True);p.add_argument('--rank',type=int,default=1);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 manifest=json.loads((a.corpus/'manifest.json').read_text(encoding='utf-8-sig'));team=next(t for t in manifest['teams'] if int(t['rank'])==a.rank);best=max(team['active_submissions'],key=lambda x:float(x['public_score']));episodes=[e for e in team['selected_episodes'] if int(e['submission_id'])==int(best['submission_id'])]
 trajectories=[]
 for entry in episodes:
  replay=json.loads((a.corpus/team['folder']/entry['file']).read_text(encoding='utf-8-sig'));seat=(replay['info']['TeamNames']).index(team['team_name']);trajectory=[]
  for step in range(min(719,len(replay['steps'])-1)):
   obs=replay['steps'][step][seat].get('observation') or {};action=replay['steps'][step+1][seat].get('action') or {'farmer':['PASS'],'hands':[],'market':[]};trajectory.append([feature(obs,seat),action])
  trajectories.append(trajectory)
 payload=base64.b85encode(zlib.compress(json.dumps(trajectories,separators=(',',':')).encode(),9))
 source='''\"\"\"Neutral V28 multi-trajectory state imitation policy.\"\"\"\nimport base64,copy,json,math,zlib\nD=json.loads(zlib.decompress(base64.b85decode(%r)))\nI=("WHEAT","CARROT","TOMATO","STRAWBERRY","MELON","EGG","MILK","WOOL","FERTILIZER");C=I[:5];N=("GOOSE","COW","SHEEP")\ndef F(o,p):\n f=o["farms"];w=f[p];v=f[1-p];r=o.get("private") or {};m=o.get("market") or {};P=m.get("prices") or {};Z=m.get("inventory") or {};S=r.get("shed") or {};E=r.get("seeds") or {};V=r.get("inventories") or [];B=w.get("tiles") or [];c={x:0 for x in C+N+("WEED",)};u=[]\n for i,a in enumerate([w.get("farmer",[4,4])]+(w.get("hands") or [])):\n  q=V[i] if i<len(V) and isinstance(V[i],dict) else {};x,y=map(int,a);t=B[y][x] if 0<=y<len(B) and 0<=x<len(B[y]) else None\n  if isinstance(t,dict):l=(str(t.get("kind") or ""),str(t.get("crop") or ""),str(t.get("animal") or ""),int(t.get("yield_units",0) or 0),int(bool(t.get("watered_today"))),int(bool(t.get("fed_today"))),int(bool(t.get("cared_today"))))\n  else:l=(str(t or ""),"","",0,0,0,0)\n  u.append((x,y,sum(int(k or 0) for k in q.values()),int(q.get("WHEAT",0) or 0),int(q.get("FERTILIZER",0) or 0),l))\n for R in B:\n  for t in R:\n   if isinstance(t,dict):\n    k=t.get("crop") or t.get("animal") or ("WEED" if t.get("kind")=="WEED" else None)\n    if k in c:c[k]+=1\n return {"m":float(w.get("money",0) or 0),"om":float(v.get("money",0) or 0),"h":len(w.get("hands") or []),"oh":len(v.get("hands") or []),"q":len(w.get("unlocked_quadrants") or []),"oq":len(v.get("unlocked_quadrants") or []),"p":[float(P.get(x,0) or 0) for x in I],"z":[float(Z.get(x,0) or 0) for x in I],"s":[int(S.get(x,0) or 0) for x in I],"e":[int(E.get(x,0) or 0) for x in C],"b":[c[x] for x in C+N+("WEED",)],"u":u,"shop":sorted((o.get("town") or {}).get("unlocked_shops") or [])}\ndef dist(a,b):\n d=10*abs(math.log1p(a["m"])-math.log1p(b["m"]))+8*abs(math.log1p(a["om"])-math.log1p(b["om"]))+100*abs(a["h"]-b["h"])+30*abs(a["oh"]-b["oh"])+140*abs(a["q"]-b["q"])+30*abs(a["oq"]-b["oq"])+20*len(set(a["shop"])^set(b["shop"]))\n d+=sum(abs(x-y)*.04 for x,y in zip(a["p"],b["p"]))+sum(abs(x-y)*.01 for x,y in zip(a["z"],b["z"]))+sum(abs(x-y)*.35 for x,y in zip(a["s"],b["s"]))+sum(abs(x-y)*2 for x,y in zip(a["e"],b["e"]))+sum(abs(x-y)*7 for x,y in zip(a["b"],b["b"]))\n d+=300*abs(len(a["u"])-len(b["u"]))\n for x,y in zip(a["u"],b["u"]):d+=35*(abs(x[0]-y[0])+abs(x[1]-y[1]))+.2*abs(x[2]-y[2])+abs(x[3]-y[3])+2*abs(x[4]-y[4])+120*(x[5][:3]!=tuple(y[5][:3]))+3*abs(x[5][3]-y[5][3])+15*sum(i!=j for i,j in zip(x[5][4:],y[5][4:]))\n return d\ndef agent(o,c=None):\n p=int(o.get("player",0));s=min(int(o.get("step",0)),718);f=F(o,p);q=min((t[s] for t in D if s<len(t)),key=lambda x:dist(f,x[0]))[1];q=copy.deepcopy(q);q["hands"]=(q.get("hands") or [])[:len(o["farms"][p].get("hands") or [])];return q\nact=agent\n'''%payload
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(source);print(json.dumps({'rank':a.rank,'source_score':best['public_score'],'trajectories':len(trajectories),'bytes':len(source)}))
if __name__=='__main__':main()
