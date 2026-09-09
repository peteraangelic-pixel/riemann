# V10 market overlay — Generation 2

Actions run `34381066563` evaluated a complete 362-profile refinement grid over
10,860 source-excluded TOP10 games. The grid varied start day, cash reserve,
minimum wheat price and milk reserve around the two Generation-1 leaders.

The leading equivalence class scored 16-14 (53.3%), team-balanced 59.26%, mean
margin +1,158. Its simplest representative is:

```json
{"enabled":true,"start_day":6,"cash_reserve":200,
 "min_wheat_price":0,"milk_reserve":1}
```

Start day 6 versus 8 and minimum wheat prices 0/10/20 produced identical scores;
the measured gain comes from the $200 cash floor and one-unit milk reserve.
Generation 1's leader had margin +1,093 on the same games.

A standalone `agent_v10_subin_g2_63.py` completed a 32-game closed-loop B21
holdout at 23-9 (71.9%), margin +8,148. This matches the static control's 23-9
but remains slightly below its +8,410 margin; it is not submission-approved.
Progressive TOP20/TOP30 raw-tape validation remains required.
