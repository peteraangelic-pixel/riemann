# V8 structured V7/V16 hybrid — 2026-09-10

## Question

Re-test the earlier V7-opening/older-market-tail construction on the completely replaced latest TOP7, and determine whether its complementary strengths can support a conditional V8.

The candidate keeps V7 hands and market actions at turns 0–1, then uses the V16/V2 market tape from turn 2 onward. It differs from V7 in 226 seat/turn action records. This is the same causal family previously screened by branch 087c0, now evaluated on the latest uploaded corpus and complete TOP15 with substantially larger matched gates.

## Run

Actions run `34518137372`, Rust engine, zero errors:

- latest TOP7: 84 policies × 24 seeds × both seats = 4,032 games/candidate;
- complete TOP15: 105 policies × 24 seeds × both seats = 5,040 games/candidate;
- V7 and V16 controls use identical seeds.

## Latest TOP7

| Candidate | W–L | Own reward | Margin |
|---|---:|---:|---:|
| **hybrid** | **3642–390** | **107,749.91** | **+27,439.20** |
| V16/V2 | 3615–417 | 103,115.76 | +19,740.46 |
| V7 | 3607–425 | 106,868.04 | +26,455.88 |

Hybrid minus V7: **+35 wins**, +881.87 own reward and +983.32 margin. It improves six current teams and loses three net wins over two teams. This is a real, broad newest-meta signal, not merely the earlier five-win V16 fluctuation.

## Complete TOP15

| Candidate | W–L | Own reward | Margin |
|---|---:|---:|---:|
| **V7** | **4710–330** | 105,016.49 | +26,429.10 |
| hybrid | 4688–352 | **105,924.05** | **+27,148.18** |
| V16/V2 | 4388–652 | 97,214.44 | +10,577.90 |

Hybrid minus V7: **−22 wins**, despite +907.57 own reward and +719.08 margin. Most binary damage is concentrated in one old opening family (−32), partly offset by gains elsewhere.

## Opening-strategy signatures mined from replay sources

Grouping matched outcomes by the opponent's recorded turn-0 market action reveals a strong separable pattern:

- a single wheat purchase of 13: hybrid +21 latest-TOP7 wins and +6 complete-TOP15 wins;
- cow purchase of 2: +8 latest and +2 TOP15;
- several high-hire/animal openings: positive or neutral on both corpora;
- wheat purchase 13 followed by wheat purchase 60 and sale 60: **−37 TOP15 wins**;
- wheat purchase 13 followed by sale 6: −6 TOP15 wins;
- the buy-13/sell-13/buy-13 family is approximately neutral overall, although V7 remains important on selected current policies.

Several opposing openings have the same net wheat-inventory effect, so wheat inventory alone cannot distinguish them. Their transaction order changes post-turn-0 money, while high-hire openings also expose a different public hand count. This supplies a concrete feature basis for the next selector: opponent money plus hand count and selected market inventories after turn 0.

## Decision

Do not promote the static hybrid. It is the strongest current V8 component but has a clear complete-TOP15 binary regression.

Proceed with a fail-closed selector that defaults to V7 and enables the old market tail only for public post-opening fingerprints supported on both corpora. Candidate selection and the final gate must use disjoint seeds; exact generated Python source requires an independent execution check.

## Artifacts

- `kaggriculture_meta_lab/agents/candidates/agent_v8_lab_safe_open_old_market.py`
- `kaggriculture_meta_lab/results/v8-structured-hybrid-latest-top7-20260910.json`
- `kaggriculture_meta_lab/results/v8-structured-hybrid-top15-20260910.json`
