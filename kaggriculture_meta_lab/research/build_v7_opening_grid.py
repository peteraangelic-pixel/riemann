#!/usr/bin/env python3
"""Build isolated two-seat V7 opening mutations as V9 candidates."""
from __future__ import annotations
import base64,copy,importlib.util,json,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'kaggriculture/v9_candidates/v7_opening_grid'
def load():
 s=importlib.util.spec_from_file_location('v7',ROOT/'kaggriculture/agent_v7_scripted.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m.ACTIONS
def main():
 base=load();OUT.mkdir(parents=True,exist_ok=True);manifest=[]
 for buy in (9,13,17,21,25,30,35):
  for reserve in (3,5,7):
   sell=buy-reserve; schedules=copy.deepcopy(base)
   for actions in schedules:
    actions[0]['market']=[['BUY_PRODUCT','WHEAT',buy]]
    actions[1]['market'][0]=['SELL','WHEAT',sell]
   payload=base64.b85encode(zlib.compress(json.dumps(schedules,separators=(',',':')).encode(),9)).decode();name=f'agent_v9_v7w_b{buy:02d}_s{sell:02d}'
   source='''"""V7 with isolated two-seat t0/t1 wheat quantities."""\nimport base64,copy,json,zlib\nACTIONS=json.loads(zlib.decompress(base64.b85decode(PAYLOAD)).decode())\ndef agent(observation,configuration):\n p=int(observation.get("player",0)); step=min(int(observation.get("step",0)),719); action=copy.deepcopy(ACTIONS[p][step]); farms=observation.get("farms") or []; hands=(farms[p].get("hands") or []) if p<len(farms) else []; action["hands"]=(action.get("hands") or [])[:len(hands)]; return action\nact=agent\n'''.replace('PAYLOAD',repr(payload))
   (OUT/f'{name}.py').write_text(source,encoding='utf8');manifest.append({'name':name,'buy':buy,'sell':sell,'reserve':reserve,'control':buy==30 and sell==25})
 (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('built',len(manifest))
if __name__=='__main__':main()
