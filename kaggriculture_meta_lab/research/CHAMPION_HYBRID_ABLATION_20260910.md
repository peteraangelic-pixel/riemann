# GermanJurado1 hybrid ablation

Tested the first guarded wrapper against B21/S16 on seeds 100–103, both swaps.

## Result

```text
hybrid: 8-0, mean candidate 92,516.0, mean B21 85,375.5, total margin +57,124
pure tape reference on same seeds: 8-0, mean candidate 99,464.25, mean B21 85,303.75, total margin +113,284
```

The attempted endgame liquidation override made the candidate materially worse.
It has been removed. This is a useful negative result: do not add a generic
sell-all override without matching the tape's actual shed/action semantics.

The guarded wrapper remains only as a crash/schema experiment, not a promoted
candidate. The pure corrected GermanJurado1 tape remains the current local
champion control until a reactive variant beats it on identical seeds.
