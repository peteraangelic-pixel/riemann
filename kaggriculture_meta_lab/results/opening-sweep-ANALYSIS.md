# Opening sweep analysis — the "91% win" near-tie trap

User run: `opening-sweep-20260907-114822.md` (75 seeds x2 seats = 150 games/var,
24 workers, 675 s). b17_s12 and b19_s14 both showed **91.3% win rate (137-13)**
vs the B21/S16 champion, with mean margin ~0. Follow-up closed-loop tests show
this is **NOT a real strength gain**:

## Evidence

```
b17 vs champion (mirror, near-identical tape):  41W 7L,  margin median +$9, mean |margin| ~$87
b17 vs v7_scripted (a DIFFERENT opponent):      10W 2L 12T, mean cash 82,588
champion vs v7_scripted (same seeds):          10W 2L 12T, mean cash 82,588  <- identical
```

Against a genuinely different strong opponent, b17 and the champion produce the
**same mean cash to the dollar**. The 91% win rate appears ONLY when the two
tapes are nearly the same: the opening changes the cash by a handful of dollars,
which breaks a coin-flip tie in one direction. That is a tie-break artefact, not
strength. In the Bradley-Terry final you are NOT paired with your own twin; you
face diverse opponents, where b17 ≡ champion.

## Rule going forward

Do not promote an opening variant on win-rate alone. Require **BOTH**:
1. mean cash/margin vs a DIVERSE opponent set (v7_scripted + a reactive agent),
   not just vs the champion tape;
2. a material margin (tens-to-thousands of dollars), not a ~$0 mirror edge.

The opening is still a HUGE lever (buy 21->23 wheat = -49k, -50k; the schedule
is finely tuned), so opening search stays central — but the acceptance metric
is absolute cash vs varied opponents (and the open-loop TOP49 corpus), exactly
as `docs/CURRENT_20260907.md` promotion rules say: "never infer closed-loop
rating from an open-loop tape" and conversely don't trust a mirror win-rate.
