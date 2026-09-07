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

Introduce candidate-only constants for P0 and P1 buy/sell amounts. Test one seat
at a time before a factorial combination. Market order changes prices, so the
best P0 and P1 opening need not match. Never modify frozen V7 or frozen B21.

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

## E. Close near losses through endgame actions

For narrow losses, inspect the final selling window, product order, unused shed
inventory, fertilizer/milk/wool disposal, oversized or invalid orders, and a
one-tick sale delay. Test each endgame mutation independently. The old
`endgame24` result is only a hypothesis from another planner, not a patch to
copy.

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

## Promotion order

1. Collect and classify new B21 live replays.
2. Fix the local opening experiment so untouched B21 is the direct control.
3. Run A, then B, then C as separate families.
4. Use D and E to promote by strict wins and recover near losses.
5. Develop F separately for elite high-score loss families.
6. Combine only independently demonstrated winners in named V10 bundles.
7. Re-run paired current controls, TOP49 both seats, then old archive holdouts.
8. A Kaggle upload requires a new explicit user approval.
