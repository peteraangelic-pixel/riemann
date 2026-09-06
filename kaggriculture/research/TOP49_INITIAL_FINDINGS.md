# TOP49 initial findings — 2026-09-06

## Data recovery

`per_replay.zip` contains 245 player-replay records (49 players × five), but
only 196 unique episodes because 49 games appear under both TOP49 participants.
The compact generic parser retained 25 early state snapshots and broad action
counts, but lost final scores, winner labels, product identities, and order
quantities. Conclusions that need those fields therefore use full replay bodies,
not the compact parser's null/UNKNOWN fields.

Fingerprinting used 327 early-policy dimensions. Most players form a broad
Aastik-adjacent population, but two strong outliers appeared:

- `我都先道歉`: very stable across five games and delays its first sale until
  turn 28 rather than Aastik's turn 2.
- `get some fries`: a much higher-turnover, variable market policy.

A second delayed-sale family includes JamesJJJJJ/Beyond/taiseiu around turn 31.
SJY321 and Crop Dusta delay first sale until turn 49, but their full policies
are not equivalent: Stage L rejected transplanted Crop Dusta openings, while
SJY321's full trajectory has a much more aggressive wheat economy.

Actions run `34052405876` downloaded 31 unique full replay bodies for the
selected families and controls.

## What the full replays establish

| Target policy | Original games W-L | Target mean | Opponent mean | Distinguishing behaviour |
|---|---:|---:|---:|---|
| Aastik Rajan15 | 1-4 | 64,606 | 71,823 | known Aastik family; difficult recent opponents |
| 我都先道歉 | **5-0** | **97,581** | 90,996 | no sale before turn 28; adaptive crop/animal mix including tomato |
| get some fries | 3-2 | 91,802 | 92,328 | 180–299 product-buy orders; high fertilizer/wheat turnover |
| SJY321 | **4-1** | **110,513** | 92,562 | sale delayed to turn 49; buys roughly 680–1,488 wheat units; one 160,813 game |
| Ant | 4-1 | 70,040 | 66,553 | identical action totals in all five games, but lower economic ceiling |
| JamesJJJJJ | 2-3 | 74,200 | 76,577 | delayed-sale family, but weak initial evidence |
| Mengfei Li | 1-4 | 82,833 | 87,523 | relatively Aastik-like and lost four direct games to 我都先道歉 |

The two strongest third-policy sources are therefore **我都先道歉** and
**SJY321**. `get some fries` remains a useful market-stress family rather than
the first reconstruction target.

## Controlled open-loop screen of current V8

Actions run `34052546519` replayed each target's actions against both frozen V8
controls on both seats. Each row has five independent episode seeds mirrored
across two seats; it is ten games but only five independent trajectories.

| Opponent tape family | V8 Aastik W-L | Aastik margin | V8 hybrid W-L | Hybrid margin |
|---|---:|---:|---:|---:|
| Aastik Rajan15 | 6-4 | +14,980 | 6-4 | +5,125 |
| 我都先道歉 | **0-10** | **-13,172** | **0-10** | **-13,170** |
| SJY321 | 4-6 | **-18,198** | 4-6 | **-18,194** |
| get some fries | 4-6 | -68 | **6-4** | **+1,842** |

This is the first direct evidence in the expanded corpus of a policy family
that both V8 controls consistently fail to cover. The `我都先道歉` result is not
a tiny opening-only artefact: it repeats over five source trajectories and both
seats. SJY321 is also strategically distinct and has the highest observed
source-policy mean, though V8 wins two of its five independent trajectories.

The hybrid's Renoir opening helps against `get some fries`, converting one
independent trajectory from two losses to two wins. It does essentially nothing
against the two strongest uncovered families.

## Interpretation and next gate

This is **open-loop discovery**, not proof that copying a trajectory will improve
closed-loop rating. Stage L showed that transplanting an elite opening can fail
badly when separated from its full economy. Therefore:

1. Keep `agent_v8_aastik.py` and `agent_v8_hybrid.py` byte-for-byte frozen.
2. Reconstruct separate `agent_v9_third_*` full-trajectory candidates from all
   five 我都先道歉 and all five SJY321 source policies.
3. Screen each reconstruction independently against the same four TOP49
   families plus the existing public/common-loss corpora.
4. Compare full-policy candidates before extracting opening/market primitives.
5. Promote only repeatable winners to paired closed-loop and fresh holdouts.

No Kaggle submission is justified or authorized by this screen.
