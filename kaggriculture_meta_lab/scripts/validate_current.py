"""Validate the current V9 candidate against every frozen V7/V8 control.

Runs identical seeds and both seats. This is closed-loop validation; the TOP49
open-loop gate remains the main repository's screen_top49_all.py workflow.
"""
from __future__ import annotations
import argparse,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kaggriculture_lab.stats import aggregate,promotion_gate
from kaggriculture_lab.tournament import build_jobs,default_workers,run
DEFAULT_CANDIDATE='agents/current/agent_v9_b21_s16.py'
DEFAULT_CONTROLS=['agents/current/agent_v7_scripted.py','agents/current/agent_v8_aastik.py','agents/current/agent_v8_hybrid.py']
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',default=DEFAULT_CANDIDATE);p.add_argument('--control',action='append',dest='controls');p.add_argument('--games',type=int,default=50,help='seeds per control; both seats doubles this');p.add_argument('--workers',type=int,default=default_workers());p.add_argument('--start-seed',type=int,default=20264000);p.add_argument('--allow-large',action='store_true');a=p.parse_args();controls=a.controls or DEFAULT_CONTROLS
 projected=len(controls)*a.games*2
 if projected>1200 and not a.allow_large:raise SystemExit(f'Refusing {projected} full games; use <=200 seeds or explicitly pass --allow-large')
 output={'candidate':a.candidate,'seeds':a.games,'both_seats':True,'controls':[]};all_pass=True;t0=time.perf_counter()
 for i,control in enumerate(controls):
  jobs=build_jobs(a.candidate,[control],a.games,a.start_seed,swap_seats=True,steps=720,tag=Path(control).stem);rows=run(jobs,a.workers,progress_every=max(20,len(jobs)//4));agg=aggregate(rows);ok,reasons=promotion_gate(agg,min_games=max(20,a.games));all_pass &= ok
  rec={'control':control,**agg.to_dict(),'gate_pass':ok,'gate_reasons':reasons};output['controls'].append(rec);print(f"{Path(control).name}: {agg.wins}W-{agg.losses}L-{agg.ties}T margin {agg.mean_margin:+.0f} gate {'PASS' if ok else 'FAIL'}")
 output['all_controls_pass']=all_pass;output['elapsed_s']=time.perf_counter()-t0;out=ROOT/'results'/f'validate-current-{time.strftime("%Y%m%d-%H%M%S")}.json';out.parent.mkdir(exist_ok=True);out.write_text(json.dumps(output,indent=2)+'\n');print('Wrote',out);return 0 if all_pass else 2
if __name__=='__main__':raise SystemExit(main())
