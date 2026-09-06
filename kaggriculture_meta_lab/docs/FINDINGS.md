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
