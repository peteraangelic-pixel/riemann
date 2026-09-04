# ARC-AGI-3 experiment log

Every public `[arc-eval]` run publishes its full outcome as a GitHub check
("Public ARC graph evaluation") on the evaluated commit; compact summaries,
transition geometry and frame sketches are in the check output, full
recordings remain a 14-day workflow artifact. This file records decisions and
results that matter across sessions, so an interrupted session can resume from
committed state alone.

## 2026-09-03/04 — bounded public evaluation loop (games: ls20, vc33; 400 actions each)

Scorecard progression over 25 consecutive `[arc-eval]` commits
(oldest → newest):

| ls20 level | vc33 level | scorecard |
| --- | --- | --- |
| 0 | 1 | 0.0014–0.0022 |
| 1 | 1 | 1.787103152557669 |
| 2 | 1 | 5.35853172398624 |

- ls20 advanced 0→1 (`aabfaf0`) and 1→2 (`011a084`); vc33 never left level 1.
- `91ded55`–`5309031` (meter-budget routing) regressed ls20 to level 1;
  recovered at `ade01b1`. Since `ade01b1` the score is **frozen at 5.3585**
  (ls20 `NOT_FINISHED` on level 2, vc33 `NOT_FINISHED` on level 1) across 15+
  eval commits.
- `811d6f5` ("avoid visually revalidated forced tile entries") added blocking of
  tiles that caused a *forced avatar displacement*. Its eval (run
  33782702566) showed the agent falling out of tile navigation into generic
  `graph-simple-frontier` on ls20 level 2 and dying 3× instead of 2×; score
  unchanged. **Reverted in `73d5f2f`** — displacement alone is not reliable
  death evidence (it can be a normal teleport/control mechanic). Do not block
  tiles on displacement evidence again.

Observed ls20 level-2 failure mode (baseline `827f377`, run 33782014515):
after every game-over reset the agent replays the identical corridor route and
repeats the identical fatal decision — entering tile `(10,3)` via action 2
after the badge/control exit sequence — dying at the same geometry twice per
run (steps ~190 and ~318). Each cycle costs ~130 actions and the agent never
sees any level-2 content past that point. Terminal feedback is not retained
across resets.

Observed vc33 failure mode: the entire run stays in `graph-click-frontier`
mode (394/400 actions); the agent has not recognised a structured mechanic on
level 1 at all and dies from edge-band clicks.

## Working hypotheses

1. Retain **repeated explicit terminal (GAME_OVER) landings per level** and
   stop routing into a landing tile only after the *same* level+tile+landing
   killed the agent at least twice — much stronger evidence than displacement.
2. Find vc33 level 1's mechanic from recordings before adding new primitives.
