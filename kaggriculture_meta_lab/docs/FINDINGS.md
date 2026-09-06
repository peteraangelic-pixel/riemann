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

**Final closed-loop result (V8 fert-only vs pure V7, 20 seeds × 2 seats = 40 games):**

```
27 W / 13 L / 0 T, score rate 67.5% (95% Wilson CI 52.0-79.9)
mean margin +634, errors 0, balanced on both seats (13-7 / 14-6)
-> Wilson gate PASS (lower bound 52% > 50%).
```

A small, **regime-independent, zero-crash** gain — exactly the kind of stable
edge the final Bradley–Terry ranking rewards. Bigger fertilizer upside (the
elite ~2× premium-yield cycle) requires the demand-driven crop-mix study
(strawberries/ongoing crops), which is the next project, not a V8 side-effect.

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
