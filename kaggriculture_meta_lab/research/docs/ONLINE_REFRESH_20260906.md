# Online replay refresh — 2026-09-06

## Scope

GitHub Actions run `34050782816` fetched every public episode then exposed by the
Kaggle API for all of the team's submissions. The collector added 200 episodes;
the local corpus now contains 376 matches:

| Submission | Policy generation | Games | W-L | Win rate | Our mean | Opponent mean | Mean margin |
|---|---|---:|---:|---:|---:|---:|---:|
| 56032076 | V2 | 16 | 6-10 | 37.5% | 27,370 | 44,936 | -17,566 |
| 56033159 | V3 | 21 | 10-11 | 47.6% | 33,774 | 46,658 | -12,884 |
| 56033582 | V3.1 | 24 | 11-13 | 45.8% | 40,853 | 56,150 | -15,297 |
| 56037841 | pre-scripted-V7 generation | 33 | 15-18 | 45.5% | 65,346 | 70,880 | -5,534 |
| 56044395 | submitted scripted V7 | 112 | 74-38 | 66.1% | 89,008 | 81,816 | +7,193 |
| 56054137 | V8 Aastik | 87 | 63-24 | 72.4% | 87,133 | 81,888 | +5,245 |
| 56054139 | V8 Renoir-opening hybrid | 83 | 65-18 | 78.3% | 90,234 | 82,969 | +7,265 |

These are observed public matches, not paired experiments. In particular, the
Aastik and hybrid sets have zero shared opponent names, so their raw percentages
must not be interpreted as a controlled head-to-head comparison.

## Recent windows

| Submission | Latest 10 | Latest 20 | Latest 40 | Latest-20 mean margin |
|---|---:|---:|---:|---:|
| scripted V7 | 6/10 | 9/20 | 22/40 | -3,342 |
| V8 Aastik | 6/10 | 14/20 | 28/40 | -165 |
| V8 hybrid | **9/10** | **17/20** | 29/40 | +2,534 |

The statement that both agents exceed 90% is not supported by the complete
public replay sample. The hybrid reached exactly 90% in its latest ten, but the
small window is noisy and Aastik's latest ten are 6/10. The changing matchmaker
also makes chronological windows progressively harder and non-comparable.

## V8 loss taxonomy

Aastik's 24 losses include:

- four losses by more than 10k;
- nine near-losses by less than 1k;
- several high-income losses in which our score exceeded 110k, so the problem
  was the opponent's still higher ceiling rather than an economic collapse;
- a small low-output tail around 44k–55k, consistent with an unfavourable market
  interaction for the fixed trajectory.

The hybrid's 18 losses include:

- four losses by more than 10k;
- five near-losses by less than 1k;
- several 110k+ losses against still higher-scoring opponents;
- a smaller low-output tail, notably approximately 48k and 59k.

This separates three useful engineering targets:

1. **Near ties:** market timing/order and endgame liquidation primitives may
   rescue these without changing the full policy.
2. **Low-output collapses:** early market-regime detection should decide when a
   fixed opening is unsafe.
3. **High-output losses:** these need a genuinely higher-ceiling production
   family — the likely role of a third policy — rather than defensive tuning.

## Consequence for TOP49 work

Keep `agent_v8_aastik.py` and `agent_v8_hybrid.py` immutable as controls. New
TOP49-derived work should use separate `agent_v9_*` experimental candidates and
versioned fingerprint/cluster reports. Promote nothing into either V8 control
until it wins paired-seat, same-seed tests and fresh holdouts.

Five recent matches for each of 49 players are sufficient for initial family
fingerprinting and opening/common-loss contrast. They are not by themselves a
confidence-sized closed-loop benchmark: first deduplicate them by policy family,
then reconstruct representative tapes and run current agents against those
representatives.
