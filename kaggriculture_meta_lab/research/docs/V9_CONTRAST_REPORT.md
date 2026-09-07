# V9 episode-level contrast report

Analyzed **245** TOP49 player-tapes, with both seats retained in each outcome row.

## Outcome funnel

- `both_win`: **64** episodes
- `aastik_only`: **10** episodes
- `hybrid_only`: **10** episodes
- `both_lose`: **161** episodes
- `v7_only`: **35** episodes
- `v9_only`: **24** episodes
- `v7_v9_both_lose`: **123** episodes

## V7-only versus B11/S07-only

| feature | left mean | right mean | standardized delta |
|---|---:|---:|---:|
| t5:SELL:WHEAT | 8.37 | 29.08 | -1.18 |
| t5:BUY_PRODUCT:WHEAT | 12.97 | 33.92 | -1.16 |
| t20:SELL:WHEAT | 13.97 | 79.67 | -1.05 |
| t20:BUY_PRODUCT:WHEAT | 20.09 | 85.00 | -1.04 |
| t2:BUY_PRODUCT:WHEAT | 10.97 | 23.96 | -0.79 |
| t1:BUY_PRODUCT:WHEAT | 10.23 | 23.58 | -0.79 |
| t2:SELL:WHEAT | 7.46 | 19.42 | -0.76 |
| t1:SELL:WHEAT | 0.00 | 10.92 | -0.70 |
| t720:HIRE | 287.43 | 282.71 | +0.53 |
| t1:BUY_ANIMAL:COW | 0.83 | 0.25 | +0.49 |
| t2:BUY_ANIMAL:SHEEP | 1.77 | 1.46 | +0.46 |
| t1:HIRE | 1.03 | 0.33 | +0.38 |
| t20:BUY_ANIMAL:COW | 2.31 | 2.08 | +0.38 |
| t2:BUY_ANIMAL:COW | 2.31 | 2.08 | +0.38 |
| t5:BUY_ANIMAL:COW | 2.31 | 2.08 | +0.38 |

## Aastik/hybrid common losses versus common wins

| feature | left mean | right mean | standardized delta |
|---|---:|---:|---:|
| t2:BUY_ANIMAL:SHEEP | 1.76 | 2.03 | -0.52 |
| t720:BUY_ANIMAL:GOOSE | 2.00 | 1.19 | +0.50 |
| t2:BUY_PRODUCT:WHEAT | 14.53 | 19.34 | -0.36 |
| t5:BUY_PRODUCT:WHEAT | 19.01 | 24.25 | -0.33 |
| t2:SELL:WHEAT | 10.80 | 14.91 | -0.32 |
| t720:BUY_ANIMAL:COW | 8.40 | 8.89 | -0.31 |
| t20:BUY_ANIMAL:SHEEP | 1.98 | 2.05 | -0.31 |
| t5:BUY_ANIMAL:SHEEP | 1.98 | 2.05 | -0.31 |
| t5:SELL:WHEAT | 14.43 | 19.20 | -0.31 |
| t1:BUY_PRODUCT:WHEAT | 14.40 | 18.61 | -0.31 |
| t720:BUY_ANIMAL:SHEEP | 6.52 | 7.25 | -0.30 |
| t1:BUY_ANIMAL:SHEEP | 0.14 | 0.31 | -0.30 |
| t20:HIRE | 5.06 | 4.94 | +0.28 |
| t2:HIRE | 5.06 | 4.94 | +0.28 |
| t5:HIRE | 5.06 | 4.94 | +0.28 |

These are diagnostic associations from opponent-emitted replay actions, not causal promotion evidence. Any mutation still requires observation-level checks, identical-seed controls, and fresh holdouts.
