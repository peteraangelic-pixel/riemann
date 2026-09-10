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

These numbers are unusually large and come from only one selected tape per TOP15 team, so they are promising rather than promotion-grade. The market probe was imported under the neutral local name `agent_v7_market_probe.py` and queued for our complete 105-policy, matched-seed TOP15 audit.

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
