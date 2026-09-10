# Peer branch audit — 2026-09-10

Audited without switching branches:

- `arena/01a087c0-riemann` through remote head `5e2dea5`;
- `arena/01a075fa-riemann` through remote head `f7c60a6`.

## Branch 087c0: valuable opening decomposition

This branch independently isolated the same V4/V5 opening failure, then performed a broader combinatorial search. Its strongest useful finding is that opening turns have separable roles:

- turn 0 determines robustness against the omitted large-wheat-book archetype;
- turn 1 determines performance against the evolved/hybrid family;
- two separate early wheat buys followed by a sell are load-bearing; simplified single-buy openings caused hidden catastrophic regressions on broader holdout controls.

Its first V6 used the V5 body with a safe turn 0 while retaining the aggressive turn 1. On one-policy-per-team TOP15 it scored 1725–194 versus V5's 1614–306 and changed almost exclusively the catastrophic matchup. A later screen found `t1b60`, then a 1,920-game, 15-control panel reported:

| Candidate | W–L | Score | Own reward | Margin | Special matchup |
|---|---:|---:|---:|---:|---:|
| market probe | 1770–150 | 0.9219 | 108,363 | +30,589 | 91–37, +7,831 |
| synthetic alternative | 1667–253 | 0.8682 | 102,365 | +22,657 | 90–38, +7,940 |
| branch V6 control | 1690–230 | 0.8802 | 96,799 | +13,119 | 91–37, +7,824 |

These numbers were initially treated as promising rather than promotion-grade because they came from only one selected tape per TOP15 team. The market probe was imported under the neutral local name `agent_v7_market_probe.py` and then passed our complete 105-policy, matched-seed TOP15 audit.

### Independent complete TOP15 confirmation

Run 34494565323 evaluated 8 shared fresh seeds against all 105 selected TOP15 policies in both seats: 1,680 games per candidate, zero errors.

| Candidate | W–L | Score | Own reward | Margin | Best-listed score |
|---|---:|---:|---:|---:|---:|
| **V7 market probe** | **1603–77** | **0.9542** | **102,542** | **+27,435** | **0.9408** |
| V6 safe opening | 1527–153 | 0.9089 | 89,860 | +10,484 | 0.8951 |
| V3 coherent replay | 1510–170 | 0.8988 | 89,373 | +9,551 | 0.8850 |
| V16/V2 | 1471–209 | 0.8756 | 90,022 | +10,028 | 0.8382 |
| G2 control | 674–1006 | 0.4012 | 80,820 | −5,096 | 0.3951 |

V7 versus V16 gains +12,521 own reward and +17,407 margin per matched case; versus V6 it gains +12,683 own reward and +16,951 margin. Against the special omitted archetype it remains robust at 102–10 and +5,851. This is a genuinely large result rather than a narrow binary exploit, and it significantly exceeds G4/G2 and every previous static candidate on all three principal local metrics.

Secondary gates in run 34495271206 also passed:

- complete matched TOP7: V7 1255–89, score 0.9338, own reward 101,827, margin +25,660; V6 control 1188–156, score 0.8839, own reward 88,516, margin +12,911;
- recovered TOP30 original seeds: V7 178–122, score 0.5933, own reward 100,670, margin +12,523;
- TOP30 best-listed subset: 98–46, score 0.6806, own reward 104,203, margin +19,188.

The aggregate TOP30 binary score remains below V16's 0.6167, but V7 has the strongest TOP30 own reward and margin by a large amount and the strongest best-listed binary score. It is now the leading V7 candidate pending live validation.

The branch also confirms opening rock-paper-scissors: a local head-to-head optimum can still be population-fragile. Its wide-holdout rejection of apparently strong synthetic openings is especially important.

## Branch 087c0 follow-up through `ef2c149`: useful day-6 pulse, rejected as V8

The newer branch work added two reusable methodological improvements: evaluation against all 84 policies in the refreshed TOP7 corpus (12 replays per team), and single-action ablation after a day-window crossover. Its V7-opening plus older market-tail crossover improved the initial six-seed screen, but lost three wins on the 2,016-game refreshed-TOP7 holdout. This independently reinforces that a margin-positive day block is not automatically promotion-grade.

The most interesting surviving micro-edit added `SELL FERTILIZER 3` at step 153 and changed nothing else. On branch evidence it improved both narrow panels:

- old 15-representative TOP15: 894–66 versus V7 892–68;
- refreshed 84-policy TOP7, 12 fresh seeds, both seats: 1845–171 versus 1843–173;
- paired refreshed-TOP7 delta: +108.96 margin and +26.56 own reward per game.

It was imported under the neutral LAB name `agent_v8_fertilizer_pulse.py` and subjected to our broader gates in run `34506530879`. The complete 105-policy TOP15 result reversed the binary signal:

| Candidate | W–L | Score | Own reward | Margin |
|---|---:|---:|---:|---:|
| V7 | **2387–133** | **0.94722** | 101,995.83 | **+28,591.19** |
| fertilizer pulse | 2379–141 | 0.94405 | **102,129.57** | +28,533.25 |

The pulse gained +133.74 own reward but lost eight games and 57.95 margin per matched case. Recovered TOP30 was binary-identical at 178–122, while the pulse was also slightly lower in own reward (−22.97) and margin (−16.20). Therefore it is retained as a useful causal feature but **rejected as static V8**. The disagreement between 15/84-policy gates and the complete 105-policy gate is precisely why promotion continues to require broad per-policy coverage.

A worthwhile next experiment is state-gating this one sale rather than adding it unconditionally: evolve thresholds over the public fertilizer market state and own available fertilizer, with V7 as fail-closed identity. The branch's day/action ablation method is useful; its static finalist is not itself the answer.

## Branch 075fa: reactive V6b is not yet competitive

This branch created a fail-closed, price-aware V6b with state fingerprinting and a selector. It is useful infrastructure work, but the first gameplay benchmark is negative:

- 10 games against random;
- baseline V6 mean 91,612;
- V6b mean 89,245;
- delta −2,367;
- zero errors/timeouts.

The test lacks controlled seeds and real TOP7/TOP15 opponents. Therefore V6b is not a promotion candidate. Potentially reusable elements are the fail-closed selector, telemetry/state fingerprints and exception containment—not the current complete policy.

## Naming/privacy convention

Promoted or newly created local candidates use neutral version/behavior names. Kaggle archives always expose only `main.py`; new submission descriptions also omit opponent/player names. Historical provenance files keep their existing paths because mass renaming would break reproducibility, but they are not used as public archive filenames.
