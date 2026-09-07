#!/usr/bin/env python3
"""Build isolated delayed28-opening → Aastik boundary candidates."""
from __future__ import annotations
import base64, importlib.util, json, zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'kaggriculture/v9_candidates/primitives'
DURATIONS=(1,2,3,5,8,16)

def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def main():
 a=load(ROOT/'kaggriculture/agent_v8_aastik.py','aastik_source')
 d=load(ROOT/'kaggriculture/v9_candidates/agent_v9_third_delayed28_01.py','delayed_source')
 OUT.mkdir(parents=True,exist_ok=True); manifest=[]
 for mode in ('market','full'):
  for duration in DURATIONS:
   actions=[]
   for step,(base,source) in enumerate(zip(a.ACTIONS,d.ACTIONS)):
    action=json.loads(json.dumps(base))
    if step<duration:
     if mode=='market':action['market']=json.loads(json.dumps(source['market']))
     else:action=json.loads(json.dumps(source))
    actions.append(action)
   name=f'agent_v9_d28_{mode}_{duration:02d}'
   payload=base64.b85encode(zlib.compress(json.dumps(actions,separators=(',',':')).encode(),9)).decode()
   (OUT/f'{name}.py').write_text(
    '"""Isolated delayed28 opening boundary over frozen Aastik."""\n'
    'import base64,copy,json,zlib\n'
    'def _d(x): return json.loads(zlib.decompress(base64.b85decode(x)).decode())\n'
    +f'ACTIONS=_d({payload!r})\nMODE={mode!r}\nSWITCH_STEP={duration}\n'
    "def act(observation,configuration):\n"
    " player=int(observation.get('player',0)); step=min(int(observation.get('step',0)),719); action=copy.deepcopy(ACTIONS[step]); farms=observation.get('farms') or []; hands=(farms[player].get('hands') or []) if player<len(farms) else []; action['hands']=action.get('hands',[])[:len(hands)]; return action\n"
    'def agent(observation,configuration): return act(observation,configuration)\n',encoding='utf8')
   manifest.append({'name':name,'mode':mode,'switch_step':duration})
 (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('built',len(manifest),'primitive candidates')
if __name__=='__main__':main()
