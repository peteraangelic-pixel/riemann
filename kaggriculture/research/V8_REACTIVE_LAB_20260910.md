# V8 reactive opening LAB — 2026-09-10

## Decision

**Do not promote the reactive finalist as V8.** The public-state selector is real and selective, but the complete holdout did not improve wins over the V7 identity control. It traded a small own-reward gain for a worse mean margin, so it does not meet the material-improvement gate.

## Mechanism

V6 and V7 differ only at turn 1 in both seats:

- V6: `SELL WHEAT 13`;
- V7: `BUY WHEAT 60 -> SELL WHEAT 90`;
- every later action is identical.

The Rust `MarketOverlay` therefore gained one deliberately narrow primitive. After turn 0, it reads only public opponent money and public wheat-market inventory. If all enabled bounds match, it substitutes the V6 prefix while preserving V7's remaining turn-1 orders and all later actions. Otherwise it stays exactly V7. The generated Python finalist implements the same selector and fails closed to V7 when the fingerprint cannot be read.

The evolved gene is `[money_mode, money_threshold, inventory_mode, inventory_threshold]`, with mode `0=ignore`, `1=below-or-equal`, and `2=above-or-equal`.

## Search and complete holdout

Dedicated successful persistence run: Actions `34500616904`, bot commit `068f95b`.

- population: 160;
- generations: 3;
- Rust games: 250,320;
- every policy from TOP15, both physical seats;
- complete finalist holdout: 1,680 games per gene, seeds 124000–124007.

Winner: **`[2, 2800, 0, 10020]`**, semantically opponent money `>= 2800` with inventory ignored.

| candidate | W-L | score | own reward | margin | worst team score |
|---|---:|---:|---:|---:|---:|
| reactive winner | 1630-50 | 0.970238 | 111,018.054 | +29,014.410 | 0.892857 |
| V7 identity `[0,0,0,0]` | 1630-50 | 0.970238 | 110,748.436 | **+29,180.514** | 0.892857 |

Matched conclusion: the selector changed economic outcomes, adding **+269.618 own reward/game**, but produced **no additional win** and reduced margin by **166.104/game**. Thus this is not a stronger V8.

All three top equivalent genes used the same effective money condition. Several inventory genes were inactive or redundant under realized turn-1 states.

## Selectivity check

Across the 210 turn-1 public observations in the complete extracted TOP15 replay set, opponent money `>= 2800` held in **32 observations (15.24%)** and failed in **178 (84.76%)**. This confirms the winner is not an always-on V6 alias. This replay-observation count is a mechanism audit, not a substitute for activation telemetry from the fresh seeded simulations.

## Independent Python-engine gate

The first gate in run `34500616904` correctly refused to score 840 failed games. Exact persisted diagnostic:

- `v8-reactive-independent-gate-exit.txt`: `1`;
- V6 and V7 completed 1,680 Rust games;
- all 840 reactive Python-fallback games failed because that workflow had not installed `kaggle-environments`.

The gate was repaired to install the actual framework, expose representative errors, upload evidence even on failure, and reduce the smoke run to one fresh seed because 840 real Python-engine games exceed 30 minutes. Run `34501516117` demonstrated that the full four-seed Python fallback exceeds the 30-minute job budget. Follow-up run `34504691448` was launched with 210 reactive games, but its final outcome could not be retrieved after the GitHub connection began returning HTTP 401. It must not be treated as passed evidence.

The generated source was separately imported against genuine replay observations and returned valid actions for steps 0, 1, and 2, including activation of the evolved turn-1 branch. That is a source smoke test only, not independent game validation.

## CI note

Generic Rust run `34499100864` passed build, clippy, debug/release tests, selector tests, Python adapters, differential checks, and integrated parity, then failed the final tracked-format enforcement. The likely remaining change is rustfmt output in `overlay.rs`; CI should not be declared clean until its exact patch is applied and the workflow passes.

## Artifacts

- `kaggriculture_meta_lab/results/v8-reactive-evolution-20260910.json`
- `kaggriculture_meta_lab/results/v8-reactive-independent-gate.txt`
- `kaggriculture_meta_lab/results/v8-reactive-independent-gate-exit.txt`
- `kaggriculture_meta_lab/agents/candidates/agent_v8_reactive_opening.py`
- `kaggriculture_meta_lab/scripts/search_v8_reactive_switch.py`
- `kaggriculture_meta_lab/rust_port/src/overlay.rs`

The static V8 identity and this reactive finalist remain LAB artifacts. V7 remains the current local candidate; neither result justifies a Kaggle promotion over the stronger live control.
