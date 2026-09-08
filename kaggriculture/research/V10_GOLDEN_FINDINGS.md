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
- `[USED]` B20/S15 retained 184 wins but fell to 88,811 and +628. Isolating it
  on P0 or P1 also retained all 184 wins but reduced mean margin by 107 or 100;
  no player-tape record changed win status. Reject it as an unconditional
  seat-specific replacement.
- `[ACTIVE]` The seat test exposed a conditional shape: 155/245 records improved,
  77 were identical, and 13 declined, with three `ymg_aq` tapes causing nearly
  all material harm (roughly -8k to -19k). Derive a condition from observable
  market state—not nickname—with exact B21 fallback.
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
- `[USED]` Rust/Rayon static-tape acceleration is now independently validated
  and integrated into the LAB: 585 bit-exact Python comparisons, 22,597 exact
  states, mixed hand semantics, deterministic 14k batches, and roughly 112-222x
  measured small-batch speedup on a four-logical-CPU runner. Treat the number as
  a simulator benchmark—not a full-sweep guarantee. Repository-native run
  `34232195149` then matched all 14 static/raw-replay LAB games exactly across
  both seats (including seed 0). The newer `01a07c52` backend then added
  non-executing AST classification, normalized behavior fingerprints, safe
  duplicate-game reuse and fallback-row identity checks; 23,104 action checks
  and 16 full games passed. Use it for static sweeps; reactive policies stay on
  the audited Python engine. The refreshed repository-native workflow passed
  all checks in Actions run `34251146717`, including 61 adapter/protocol tests
  and the 14-game exact static/raw integration gate.

## Source D — current TOP30 replay snapshot (2026-09-08)

- The user-uploaded 23.1 MB `TOP30.7z` expands to 150 selected raw records for
  30 current teams. Independent validation found 129 unique episodes, valid
  integer seeds, 720 steps in every replay, finite matching rewards, and 300
  `DONE` statuses; archive and per-record hashes are inventoried under
  `kaggriculture_meta_lab/corpus/top30_2026-09-08/`.
- Selection is newest-across-active-submissions, not five records from each
  leaderboard-best submission: only 72/150 records are from the best-scoring
  active submission listed in the manifest. Report all-recent and best-listed
  subsets separately.
- The bundled analysis cannot determine scores: 0/150 raw reports have a final
  score or winner, and 30 manifests were analyzed as pseudo-replays. It is
  exploratory only; use raw data for gates.
- Parity-gated Rust run `34280083082` evaluated B21 both seats on all 150 tapes
  with zero errors. B21 scored 75-225 (25.0%, Wilson 20.4–30.2), mean margin
  -3,862; on the 72 best-listed records it scored 37-107 (25.7%), margin -4,958.
  The current corpus decisively rejects B21 as a submission candidate.
- Current best-listed behavior is animal/hand heavy (about 10.4 hands, 14.8
  pastures, 6.5 sheep, 6.4 cows) and sells much more frequently than B21. Use a
  bounded TOP10 -> TOP20 -> TOP30 curriculum to derive leads, followed by
  closed-loop control gates.

## Source E — historical fertilizer sweep uploaded by the user

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
- `[USED]` The focused refresh collected all 99 available public B21/S16 episodes:
  56-43, mean cash 89,595, mean margin +4,092, but median margin only +590.
  Positive mean margin did not produce a dominant W/L record.
- `[ACTIVE]` The live recovery pool contains 14 losses within 2,500 coins and 14
  losses where B21 still exceeded 100,000 cash. Treat close high-output losses
  separately from low-output structural failures.
- `[PENDING]` Opponent board fingerprints suggest targeted pressure from
  3-goose/9-cow/5-sheep and several 6-cow/11-sheep families. This is
  descriptive live evidence only; test goose and cow/sheep mechanisms in
  controlled isolation.

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
