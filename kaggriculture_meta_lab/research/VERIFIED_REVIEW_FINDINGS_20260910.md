# Verified findings from external review

## Confirmed in current checkout

### G4/reactive constants

`agent_v10_reactive_subin.py` currently contains:

```text
TICKS_PER_DAY = 6.0
ADAPT_OPPONENT_MODE = 0
```

`ANIMAL_CELLS` overlaps the market overlay `ACCESS` set at:

```text
(4, 4)
(5, 4)
(4, 5)
```

This is a confirmed coordinate overlap, not yet a confirmed gameplay bug. It
must be checked against the engine's build/access legality before changing it.

### B21/S16 semantics

The decoded B21 actions have 720 rows per seat. The module patches:

```text
step 0: BUY_PRODUCT WHEAT 21
step 1: SELL WHEAT 16
```

Step 1 also contains its recorded seed/animal/hire actions. Therefore the name
B21/S16 must not be interpreted as a fresh 720-step threshold policy. It is a
replay tape with a two-step bootstrap patch.

## Unverified but high-priority

1. `TICKS_PER_DAY=6.0` must be checked against actual shop consumption in the
   engine; `turns_per_day=24` alone does not prove it is wrong.
2. `ANIMAL_CELLS`/`ACCESS` overlap may be legal or may block pickup/building.
3. G3/G4 profile JSONs need the exact generator and runner; their extended
   fields are not ordinary `MarketOverlay` fields.
4. GermanJurado1 results need replay/compiler reproduction before promotion.
5. All historical tape scores should be rechecked with the `steps[1:]`
   convention and exact final-money golden fixtures.

## Next implementation priorities

1. Add engine-level tests for shop consumption cadence.
2. Add engine-level tests for animal structure cells and shed access.
3. Add golden replay reward tests for the tape compiler.
4. Recover/reproduce the exact G3/G4 structural runner.
5. Reuse `FarmerPlanner`'s real observation/action schema for reactive modes;
   do not connect the current abstract R1 adapter directly to Kaggriculture.
6. Add self-play versus the previous generation before promotion.
