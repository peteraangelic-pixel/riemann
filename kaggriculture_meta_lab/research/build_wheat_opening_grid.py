#!/usr/bin/env python3
"""Build isolated Aastik t0/t1 wheat opening grid."""
from __future__ import annotations
import base64,importlib.util,json,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'kaggriculture/v9_candidates/wheat_grid'
def load():
 s=importlib.util.spec_from_file_location('a',ROOT/'kaggriculture/agent_v8_aastik.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m.ACTIONS
def main():
 base=load();OUT.mkdir(parents=True,exist_ok=True);manifest=[]
 for buy in (5,7,8,9,10,11,12,13,17,21,25,30):
  for reserve in (4,2,0):
   sell=buy-reserve;actions=json.loads(json.dumps(base));actions[0]['market']=[['BUY_PRODUCT','WHEAT',buy]]
   orders=actions[1]['market'];orders[0]=['SELL','WHEAT',sell]
   payload=base64.b85encode(zlib.compress(json.dumps(actions,separators=(',',':')).encode(),9)).decode();name=f'agent_v9_wheat_b{buy:02d}_s{sell:02d}'
   (OUT/f'{name}.py').write_text('"""Aastik with isolated t0/t1 wheat quantities."""\nimport base64,copy,json,zlib\ndef _d(x):return json.loads(zlib.decompress(base64.b85decode(x)).decode())\n'+f'ACTIONS=_d({payload!r})\nBUY_WHEAT={buy}\nSELL_WHEAT={sell}\n' + "def act(observation,configuration):\n player=int(observation.get('player',0));step=min(int(observation.get('step',0)),719);action=copy.deepcopy(ACTIONS[step]);farms=observation.get('farms') or [];hands=(farms[player].get('hands') or []) if player<len(farms) else [];action['hands']=action.get('hands',[])[:len(hands)];return action\ndef agent(observation,configuration):return act(observation,configuration)\n",encoding='utf8')
   manifest.append({'name':name,'buy':buy,'sell':sell,'control':buy==13 and sell==9})
 (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('built',len(manifest))
if __name__=='__main__':main()
