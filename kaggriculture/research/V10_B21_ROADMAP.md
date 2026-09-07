# V10 roadmap: preserve B21/S16, recover wins, then extend production

Date: 2026-09-07. Frozen control: `v9_candidates/v7_opening_grid/agent_v9_v7w_b21_s16.py`.
No experiment may overwrite the frozen B21/S16 submission source.

## Evidence entering this roadmap

- TOP49 all-five/both-seat gate: B21/S16 184/490, mean score 89,115,
  margin +835; V7 188/490, 88,409, margin -901.
- Live submission 56071535 reached rating 2062.9 at the latest status query,
  below V7/Aastik/hybrid despite promising early 155k+ games.
- Windows current-control validation (50 seeds, both seats):
  - vs V7: 36-8-56, score 64%, margin +60;
  - vs Aastik: 62-38, margin +960;
  - vs hybrid: 62-36-2, score 63%, margin +979.
  This is useful paired closed-loop evidence but does not supersede TOP49 or
  live ratings.
- Windows `v10_b21_opening` sweep screened 16 policies, but its 8-seed top-K
  excluded untouched B21. All four promoted candidates failed on fresh seeds
  (45-47% score versus V7). Therefore it promotes nothing and does not prove
  B21 is locally optimal.

## A. Fine local opening search around B21/S16

The first direct Windows run completed 1,628 games in 612 seconds. Three
same-remainder candidates (`B18/S13`, `B19/S14`, `B20/S15`) each scored
**186W-14L (93%, Wilson 89-96%)** against untouched B21 over 200 fresh promotion
games. Their mean margins were respectively -14, -16, and -21: many tiny wins
and a small family of large losses. The old balanced gate incorrectly rejected
them on margin even though Kaggle's rating objective is W/L/T. They are now
rating finalists, not promoted agents; the focused fresh-seed final must measure
their direct ordering and the rare-loss family before current-control/TOP49
gates.

**Status after the focused run:** symmetric opening search is complete. The
3,000-game final created a stable mirror ladder (B18 > B19 > B20 > B21 at about
94% per neighboring matchup), but TOP49 rejected it as general strength: B18
fell to 178 wins, B19/B20 tied B21's 184 while lowering score/margin. Keep B21
as control and B20 only as a seat-specific/conditional component. Do not spend
more compute on symmetric mirror opening quantities.

Search buys 18-25 and sales around 15-20, but do not assume that only retained
wheat matters. The run showed discontinuities: B21/S17 and B25/S19 collapsed,
while adjacent configurations did not. The fixed later trajectory can depend
on the exact inventory, not merely a 4-6 wheat remainder.

Required controls:

- compare every mutation directly with untouched B21 on paired fresh seeds;
- force untouched B21 through every selection stage rather than allowing noisy
  top-K screening to drop it;
- fingerprint behavior and deduplicate equivalent candidates;
- retain strict wins, score rate, and margin as separate objectives;
- gate finalists on TOP49 and current V7/Aastik/hybrid.

## B. Seat-specific openings

Candidate-only P0/P1 constants were implemented and tested on all 245 TOP49
player-tape records, both seats. P0-only B20/S15, P1-only B20/S15, and both-seat
B20/S15 all retained exactly 184/490 wins but reduced mean margin versus frozen
B21 by 107, 100, and 207 coins respectively. No record changed win status.

The average hides a useful conditional pattern: 155 records improved margin,
77 were identical, and only 13 declined; just three `ymg_aq` records caused
material drops of roughly 8k-19k. Therefore B is complete as an unconditional
seat test with no promotion. P1 was marginally less harmful than P0, but neither
seat-specific policy is a general replacement. Preserve these rows to derive a
market-state condition; never identify the condition by opponent nickname.

## C. Conditional step-1 sale

Keep the deterministic step-0 purchase, then use the observed step-1 market to
choose a bounded sale amount. Candidate signals include wheat price/inventory
changes caused by the opponent's first order. Test explicit branches such as
S14/S16/S18 only after replay-derived thresholds are defined. Include a safe
fallback exactly matching B21.

## D. Recover the four strict wins lost versus V7

Use episode rows, not aggregate means, to classify:

1. large gains uniquely created by B21;
2. narrow V7-only wins that can be recovered cheaply;
3. inventory/trajectory collapses introduced by opening changes;
4. correlated records from the same underlying episode.

The target is to preserve B21 economics while gaining at least five strict wins,
thus exceeding V7's 188/490 rather than optimizing score alone.

**Attribution progress:** the net four-win difference comes from 14 changed
player-tape records, not four records: V7 wins both seats on eight records where
B21 loses both, while B21 wins both seats on six records where V7 loses both.
The next analysis must preserve the six B21 gains while targeting the eight V7
recoveries.

## E. Close near losses through endgame actions

For narrow losses, inspect the final selling window, product order, unused shed
inventory, fertilizer/milk/wool disposal, oversized or invalid orders, and a
one-tick sale delay. Test each endgame mutation independently. The old
`endgame24` result is only a hypothesis from another planner, not a patch to
copy.

**Target set identified:** B21 has 27 near-loss player-tape records within 2,500
coins, corresponding to 23 unique underlying episodes. Start with the three
within 500 coins, then seven within 1,000, preserving episode deduplication.

## F. Separate solution for high-score losses to 100k+ opponents

Opening tuning cannot solve games where B21 scores above 100k but loses to
120-160k. Build separately attributed production families:

- premium productivity and bounded fertilizer use;
- additional effective harvests before season end;
- removal of PASS/invalid/empty operations;
- controlled melon-to-strawberry or tomato substitution using visible demand;
- no naive animal expansion, which the alternate Meta-Lab rejected.

These are structural candidates and must not be bundled with opening/endgame
changes until each passes independently.

## Execution order and status

### Finish before nested TOP10/20/30 curriculum

1. Symmetric opening A: **complete; no replacement promoted**.
2. Collect and classify new B21 live replays: **complete for all 99 currently public B21 episodes**.
3. B seat-specific opening: **complete; no unconditional replacement promoted**.
4. D comparison versus V7: **14 changed records identified; action attribution pending**.
5. E near-loss pool: **27 controlled records / 23 unique episodes plus 14 live
   losses within 2,500 identified; endgame action audit pending**.
6. C conditional step-1 sale: use the three material seat-test failures and
   replay market state to derive thresholds; fallback must remain exact B21.

These steps remain valuable before curriculum because they create the controlled
mutation vocabulary that curriculum will select among. They were not cancelled
or replaced by the TOP10 idea.

### User-specified nested elite curriculum (no TOP31-49 training)

1. Evaluate frozen B21 only on TOP10, extract failure mechanisms, and generate
   many isolated configurations against TOP10 discovery records.
2. Freeze the best `C10` specialist and test it without retraining on TOP11-20.
3. If transfer is useful, clone C10, incorporate the transfer findings, and
   train the clone cumulatively on TOP20; preserve original C10.
4. Test frozen C20 on TOP10 and unseen TOP21-30, compare with C10 and B21, and
   extract mechanisms.
5. If useful, clone C20 and train that clone specifically/cumulatively with the
   TOP21-30 evidence; preserve C20 and call the result C30.
6. Final matrix: C10, C20, C30, and B21 on TOP10, TOP11-20, TOP21-30, and
   cumulative TOP20/TOP30 views. Do not add a TOP31-49 curriculum stage.

At every stage retain same-record/both-seat results, deduplicate underlying
episodes, report strict wins separately from score/margin, and use temporally
new live episodes as the final holdout. Develop F separately for high-score loss
families, then combine only independently demonstrated winners. Any Kaggle
upload still requires a new explicit user approval.
