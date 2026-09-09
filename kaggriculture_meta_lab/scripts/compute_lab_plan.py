#!/usr/bin/env python3
"""Calculate the LAB experiment budget and a conservative runtime estimate.

This is planning only: it never claims a benchmark. Pass a measured Rust
throughput from the 5950X with --games-per-second after the first calibration.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--population', type=int, default=1000)
    ap.add_argument('--screen-opponents', type=int, default=4,
                    help='V7, Aastik, hybrid and one TOP10 representative')
    ap.add_argument('--screen-seeds', type=int, default=8)
    ap.add_argument('--top-k', type=int, default=10)
    ap.add_argument('--promote-seeds', type=int, default=30)
    ap.add_argument('--top20-seeds', type=int, default=50)
    ap.add_argument('--top30-seeds', type=int, default=75)
    ap.add_argument('--holdout-seeds', type=int, default=250)
    ap.add_argument('--v12-variants', type=int, default=27)
    ap.add_argument('--v12-screen-seeds', type=int, default=20)
    ap.add_argument('--v12-promote-seeds', type=int, default=120)
    ap.add_argument('--v12-final-seeds', type=int, default=175)
    ap.add_argument('--games-per-second', type=float, default=4000,
                    help='measured Rust batch throughput; default is conservative')
    ap.add_argument('--output', type=Path)
    a=ap.parse_args()
    if min(a.population,a.screen_opponents,a.screen_seeds,a.top_k,a.promote_seeds,
           a.top20_seeds,a.top30_seeds,a.holdout_seeds,a.v12_variants,
           a.v12_screen_seeds,a.v12_promote_seeds,a.v12_final_seeds,a.games_per_second)<=0:
        ap.error('all quantities must be positive')
    # Every candidate/opponent comparison is played in both physical seats.
    v12_screen=a.v12_variants*a.v12_screen_seeds*2
    v12_promote=a.top_k*a.v12_promote_seeds*2
    v12_final=(a.top_k+1)*a.v12_final_seeds*2  # finalists + untouched baseline
    evo_screen=a.population*a.screen_opponents*a.screen_seeds*2
    evo_promote=a.top_k*a.promote_seeds*a.screen_opponents*2
    top20=a.top_k*a.top20_seeds*2
    top30=a.top_k*a.top30_seeds*2
    holdout=a.top_k*a.holdout_seeds*2
    stages={'v12_screen':v12_screen,'v12_promote':v12_promote,'v12_final':v12_final,
            'evolution_screen':evo_screen,'evolution_promote':evo_promote,
            'top20_gate':top20,'top30_gate':top30,'holdout':holdout}
    total=sum(stages.values())
    assumptions=vars(a).copy(); assumptions['output']=str(assumptions['output']) if assumptions['output'] else None
    report={'assumptions':assumptions,'stages':stages,'total_games':total,
            'estimated_seconds_at_measured_rate':round(total/a.games_per_second,1),
            'estimated_hours_at_measured_rate':round(total/a.games_per_second/3600,2),
            'notes':['Rust batch throughput must be calibrated on the 5950X; 4000 games/s is a planning default, not a claim.',
                     'Reactive policies remain on Python unless their native overlay passes parity.',
                     'Every promotion gate includes both seats and an untouched baseline.']}
    text=json.dumps(report,indent=2,ensure_ascii=False)+'\n'
    if a.output: a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(text,encoding='utf-8')
    print(text,end=''); return 0
if __name__=='__main__': raise SystemExit(main())
