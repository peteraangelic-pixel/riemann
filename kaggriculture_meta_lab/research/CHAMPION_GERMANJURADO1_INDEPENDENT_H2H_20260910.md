# Independent H2H: corrected GermanJurado1 tape

Runner: `scripts/h2h_tape_runner.py`
Environment: `kaggle-environments==1.32.7`
Tape mapping: imported corrected candidate using `steps[1:]` lineage.

## Seeds 100–103, both swaps

| Opponent | Games | W/L/T | Mean candidate | Mean opponent | Total margin |
|---|---:|---:|---:|---:|---:|
| B21/S16 | 8 | 8/0/0 | 99,464.25 | 85,303.75 | +113,284 |
| v10 Subin static | 8 | 8/0/0 | 118,610.50 | 110,860.50 | +62,000 |

Raw final rewards were identical under swap for these deterministic opponents,
which is expected for this symmetric tape setup. No error or timeout was
reported.

## Fresh check: seeds 116–119, both swaps, B21/S16

```text
6 wins / 2 losses / 0 ties
mean candidate: 103,984.625
mean B21:        95,869.000
total margin:    +64,925
errors: 0
timeouts: 0
```

The two losses are seed 118, where both swaps produced 143,990 candidate versus
149,280 B21. This is useful evidence against claiming universal dominance.

## Interpretation

This independently reproduces the corrected tape's strong result against the
local B21 and Subin controls. It does **not** yet establish:

- superiority to a live reactive opponent;
- superiority to the real G2 submission on identical seeds;
- fresh holdout dominance at meaningful scale;
- a reactive submission policy;
- Kaggle leaderboard transfer.

Next validation should add the exact `agent_v10_subin_g2_83.py` from the source
branch, a 32-game B21/G2 matrix on seeds 100–115, then a larger unseen seed
holdout and at least one reactive opponent. The tape remains an open-loop
imitation and must be labelled accordingly.
