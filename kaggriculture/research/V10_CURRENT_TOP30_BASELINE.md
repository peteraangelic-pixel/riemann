# Current TOP30 replay baseline (2026-09-08 snapshot)

## Provenance and gate

Input is the user-uploaded `TOP30.7z` at commit `1ebeefd`, SHA-256
`f6c68c7475128aad850b9462cf89a7948565a254d5eb493e54923b3b5320f592`.
The independent inventory audit passed all 150 selected raw files; see
`kaggriculture_meta_lab/corpus/top30_2026-09-08/`.

The calculation used the parity-gated Rust raw-tape adapter in Actions run
`34280083082`. For each team-policy record it preserved `info.seed`, selected
the named team's recorded seat, and ran B21/S16 in both physical seats. All 300
games completed without an error. This is an open-loop stress test against
recorded actions, not a closed-loop leaderboard reconstruction.

## B21/S16 result

| Curriculum | records / games | B21 W-L-T | score | Wilson 95% | mean margin | mean cash B21 / tape |
|---|---:|---:|---:|---:|---:|---:|
| TOP10, all recent | 50 / 100 | 23-77-0 | 23.0% | 15.8–32.2% | -2,301 | 91,172 / 93,473 |
| TOP20, all recent | 100 / 200 | 39-161-0 | 19.5% | 14.6–25.5% | -5,744 | 90,873 / 96,617 |
| TOP30, all recent | 150 / 300 | 75-225-0 | 25.0% | 20.4–30.2% | -3,862 | 90,803 / 94,664 |
| TOP10, best-listed submissions | 16 / 32 | 8-24-0 | 25.0% | 13.3–42.1% | -7,117 | 94,576 / 101,692 |
| TOP20, best-listed submissions | 42 / 84 | 15-69-0 | 17.9% | 11.1–27.4% | -8,028 | 94,447 / 102,476 |
| TOP30, best-listed submissions | 72 / 144 | 37-107-0 | 25.7% | 19.3–33.4% | -4,958 | 94,150 / 99,108 |

The result is seat-stable rather than a seat artifact: on all TOP30 records B21
scored 24.0% as player 0 and 26.0% as player 1. The old B21 tape is therefore a
clear loser against the current replay distribution and must remain only as the
control for improvement, not as a submission candidate.

## What changed strategically

An independent action census of the best-listed TOP30 subset shows a recognizable
new meta built around roughly 10.4 hands, three unlocked quadrants, about 14.8
pastures, 6.5 sheep, 6.4 cows, and 1.7 geese at episode end. Compared with the
B21 tape, these records issue far more market sales (about 336 versus 215),
WHEAT seed purchases (about 79 versus 25), and fertilizer sales (about 95 versus
60). They average about 101.9k recorded cash.

This is not evidence that blindly changing three counts will transfer: the
leader policies are reactive and the public corpus contains mixed submissions.
It does establish the next bounded research direction: screen representative
current TOP10 best-submission policy tapes, then require stability as the
curriculum expands to TOP20 and TOP30. Any resulting static imitation remains an
open-loop lead and must later beat controls in closed-loop tests.

The exact 300 rows and cumulative summaries are stored in
`kaggriculture_meta_lab/results/top30-b21-baseline-20260908.json`.
