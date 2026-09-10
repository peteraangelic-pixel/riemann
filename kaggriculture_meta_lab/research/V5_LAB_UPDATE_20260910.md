# V5 LAB update

Upstream `arena/01a087c0-riemann` produced V5 via Rust block evolution:

- 11 donors: Kanno family, V4, peer hybrid, market parent;
- genome: German/Kanno cut plus 120 market blocks;
- population 384, 4 generations, 279,084 jobs;
- controls include V4, hybrid, V3, V2, German, B21, Subin, Yusuke, Himanshu and market parent;
- regression floors and parent injection were used.

The fresh validation (seeds 43000+, both seats, 256 games/control) reports:

```text
V5 vs V4:     240-16, +364/g
V5 vs hybrid: 236-20, +24/g
V5 vs B21:    209-47
G2 slow gate: 16-0, +7285
```

The 384-game aggregate against the hybrid is 359-25 (93.5%), while V4 is
364-20 (94.8%). The edge over the hybrid is real but narrow in material
margin, so V5 should be treated as the current primary control, not as a
closed-loop champion.

Our local slow smoke (seeds 100–101, both seats) gives:

```text
V5 vs market-genetic V3: 4-0, +1510 total
V5 vs ours V4 hybrid:   4-0, +182 total
```

The second result is effectively a tie in material margin; larger Rust
validation is required.

## Updated own LAB plan

V5 becomes the principal parent/control. Evolution must include V5, V4,
ours-peer hybrid, market-genetic V3 and Kanno as immutable parents. The next
own genome retains day cut and market blocks, and adds state-fingerprint
conditioned block selection. Selection is lexicographic:

1. zero errors/timeouts and parity;
2. regression floors on V5, hybrid, V4, G2 and B21;
3. positive material margin on fresh holdout;
4. only then maximize aggregate margin.

No promotion from mirror win-rate alone, and no closed-loop claim from these
open-loop tapes.
