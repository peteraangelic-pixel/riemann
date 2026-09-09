# V10 market overlay — Generation 1

## Repair

Generation 1 projects pre-market shed inventory through live units' same-turn
DROP, PLACE and PICKUP operations, including access position, shed capacity,
insertion order and live-hand truncation. Sale fractions are one per-product
turn budget. An enabled profile with all defaults is required to match the
disabled control exactly.

## TOP10 screen

Actions run `34379566745` evaluated 500 sparse identity-local profiles in 15,000
Rust games (15 non-source best-listed TOP10 records, both seats). The identity
contract passed. The leading profile was:

```json
{"enabled":true,"start_day":8,"cash_reserve":200,
 "min_wheat_price":30,"milk_reserve":1}
```

It scored 16-14 (53.3%), team-balanced 59.26%, mean margin +1,093, versus the
disabled baseline's 14-16 (46.7%), team-balanced 48.15%, margin -282. The second
profile also scored 16-14; several milk-reserve profiles reached 15-15 with
positive margin.

## Closed-loop check

A standalone implementation, `agent_v10_subin_g1_466.py`, was compared with the
static Subin control on the same 16 fresh seeds and both seats against B21/S16:

- G1-466: 23-9 (71.9%), mean margin +8,059, no errors;
- static Subin: 23-9 (71.9%), mean margin +8,410, no errors.

Thus G1 is a genuine open-loop lead but has not improved the closed-loop control
on this holdout. It is not submission-approved. The retained ten profiles move
to progressive TOP20/TOP30 validation; no new Kaggle upload is warranted yet.
