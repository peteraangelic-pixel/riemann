# V12 Analysis — Breaking the 2800 Ceiling

## Problem Statement
- V2 (Kanno t7 static tape): live ceiling **~2800 pts**, rank ~#550
- TOP10 target: **~3100 pts** (Majkel1337 #1 at 3104.6)
- Gap: **~300 points**

## Root Cause: Static Tape vs Reactive Agent

### V2 (static tape):
- P0 and P1 actions **100% identical** (719/719 steps)
- Same 719 actions regardless of opponent, prices, or game state
- Can't adapt to different seats (P0 starts with ~2464g, P1 with ~191g)

### TOP players (reactive agents):
- P0 and P1 actions **0% identical** (fully reactive per-seat)
- Adapt to market prices, opponent behavior, game phase
- **Seat-aware**: different strategy for high-money (P0) vs low-money (P1)

## Key Differences: V2 vs Majkel1337

| Feature | V2 (agent.py) | Majkel1337 (#1, 3104) |
|---|---|---|
| Crops | WHEAT, CARROT, MELON | WHEAT, MELON, STRAWBERRY, CARROT, TOMATO |
| Animals | NONE | COW×4, SHEEP×5 |
| FERTILIZER selling | No (no animals) | Daily from d11+ (main revenue!) |
| Opening | Same for both seats | Seat-aware (COW+SHEEP for P0, HIRE for P1) |
| Land | NE+d18, SW+d18 | NE+d0, SW+d10 |
| Endgame | Plants until d29 | Liquidates d29 (sells everything) |

## Revenue Analysis

V2 total sells (per seat): WHEAT 17334, FERTILIZER 10357, CARROT 17048, MILK 8257, EGG 8079, STRAWBERRY 6264, WOOL 6188, MELON 6072, TOMATO 6000

Majkel1337: FERTILIZER 122-269 units/day × ~90g = **~11k-24k extra gold/day**

## Why V12 Reactive Fails (so far)

1. **Animals need management**: BUY → BUILD_PASTURE → PLACE → FEED → CARE (daily cycle)
2. **Existing agent.py doesn't handle animals**: only PLANT/HARVEST/WATER/DIG
3. **Adding animals without management = wasted money** (V12b: -437 vs V2)

## Next Steps (requires significant engineering)

1. **Animal management logic**: BUILD_PASTURE, PLACE, FEED, CARE actions in farmer/hands
2. **Seat-aware opening**: detect P0 vs P1 by starting money, different strategy
3. **Strawberry/Tomato crops**: ongoing crops that regrow after harvest
4. **Fertilizer placement**: PLACE FERTILIZER on crops for bonus yield
5. **Endgame liquidation**: d29 sell everything, stop planting

## Files
- `agents/champion_tape_v11.py` — V8 late401 + V10 routing + safe reversions (static tape, best local)
- `agents/v12_reactive.py` — reactive attempt (broken farming core)
- `agent_v12.py` — enhanced agent.py with strawberry/tomato/animals (broken)
- `agent_v12b.py` — minimal V2+animals (works but animals not managed)

## Recommendation
The 2800→3100 gap requires **reactive agent with animal management**. This is a fundamental rewrite of the farming logic (~200-300 lines of new code for BUILD_PASTURE/PLACE/FEED/CARE cycles). The static tape approach (V8/V10/V11) is capped at ~2800.
