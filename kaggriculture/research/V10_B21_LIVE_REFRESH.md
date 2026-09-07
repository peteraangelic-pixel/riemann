# B21/S16 live replay refresh — submission 56071535

Collected from Kaggle's public episode API on 2026-09-07. This is live telemetry,
not a controlled same-seed or both-seat benchmark. Matchmaking and rating are
path-dependent, so these rows are a temporal holdout and mechanism source only.

## Coverage and result

- 99 newly collected public episodes, all explicitly tagged to submission `56071535`.
- 56 wins, 43 losses, no ties (56.6% observed win rate).
- Mean B21 cash: 89,595; mean opponent cash: 85,504; mean margin: +4,092.
- Median B21 cash: 89,168; median margin: only +590.
- Public rating at the last separate query was 2062.9. The replay result confirms
  that high mean margin did not translate into a dominant W/L record.

## Recovery pool

Of the 43 losses:

- 3 were within 1,000 coins;
- 14 were within 2,500;
- 25 were within 5,000;
- 34 were within 10,000;
- 14 losses still had B21 cash above 100,000; four exceeded 120,000 and one
  exceeded 140,000.

Closest losses were:

| Episode | Opponent | B21 | Opponent | Margin |
|---:|---|---:|---:|---:|
| 106506287 | hidenov | 112,414 | 113,069 | -655 |
| 106410679 | darcy132 | 83,007 | 83,707 | -700 |
| 106468183 | DECEM | 85,480 | 86,348 | -868 |
| 106396180 | laoma fighting | 86,001 | 87,050 | -1,049 |
| 106402372 | Daniel Guo | 103,826 | 104,896 | -1,070 |
| 106415339 | Reinforcement Larping | 67,818 | 68,905 | -1,087 |
| 106432984 | Mohamed El-Nageeb | 117,645 | 118,821 | -1,176 |
| 106427271 | Kurisu Makise | 89,620 | 90,817 | -1,197 |
| 106422737 | Agricola | 59,126 | 60,431 | -1,305 |
| 106462754 | Olympus | 147,732 | 149,151 | -1,419 |

These are stronger endgame-attribution targets than selecting losses solely by
low B21 cash. Episode 106462754 in particular is a premium-output near-loss.

## Opponent mechanism signal

Opening quantities were recovered directly from each opponent's first two
replay actions. The most common were B13/S8 (36 games, B21 21-15, median margin
+1,178), B13/S9 (15 games, B21 6-9, median -1,419), and B30/S25 (nine games,
B21 5-4, median +178). B20/S15 appeared only six times and B21 was 2-4 with
median -2,564. This is useful context for the controlled seat-specific B20 test,
but opponent policy differences after the opening make it non-causal.

The opponent summary fingerprints are descriptive, not causal:

- The common 9-cow/8-sheep/no-goose/33-strawberry/12-melon footprint appeared
  33 times; B21 was 22-11 with mean margin +205. It is effectively a near-tie
  family despite the positive record.
- The 3-goose/9-cow/5-sheep footprint appeared nine times; B21 was 2-7 with mean
  margin -3,548.
- The 8-cow/9-sheep/no-goose footprint appeared eight times; B21 was 1-7 with
  mean margin -1,349.
- Several 6-cow/11-sheep families were also consistently negative in this small
  sample. These patterns support controlled goose and cow/sheep-mix attribution,
  but do not justify copying an opponent policy or changing B21 wholesale.

## Data caveats

The existing analyzer counts attempted opponent market quantities from replay
actions. Some opponents emit absurdly large sale quantities; these are not
proof that the quantities were fulfilled. Peak board composition is safer than
raw attempted-sale totals for archetype classification.

## Decision

1. Keep B21 frozen; this live set is diagnosis/holdout evidence, not training.
2. Add the ten closest losses above to the D/E action-attribution queue.
3. Preserve high-output losses separately: they need small tie conversion rather
   than broad production replacement.
4. Test goose and cow/sheep mechanisms only as isolated conditional components.
5. No Kaggle upload is authorized or implied by this refresh.
