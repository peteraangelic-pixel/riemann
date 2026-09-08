# Current TOP10 exemplar micro-screen

## Design

Actions run `34283353327` screened four immutable controls plus 16 distinct
policy tapes observed in best-listed TOP10 submission records. Every candidate
played the 16 available best-listed target records in both seats (640 games).
For an exemplar's headline score, both games from its own source episode were
excluded to reduce direct replay leakage, leaving 30 games (or 28 where the
same episode appears for two teams). All games used original seeds and the
parity-gated Rust raw-tape path; no result is closed-loop evidence.

This bounded rerun replaced an overbroad 6,000-game attempt that hit its
15-minute guard. The failed attempt produced no score and is not evidence.

## Result

The three strongest independent records all came from the same `Subin An`
submission/policy family:

| candidate tape | non-source W-L | score | mean margin |
|---|---:|---:|---:|
| episode 106845775 | 14-16 | 46.7% | -282 |
| episode 106846791 | 14-16 | 46.7% | -346 |
| episode 106844933 | 14-16 | 46.7% | -481 |
| next Subin episode 106847573 | 10-20 | 33.3% | -3,623 |
| V8 Aastik control | 8-24 | 25.0% | -6,442 |
| B21/S16 control | 8-24 | 25.0% | -7,116 |
| V7 scripted control | 8-24 | 25.0% | -8,518 |
| V8 hybrid control | 6-26 | 18.8% | -13,250 |

The top tape closes roughly 22 percentage points and nearly all mean-margin gap
versus B21 on this tiny TOP10 screen, but it still does not exceed 50% and its
sample is far too small for promotion. The consistency of three different
Subin episodes is more useful than one lucky replay: they share the same opening
and near-identical market cadence, while state-dependent sales differ.

The observed family opens with a WHEAT buy/sell/buy sequence, hires five hands
on the next turn, and immediately purchases cows and sheep. Across representative
records it performs about 413–415 sales, 260 hires, 189 seed buys, 65 product
buys, 12 animal buys, and two land buys. This is materially more active than the
B21 market schedule.

`agents/variants/agent_v10_subin_106845775.py` preserves the best exemplar as an
immutable static research lead. It is explicitly not the original reactive
policy and not submission-approved.

## Decision

Do not generationally mutate all 720 actions blindly. First use the Subin family
as a behavioral target for a compact reactive policy profile: opening, labor
curve, mixed herd, seed/feed reserves, sale cadence, and endgame liquidation.
Then implement the same profile in native Rust and prove action/outcome parity
before population-scale evolution. Continue TOP10 -> TOP20 -> TOP30 only after
that kernel exists; static exemplar evaluation remains a diagnostic baseline.
