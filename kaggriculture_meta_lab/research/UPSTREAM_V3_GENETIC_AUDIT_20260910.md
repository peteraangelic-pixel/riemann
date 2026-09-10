# Upstream V3 genetic audit

The latest `arena/01a0712c-riemann` is materially ahead of the earlier branch.
It includes:

- V3 Kanno-family market-timing genetic search;
- 768 population, 5 generations, 452,480 jobs;
- fast raw simulator batch runner;
- independent sibling validation;
- a winner gate and holdout candidate.

Reported winner gate summary:

```text
v3 candidate: 120/128 vs its controls, mean margin +337
v16:          127/128, mean margin +1729
German:       124/128, mean margin +991
B21:           97/128, mean margin +9709
G2:            128/128, mean margin +9215
```

The upstream branch also reports that overlay ablations on Kanno are harmful:
G2 exact, buy-stop and G4 full all regress. This supports keeping Kanno's
market timing intact rather than layering old overlays on top.

## Independent smoke of imported V3 genetic winner

Seeds 100–101, both swaps:

```text
V3 genetic winner vs Kanno V3: 4/0/0, total margin +1,424
V3 genetic winner vs B21:      4/0/0, total margin +60,730
```

The +356/game advantage over Kanno in this tiny smoke is not enough for
promotion. It justifies a larger same-seed comparison using the upstream fast
runner or our slow runner.

## Reusable infrastructure insight

The upstream `fast_h2h.py` uses a pinned raw Python simulator and checks parity
against the slow harness. This is the right infrastructure for our own
fingerprint/divergence experiments: first establish byte/euro parity, then run
large searches, while retaining a slow reference sample.
