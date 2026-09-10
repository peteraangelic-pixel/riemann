# Corpus benchmark audit

The latest peer branch finally ran the missing full TOP15 audit. This is the
current reference table; it is not a benchmark of our local V6, because our V6
is a Kaggle-schema adaptive baseline and is not the same static tape family as
V3/V4/V5.

## Fresh TOP15, 105 selected policies, 8 common seeds, both seats

| candidate | W-L | score rate | mean margin | mean reward |
|---|---:|---:|---:|---:|
| V16 | 1471-209 | 87.56% | +10028 | 90022 |
| V3 | 1510-170 | 89.88% | +9551 | 89373 |
| V5 | 1455-225 | 86.61% | +6897 | 84579 |
| V4 | 1449-231 | 86.25% | +5996 | 83630 |

Best-listed TOP15 only:

| candidate | W-L | score rate | mean margin |
|---|---:|---:|---:|
| V3 | 793-103 | 88.50% | +7754 |
| V16 | 751-145 | 83.82% | +7980 |
| V5 | 732-164 | 81.70% | +2546 |
| V4 | 731-165 | 81.58% | +1062 |

Original replay seeds, best-listed only:

| candidate | W-L | score rate | mean margin |
|---|---:|---:|---:|
| V3 | 75-37 | 66.96% | +978 |
| V16 | 60-52 | 53.57% | +980 |
| V4 | 67-45 | 59.82% | -7198 |
| V5 | 67-45 | 59.82% | -5236 |

## Critical hidden control

DeeperNet breaks V4/V5:

```text
V16: 90-22, +1624
V3:  104-8, +2777
V4:  16-96, -53590
V5:  16-96, -42334
```

This invalidates promoting V5 from the previous narrow control panel. Every
new V6/V6b candidate must include DeeperNet or a demonstrably equivalent
archetype as a hard regression floor.

## Our benchmark status

The V6 file in this branch is an experimental V5-derived telemetry baseline,
not a completed static tape champion. Therefore no honest TOP15/TOP30/TOP7
score exists for it yet. The previously reported V5/V4/V3 H2H numbers are not
substitutes for corpus benchmarks.

The next benchmark campaign must first compile a stable V6b artifact and then
run the same candidate against TOP5, TOP10, TOP15 and TOP7, with TOP30 reserved
for a later benchmark. Required report columns are W-L, score rate, mean
material margin, mean candidate reward, worst margin, errors and timeouts.
