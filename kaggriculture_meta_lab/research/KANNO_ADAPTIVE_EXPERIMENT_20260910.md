# Kanno V3 adaptive experiment

Added:

```text
agents/variants/champion_tape_kanno_adaptive_experimental.py
```

Design:

```text
Kanno V3 tape by default
→ real-schema divergence check
→ V10 reactive fallback only when a requested purchase is clearly impossible
```

The first divergence detector is intentionally conservative: it diverts only
when a tape purchase is requested while visible farm money is non-positive. It
does not invent a market price model or overwrite Kanno's late-game timing.

## Smoke result

Against B21/S16, seeds 100–103, both swaps:

```text
8 wins / 0 losses / 0 ties
candidate mean: 99,454.0
B21 mean:       85,692.75
margin sum:     +110,090
```

This is close to the pure Kanno V3 result and therefore does not show a
regression on this small smoke. It is not evidence of an adaptive advantage.
The next detector must use replay-derived state fingerprints (cash, unlocked
land, worker count, inventory, animal placement and market queue) rather than
adding arbitrary price thresholds.
