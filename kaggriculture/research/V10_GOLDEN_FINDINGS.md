# V10 golden findings ledger

Purpose: preserve valuable hypotheses, negative results, and transferable
mechanics without merging their provenance. A finding here is not automatically
a promoted agent change.

Review protocol: read this ledger before each new experiment family and after
each promotion gate. Prefix findings with:

- `[ACTIVE]` worth testing or reusing now;
- `[USED]` already incorporated into tooling/policy/roadmap (retain for traceability);
- `[CONTEXT]` failed in one chassis but may transfer in another;
- `[REJECTED]` sufficiently disproven; do not repeat without genuinely new evidence;
- `[PENDING]` promising but not yet attributed.

Do not delete useful negative evidence merely because it failed. Remove only
low-information noise, duplicates, or claims superseded by stronger evidence;
keep context-dependent mechanics explicitly marked rather than silently losing
them.

## Source A — our Windows Meta-Lab uploads

- `[USED]` Direct B21 opening run (1,628 games): B18/S13, B19/S14, and B20/S15 each
  scored 186-14 against B21. The focused confirmation (3,000 games) again put
  every lower-transaction neighbor around 91-94% against its near-identical
  successor. This is a stable mirror tie-break effect, not broad strength.
- `[USED]` Exact opening quantities create cliffs: several one-unit changes produced
  0% and losses of 11k-27k. Fixed tape inventory and market state are tightly
  coupled; "same wheat remainder" is not sufficient safety.
- `[CONTEXT]` Current-control validation remains useful but not decisive: B21 passed local
  V7/Aastik/hybrid controls while its live rating and elite tape behavior did
  not preserve the same ordering.

## Source B — our GitHub TOP49 same-record/both-seat gate

- `[USED]` B21 remains the symmetric-opening control: 184/490, score 89,115, margin +835.
- `[ACTIVE]` B20/S15 retained 184 wins but fell to 88,811 and +628. It is not a general
  replacement, but is the only lower-transaction opening worth retaining as a
  seat-specific/conditional component.
- `[REJECTED]` B19/S14 retained 184 wins with negative margin; B18/S13 fell to 178 wins.
  B18 is an anti-B21 mirror specialist and must not be promoted as a generalist.
- `[ACTIVE]` Exact V7/B21 comparison changed 14 player-tape records: V7 gained both-seat
  wins on eight records while B21 gained both-seat wins on six, netting V7's
  four-win aggregate advantage. This is a trade, not four isolated losses.
- `[ACTIVE]` B21 has 27 player-tape near-loss records within 2,500 coins, representing 23
  unique underlying episodes. These are the primary D/E recovery pool.

## Source C — alternate Arena branch `arena/01a075fa-riemann`

- `[USED]` Its independent opening sweep found the same mirror trap (about 91% for
  B17/S12 and B19/S14 with approximately zero material margin). Against a
  genuinely different V7 control, candidate and champion mean cash matched.
- `[REJECTED]` Its latest old V8-fertilizer validation versus current B21 was 0-200 with
  mean margin -66,343. Preserve only isolated fertilizer mechanics; reject the
  old policy as a competitive base.
- `[ACTIVE]` Useful engineering: Windows-safe pytest paths (`pytest.ini`, `conftest.py`,
  `tmp_path`) and a lossless tape-opening patch test.
- `[PENDING]` Potential acceleration: a Rust/Rayon simulator handoff spec with shared
  market and bit-exact reward parity as non-negotiable requirements. Claimed
  8-20x speedup is unmeasured; do not trust Rust outcomes before 50-100+ exact
  Python parity seeds across multiple tape pairs.

## Source D — historical fertilizer sweep uploaded by the user

- `[CONTEXT]` In the stale heuristic planner, detour radius 1 was strongest directly versus
  old V7, endgame day 24 led field-wide Bradley-Terry, and carrot fraction 0.25
  was a smaller positive lever.
- `[USED]` Hand-count and planted-swap constants frequently produced identical behavior.
  Deduplicate behavior, not merely configuration names.
- `[CONTEXT]` These are hypotheses for isolated B21-compatible mutations, never wholesale
  code transfers or current promotion evidence.

## Source E — live Kaggle observations and official mechanics

- `[USED]` Rating uses W/L/T, not coin margin. Small wins are valuable, but mirror-only
  wins can be misleading when the live opponent population is diverse.
- `[PENDING]` B21 has demonstrated occasional 155k+ games and a promising early climb, yet
  its aggregate live rating trailed older controls at the last status query.
  New completed B21 episodes remain a required holdout.

## Active decisions

1. Keep frozen B21/S16 as current control.
2. Finish the pre-curriculum plan: live refresh, D/E loss attribution,
   seat-specific opening, then conditional step-1 sale.
3. Use B20/S15—not B18—as the first alternate opening component.
4. Build nested elite curriculum only for TOP10, TOP11-20, and TOP21-30; omit
   TOP31-49 training per user direction. Retain full TOP49 only as historical
   context, not a new curriculum stage.
5. Preserve frozen specialists at C10, C20, and C30 and compare all of them with
   B21; never overwrite a specialist while extending its clone.
6. Develop structural premium/fertilizer/endgame policies separately and bundle
   only demonstrated winners.
