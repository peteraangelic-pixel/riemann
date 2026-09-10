# V8 V6×V7 evolutionary LAB — 2026-09-10

## Result

The first V8 evolutionary pass completed 268,800 Rust games against all 105 selected TOP15 policies. It did **not** produce a static opening better than V7. This is informative rather than a failed calculation: exact structural comparison proved that V6 and V7 differ on only one of 719 policy turns, turn 1. V7 already contains every later V6/V5 improvement.

The search varied order and quantities for one- and two-part wheat buys and sells over three evolutionary generations (160 individuals), then evaluated 40 finalists on an independent eight-seed holdout. Multiple nominal genes collapsed to the same realized action because market feasibility caps excess quantities. The winner was exactly V7's `(BUY 60, SELL 90)` turn-1 prefix.

## Evolution holdout

- winner gene: `[BUY(s)-then-SELL, 60, 0, 90]`;
- 1,680 games per finalist;
- score 0.9464;
- own reward 105,806;
- margin +28,687;
- worst team score 0.8214.

## Independent matched gate (new seeds 122000–122007)

| Candidate | W–L | Score | Own reward | Margin | Best-listed score |
|---|---:|---:|---:|---:|---:|
| **V7** | **1629–51** | **0.9696** | **101,005** | **+28,023** | **0.9676** |
| emitted V8 | 1629–51 | 0.9696 | 101,005 | +28,023 | 0.9676 |
| V6 | 1536–144 | 0.9143 | 89,690 | +9,642 | 0.9040 |
| V16/V2 | 1486–194 | 0.8845 | 90,250 | +9,821 | 0.8471 |

V7 and the emitted V8 are identical in all 1,680 matched cases. Therefore the emitted file is a reproducibility artifact, not a promoted new version.

The only remaining useful V6 edge is conditional: on these seeds V6 had better DeeperNet economy (own 89,637, margin +6,367) than V7 (own 86,882, margin +4,875), although both won 112/112. A static blend cannot retain that edge without losing V7's much larger broad-population gain, because the parents' sole difference is the same turn-1 market action.

## Next V8 direction

A genuine V8 must be reactive at turn 1:

1. execute the shared safe turn-0 opening;
2. inspect public post-clearing state at turn 1 (opponent money, wheat inventory/price and own money);
3. choose conservative V6 turn 1 only for fingerprints associated with the large-wheat-book regime;
4. otherwise execute V7 turn 1;
5. fail closed to V7 when the fingerprint is unavailable or outside calibrated support.

This requires observation-aware evaluation. The current Rust static-tape backend cannot evaluate the selector, so thresholds must first be learned from instrumented simulations and then validated in the audited Python engine or a new Rust conditional-policy primitive. We must not claim that arbitrary static splicing combines independent V6/V7 features when exact diff shows only one differing turn.

## Artifacts

- search: `kaggriculture_meta_lab/scripts/search_v8_opening_evolution.py`
- complete population evidence: `kaggriculture_meta_lab/results/v8-opening-evolution-20260910.json`
- independent gate: `kaggriculture_meta_lab/results/v8-independent-top15-fresh-20260910.json`
- emitted identity control: `kaggriculture_meta_lab/agents/candidates/agent_v8_evolved_opening.py`
- Actions run: 34497141465
