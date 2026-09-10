# V5/DeeperNet diagnosis and V6 safe-opening result — 2026-09-10

## Executive conclusion

The broad V4/V5 failure is not a mysterious defect in the simulator or the V5 wrapper. It is a two-turn opening interaction inherited by V4 and V5. V4 replaces only policy turns 0–1 of V3 with the German opening; V5 retains those two turns and adds 41 sparse later edits. Against DeeperNet, the German opening creates a catastrophic wheat-market interaction. Restoring V3's first two turns while retaining every later V5 edit produces V6.

V6 is the best candidate in the matched fresh TOP15 test: 1527–153 (0.9089), mean margin +10,484. It also repairs DeeperNet to 106–6 and +6,265. V16/V2 retains a small own-reward advantage (+162 per matched game), while V6 has +456 margin and substantially more binary wins.

## Exact policy differences

All tapes have 719 policy turns and are symmetric between physical seats.

- V3 → V4: only turns 0 and 1 differ.
- V4 → V5: 41 later turns differ: 122, 173, 181, 188, 189, 191–193, 200, 207, 209, 214–215, 240–241, 288, 346, 359–361, 401, 409, 433, 446–447, 449, 499, 513, 515, 519, 525, 577, 589, 593, 655, 661, 665–666, 697, 709, 718.
- V6: V3 turns 0–1 plus V5 turns 2–718. Thus it retains all 41 V5 late edits.

The decisive opening is:

| Turn | V3 market | V4/V5 market |
|---:|---|---|
| 0 | buy wheat 7; buy wheat 20; sell wheat 60 | buy wheat 5 |
| 1 | sell wheat 13; buy wheat 5; hire ×5; buy cows 2; buy sheep 2 | buy wheat 85; sell wheat 90; buy wheat 5; hire ×5; buy cows 2; buy sheep 2 |

DeeperNet's recorded opening (replay actions are offset by the initial environment frame) is stable across the seven audited tapes:

- initial action: PASS, no market orders;
- first policy market turn: buy wheat 13; buy wheat 60; sell wheat 60;
- next turn: sell wheat 8; sell wheat 3; hire ×5; buy wheat 3; buy cows 2;
- then buy one sheep and start a livestock-oriented spatial program.

The V4/V5 85/90 wheat round-trip collides with DeeperNet's large 60-unit wheat book. The resulting clearing-price/wealth transfer launches DeeperNet while suppressing V4/V5. This is an interaction defect: the opening works against many TOP7/TOP10 tapes but is highly exploitable by this omitted market archetype. V5's late edits improve V4's economy but occur too late to undo that opening transfer.

## Why DeeperNet was omitted earlier

DeeperNet is rank 11 in the recovered TOP15 snapshot. Earlier development panels were family controls and TOP7/TOP10 slices, so they did not include it. This was a panel-coverage defect, not evidence that DeeperNet was invalid. TOP10 was specifically misleading: V5 led there, but ranks 11–15 exposed the opening failure. The complete TOP15 corpus contains seven DeeperNet replay policies and is now a mandatory gate.

## Matched fresh TOP15 (8 seeds, all 105 selected tapes, both seats)

10,080 games were run for six candidates, 1,680 per candidate, with zero errors.

| Candidate | W–L | Score rate | Own reward | Margin | Best-listed score |
|---|---:|---:|---:|---:|---:|
| **V6** | **1527–153** | **0.9089** | 89,860 | **+10,484** | **0.8951** |
| V3 | 1510–170 | 0.8988 | 89,373 | +9,551 | 0.8850 |
| V16/V2 | 1471–209 | 0.8756 | **90,022** | +10,028 | 0.8382 |
| V5 | 1455–225 | 0.8661 | 84,579 | +6,897 | 0.8170 |
| V4 | 1449–231 | 0.8625 | 83,630 | +5,996 | 0.8158 |
| G2 control | 674–1006 | 0.4012 | 80,820 | −5,096 | 0.3951 |

Matched deltas:

- V6 − V3: +487 own reward, +933 margin; V6 better in 1217, worse in 458, equal in 5.
- V6 − V16: −162 own reward, +456 margin; V6 better in 490 and worse in 1190 on continuous margin despite its superior binary count. This confirms that V16 remains the absolute-economy control.
- V6 − V5: +5,280 own reward, +3,587 margin.
- V6 − G2: +9,040 own reward, +15,579 margin.

### DeeperNet only (112 games per candidate)

| Candidate | W–L | Own reward | Margin |
|---|---:|---:|---:|
| **V6** | **106–6** | **89,278** | **+6,265** |
| V3 | 104–8 | 87,323 | +2,777 |
| V16/V2 | 90–22 | 86,637 | +1,624 |
| G2 | 26–86 | 90,778 | −3,221 |
| V5 | 16–96 | 71,448 | −42,334 |
| V4 | 16–96 | 59,616 | −53,590 |

This isolates causality unusually cleanly: changing only turns 0–1 transforms V5 from 16–96/−42,334 into 106–6/+6,265.

## Complete TOP7 and recovered TOP30

The complete matched fresh TOP7 test contains 84 selected policies, 8 seeds and both seats (5,376 games total for V16/V3/V4/V5). It confirms why the earlier narrow panel promoted V5:

| Candidate | TOP7 score | Own reward | Margin | Best-listed score |
|---|---:|---:|---:|---:|
| V5 | **0.8966** | 88,950 | **+14,569** | **0.9136** |
| V16/V2 | 0.8884 | **88,986** | +13,145 | 0.8732 |
| V4 | 0.8854 | 88,807 | +14,330 | 0.9081 |
| V3 | 0.8676 | 88,253 | +12,536 | 0.8713 |

TOP30 was recovered exactly from `b167c7b^:TOP30.7z`. Original-seed open-loop results (300 games each) are:

| Candidate | W–L | Score | Own reward | Margin | Best-listed score |
|---|---:|---:|---:|---:|---:|
| V16/V2 | 185–115 | **0.6167** | **98,986** | **+5,052** | 0.5972 |
| V5 | 184–116 | 0.6133 | 96,013 | +3,751 | **0.6389** |
| V4 | 178–122 | 0.5933 | 95,603 | +3,546 | 0.6111 |
| V3 | 170–130 | 0.5667 | 98,105 | +4,057 | 0.5694 |
| V6 | 174–126 | 0.5800 | 98,741 | +4,457 | 0.5972 |

TOP30 is older and uses one recorded seed per policy, so it has much higher seed-policy coupling than the matched fresh tests. V6 sacrifices V5's binary fit to those old tapes but recovers most of V16's absolute economy and improves V5's own reward and margin. It must not override the newer matched TOP15 result.

## Open-loop limitation

Every corpus opponent is a recorded action tape, not the original adaptive agent. Both-seat testing, original-seed testing, matched fresh seeds, own reward, margin and per-team rows are retained, but none reconstruct closed-loop leaderboard behavior. Live Kaggle remains the final validation.

## Kaggle deactivation finding

The current public `kaggle`/`kagglesdk` package was inspected. `CompetitionApiClient` exposes submission creation, listing, retrieval and download, but no deactivate/delete/set-active submission operation; `KaggleApi` likewise has no such method. Therefore ref 56143699 cannot be safely deactivated through the supported public API/CLI used by Actions. No private endpoint was fabricated or called. Slot reuse requires the Kaggle web UI (if it offers deactivation for this simulation competition) or Kaggle support; V3 was not submitted without confirmation that a slot had been freed.

## Artifacts

- V6 agent: `kaggriculture_meta_lab/agents/candidates/v6_v3_opening_v5_late.py`
- TOP15: `kaggriculture_meta_lab/results/v6-diagnosis-top15-fresh-20260910.json`
- TOP30: `kaggriculture_meta_lab/results/{v16,v3,v4,v5,v6}-top30-original-seeds-20260910.json`
- TOP7: `kaggriculture_meta_lab/results/v16-v3-v4-v5-top7-fresh-20260910.json`
- Actions: runs 34488726880 and 34489955315
