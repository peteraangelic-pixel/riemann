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
but remains slightly below its +8,410 margin.

## Progressive finalist validation

Actions run `34381542078` evaluated the retained G2 set over 1,562 TOP30 games.
The cash-250/milk-1 class led by team balance and margin:

- TOP10: 16-14, team-balanced 59.26%, margin +1,130;
- TOP20: 46-36, team-balanced 58.60%, margin +999;
- TOP30: 78-64 (54.9%), team-balanced 57.36%, margin +672.

The static baseline was TOP30 80-62 (56.3%), team-balanced 56.78%, margin +358.
Thus the overlay improves team balance and margin but loses two raw wins. A
standalone cash-250 variant, `agent_v10_subin_g2_83.py`, again scored 23-9
closed-loop versus B21 with margin +8,148. Neither G2 profile clears the static
control's closed-loop margin, so neither is submission-approved.
