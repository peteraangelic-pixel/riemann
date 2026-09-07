# Agents inventory — read this before running anything

Three tiers, deliberately separated so a stale baseline can never sneak back
into a gate.

## `current/` — the LIVE, strongest controls (from branch `arena/01a0712c`, 2026-09-07)

These are **scripted tape agents**: frozen, pre-computed optimal action
sequences (an optimized opening + an elite player's recorded full game),
compressed with zlib+base85. They score ~140-147k. **These are the baselines a
candidate must beat** (per `docs/CURRENT_20260907.md` promotion rules).

| file | what | TOP49 open-loop (490 games) |
|---|---|---:|
| `agent_v9_b21_s16.py` | **CHAMPION.** V7 opening, buy21/sell16 wheat, two-seat t0/t1 | 184W, 89,115 cash, **+835 margin** |
| `agent_v7_scripted.py` | frozen V7 scripted tape | 188W, 88,409 cash, -901 margin |
| `agent_v8_aastik.py` | tape of elite player "Aastik" (rating-first) | 140W, 86,591 cash |
| `agent_v8_hybrid.py` | tape "203,785 hybrid" | 140W, 85,484 cash |

Tape detail: `B21/S16` = opening buys 21 wheat / sells 16 (see
`research/` build scripts). The 83 opening variants live in the other branch's
`kaggriculture/v9_candidates/` (not copied; big tapes).

## `variants/` — ARENA's own reactive experiments (pre-update, KEPT for comparison)

These are **reactive policies** (full ~900-line Python that decide each turn
from the observation). They score ~70k — roughly half the tapes' cash — so they
are NOT competitive with `current/` yet, but they contain tested mechanisms the
tapes lack (in-field fertilizer, demand adaptation). Kept so we can port their
ideas into a stronger reactive policy and A/B them.

| file | what | closed-loop result |
|---|---|---|
| `agent_v8_fert.py` | V7 + in-field fertilizer by animal hands (RESERVE=0, detour r2) | **73.3% over 1000 games vs reactive V7** (Wilson 70.5-75.9), but that V7 is the weak reactive one |
| `agent_v9_adapt.py` | V8 + demand-adaptive sheep flock (`ADAPT_ANIMALS=False` shipped → identical to V8) | neutral/negative vs V8; documented in FINDINGS 1c. Flip `ADAPT_ANIMALS=True` to enable |

## `ref/` — old reference baselines (reactive V7 line, pre-tape era)

`agent_v7.py` (845-line reactive), `agent_v4.py`, `renoir_tape.py`,
`v8_fusion.py`. These are the lineage the `variants/` were built on. Use for
regression only; **do not use as a promotion gate** — `current/` is stronger.

## Strength ladder (closed-loop cash, seed 20262000, measured)

```
v9_b21 / v7_scripted / v8_aastik   ~142-147k   (tapes)
v8_fert / v9_adapt (reactive)       ~70-72k    (our line — 2x behind)
```

The gap is the optimized **opening + scripted schedule**. Reactive policies are
what the final Bradley-Terry rewards for adapting to a live opponent, but ours
need to absorb the tape opening before they can compete.
