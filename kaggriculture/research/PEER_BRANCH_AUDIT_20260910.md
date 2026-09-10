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

V7 versus V16 gains +12,521 own reward and +17,407 margin per matched case; versus V6 it gains +12,683 own reward and +16,951 margin. Against the special omitted archetype it remains robust at 102–10 and +5,851. This is a genuinely large result rather than a narrow binary exploit, and it significantly exceeds G4/G2 and every previous static candidate on all three principal local metrics. It is now the leading V7 candidate, subject to TOP30/TOP7 and eventually live validation.

The branch also confirms opening rock-paper-scissors: a local head-to-head optimum can still be population-fragile. Its wide-holdout rejection of apparently strong synthetic openings is especially important.

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
