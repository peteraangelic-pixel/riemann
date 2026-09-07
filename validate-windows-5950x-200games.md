# Validation: agent_v8_fert.py vs agent_v7.py — 200 closed-loop games

**Source:** user's Ryzen 9 5950X / 64 GB, Windows, Python 3.13, kaggle-environments 1.32.7,
`run_windows.bat` with `GAMES=100 WORKERS=16` (console dump `wyniki.txt`, uploaded 2026-09-06,
run id `validate-20260906-145507`). 200 games in 67 s (3.0 games/s), 16 workers.

```
workers=16  closed-loop seeds=100 (x2 seats)  corpus=corpus/sample

[1/2] Closed loop: 200 games
  146W 54L 0T   score 73.0%   95% Wilson 66.5-78.7
  mean margin +733 (median +528, p10 -647)   errors 0
  seat0 73-27 margin +717 | seat1 73-27 margin +748
  GATE: PASS

[2/2] Open-loop corpus: corpus/sample
  8W 0L 0T over 8 episodes (errors 0)
  candidate mean cash 84,914 (median 78,835)
  recorded  mean cash 26,948  delta +57,966

elapsed 72s
```

## Interpretation

* The fertilizer edge is **real and large**: 73.0% over 200 paired games, Wilson 95% lower
  bound 66.5% — nowhere near the 50% no-effect line. Win rate rose from 67.5% (40 games) to
  73.0% (200 games); margin stayed small but rock-steady (+733 mean, +528 median).
* **No seat/start bias**: both seats 73-27, margins within ~4% of each other.
* **Zero crashes** in 200 games — Bradley-Terry finals only rank agents that never throw.
* The open-loop corpus is a smoke check only (tape opponents are not adaptive); the closed-loop
  V8-vs-V7 head-to-head is the decisive number.

V8 (fertilizer, crop mix identical to V7) is the promoted agent. Next lever: the adaptive
production-mix selector (market regime from the opening rounds), per docs/FINDINGS.md.
