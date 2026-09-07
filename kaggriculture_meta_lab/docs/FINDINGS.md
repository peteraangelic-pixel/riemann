# Findings produced by this lab (verified by running games)

## 1. The fertilizer path in V7 is a latent bug — this is the biggest lever

**Mechanics verified in the engine** (`kaggriculture.py`):
- `WATER` during a crop's bonus window adds **+2 yield if fertilized, else +1**
  (`bonus = 2 if tile["fertilized_until_day"] >= day else 1`).
- `FERTILIZE` sets `fertilized_until_day = day + 2` and **consumes 1 FERTILIZER
  from the acting UNIT's inventory** — so a unit must first `PICKUP FERTILIZER`
  from the shed (FERTILIZE on shed stock does nothing).
- No shop demands FERTILIZER (`TOWN_CENTER_PRODUCTS` excludes it) and cows
  produce it free via `COLLECT_FERTILIZER`, so its price floors near $1. Public
  elite tuning logs report winners buying ~620 fertilizer.

**What the closed-loop lab measured** (full 720-turn games, `fert_buyer`):

| Configuration | Result vs base V7 |
|---|---|
| V7 as shipped (`FERTILIZER_RESERVE = 0`) | baseline (~51k self-play) |
| `FERTILIZER_RESERVE = 5 / 10 / 40` (use path enabled) | **304–500 cash — total collapse** |
| buy fertilizer + enable use (`reserve=40`) | **0–16, −84k margin** |
| buy fertilizer, use path left OFF (safe) | ~30–48k (slightly worse: wasted cash) |

**Root cause** (`agents/ref/agent_v7.py`, farmer `_farm_op`, ~line 750): when the
shed holds fertilizer and any premium cell is fertilizable, the farmer returns
early to walk to the shed `(4,4)` and `PICKUP FERTILIZER` — and that detour
hijacks his whole daily schedule, so watering/harvest/planting starve. V7 ships
`FERTILIZER_RESERVE = 0`, which keeps that broken path dormant — but it also means
V7 **SELLS the fertilizer its cows produce instead of using it**.

**Implication for V8 (high value):** fix fertilizer *routing* — collect and apply
fertilizer opportunistically the way the animal hands already handle feed
(incidental shed visits), not via a farmer pre-empting his chore loop. Then the
free cow fertilizer (plus cheap bought fertilizer) doubles watering bonuses on
melon/strawberry. This is exactly the elite "virtuous cycle" (cheap fertilizer →
higher yields → more cash → more hands/land).

## 1b. V8 fertilizer fix — DONE and passed the Wilson gate

`agents/variants/agent_v8_fert.py` is V7 with the fertilizer subsystem fixed
(routed, not just bought). What the closed-loop lab measured:

1. **Never store fertilizer in the shed.** Retaining it with `FERTILIZER_RESERVE>0`
   still collapses the farm (to ~300-800) even with the farmer detour removed:
   cheap fertilizer fills the 100-cap shed and, because sales sort high-value
   first, it drops last and **blocks the end-of-day deposit of premium product**.
   `FERTILIZER_RESERVE = 0` is kept; fertilizer is applied DIRECTLY in the field.
2. **Apply it where it is collected.** The animal hand that does
   `COLLECT_FERTILIZER` (carries 1 fert) now applies it to a nearby fertilizable
   premium cell with a **bounded 2-tile detour**, and only when its animal chores
   are caught up. Detour radius sweep: r2 beat V7 4/5, r4/r99 regressed (detour
   disrupted feeding more than the extra fert was worth).
3. **Do NOT bundle crop-mix changes.** Adding 12 strawberries loses to pure V7
   (-2.8k) even though fertilizer helps *within* the strawberry mix; strawberry
   expansion is market-negative on its own and is a separate demand-driven
   decision. V8 keeps the crop mix identical to V7 (`STRAWBERRY_TARGET=0`).

**Closed-loop result (V8 fert-only vs pure V7):**

```
40 games  (20 seeds × 2 seats):  27 W / 13 L / 0 T, 67.5% (CI 52.0-79.9), margin +634
200 games (100 seeds × 2 seats, user's 5950X, 2026-09-06):
  146 W / 54 L / 0 T, score 73.0% (95% Wilson CI 66.5-78.7)
  mean margin +733 (median +528), errors 0, seats balanced (73-27 / 73-27)
  -> Wilson gate PASS decisively (lower bound 66.5% >> 50%).
  Full report: results/validate-windows-5950x-200games.md
```

A small-margin but **large-rate, regime-independent, zero-crash** gain — exactly
the kind of stable edge the final Bradley–Terry ranking rewards. Bigger
fertilizer upside (the elite ~2× premium-yield cycle) requires the
demand-driven crop-mix study (strawberries/ongoing crops), which is the next
project, not a V8 side-effect.

## 1c. V9 demand-adaptive animal mix — built, tested, NOT promoted (negative)

V9 (`agents/variants/agent_v9_adapt.py`, shipped with `ADAPT_ANIMALS=False` so
it is byte-identical in behaviour to V8) sizes the sheep flock from the town's
visible shop demand (`town.unlocked_shops`): wool is demanded only by
YARN_STORE (2 units/interval), milk by PIZZA/ICE_CREAM/SMOOTHIE. The mechanism
is verified correct (flag-off control is exactly 50.0% / margin 0 vs V8).

Closed-loop findings (screen over the `sweeps/v9_adapt.json` family):

```
static 8 sheep vs V7:   0% (12 games)   <- adding animals outright is bad
static 7 sheep vs V7:   8.3%
aggressive adapt (y1/y2 -> 8-9 sheep, d8): 50-58%
conservative adapt (d12, need 3 yarn shops): 62.5% (40 games, margin +460)
v8_control (V8 as-is):  66.7% screen / 67.5-73.3% full gates
```

**Why it loses / is neutral:** the routing/hand system is calibrated to a fixed
14-animal estate (8 cows + 6 sheep). Buying extra sheep pulls animal-hand time
from field service, and a wool-heavy town is not common enough for the extra
3 sheep to pay back before the season ends. The hand/hours budget is the real
constraint, not information — so the first adaptive lever should target the
*field* (ongoing crops: strawberries/tomatoes are planted AFTER the early
animal build-out and don't steal animal-service time), not more animals.

The demand signal itself is real and cheap (`town.unlocked_shops`,
`market.prices`, `market.inventory` are all in the observation and shared
between farms). V9 is kept as the template + testbed; the `v9_adapt.json`
funnel is the way to revisit it (e.g. sheep REDUCTION when yarn demand is
absent, or swapping crops instead of animals). The next adaptive project is
ongoing-crop adaptation, gated the same way.

## 2. Closed loop vs open loop

- V7's `replay_benchmark.py` (open loop) faithfully reproduces Kaggle scores for
  the *physical* schedule and shared market — keep using it for regression.
- But only closed-loop games reveal when a change changes the *market regime*
  (e.g. buying fertilizer that then sits unsold). The fertilizer collapse above
  is invisible in open loop and obvious in closed loop.

## 3. Practical settings (5950X / 64 GB)

- Use worker **processes**; start at **16**. In this 2-core sandbox full games run
  ~0.5 games/s; on a 5950X expect an order of magnitude+ more.
- Python engine is enough for parameter/policy search (thousands of games/night).
  The ~24k episodes/s figure refers to a C++ port (`destbreso/kaggriculture-cppsim`),
  worth it only for RL self-play.
- Engine: `kaggriculture` IS present in `kaggle-environments` on PyPI from 1.32.4;
  pin the version the competition server runs and re-run holdouts after updates.
