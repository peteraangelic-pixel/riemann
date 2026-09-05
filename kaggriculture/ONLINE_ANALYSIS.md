# Kaggriculture online analysis

> Submission policy: online uploads consume a limited daily allowance. Never
> trigger a Kaggle submission without the user's explicit approval. Strategy
> collection, CI, replay benchmarks, and parallel tuning do not imply upload
> approval.

Snapshot: 2026-09-05. Submission ref: `56032076` (v2, commit `c393cfe`).

## Public matches collected

| Episode | Side | Result | Our money | Opponent | Opponent money |
|---|---:|---|---:|---|---:|
| 105787151 | 0 | loss | 26,090 | Team21 | 69,035 |
| 105788063 | 0 | loss | 26,308 | Alejandro Rendon B. | 98,306 |
| 105788970 | 1 | loss | 25,252 | foundtion | 81,201 |
| 105789885 | 1 | win | 25,301 | cshara | 23,879 |
| 105790213 | 0 | win | 23,706 | Khôi Trương | 16,188 |
| 105790807 | 1 | win | 27,559 | Achintya Rai | 9,461 |
| 105791750 | 0 | loss | 34,083 | Suresh Chandra Mangena | 49,506 |
| 105792708 | 0 | loss | 27,289 | Sai_Dattu | 37,361 |
| 105793659 | 0 | loss | 27,811 | Rudransh Singh Rathore | 69,255 |
| 105794581 | 0 | loss | 26,210 | Pavel Filin | 47,897 |
| 105795574 | 1 | win | 29,266 | Ivan Zagorulko | 12,697 |
| 105796497 | 1 | win | 28,864 | Teja Pattem | 16,215 |
| 105797403 | 0 | loss | 29,163 | phoenix_merk | 66,240 |
| 105798313 | 1 | loss | 26,546 | dauriel | 70,730 |
| 105799286 | 0 | win | 30,663 | Shrey Modi | 17,222 |
| 105800261 | 0 | loss | 23,809 | revv0o | 33,784 |

Complete v2 sample at the snapshot: 6 wins, 10 losses. V2 averaged 27,370;
opponents averaged 44,936. Our output stayed narrow while opponent strength
varied widely, confirming that the wheat/carrot/melon economy is reliable but
has a low earnings ceiling.

## Pattern separating wins from losses

The 15-match sample separates strong and weak opponents quantitatively:

| Matches | Opponent avg | Peak animals avg | Peak strawberries avg | Peak melons avg |
|---|---:|---:|---:|---:|
| Our 6 wins | 15,944 | 4.5 | 6.2 | 7.8 |
| Our 10 losses | 62,332 | 13.8 | 19.9 | 15.2 |

The pattern is not tied to one opponent. Strong agents repeatedly combined a
serviced animal herd with fertilizer and high-value crops. Examples include
Team21 (7 cows, 6 sheep), Alejandro (7 cows, 5 sheep), foundtion (6 cows, 7
sheep), Rudransh (6 geese, 6 cows, 8 sheep), and dauriel (31 animals). Suresh
showed a different viable route with 13 geese, eggs, fertilizer, strawberries
and melons.

The weaker opponents either failed to service purchased animals or stayed
close to a crop-only baseline. Merely possessing crops, animals or structures
was not enough; daily logistics is the differentiator.

## Rejected experiment

A first strawberry-only extension was tested and reverted before submission.
Against v2 it scored 0 wins in 10 games (23.7k average versus v2's 26.7k).
Smaller belts (`STRAWBERRY_KAPPA` 0.08–0.32) also lost every five-seed
head-to-head. Premium crops cannot simply be added to the existing generic
watering conveyor: they need labor capacity and the cash flow of a coherent
animal/fertilizer system.

## v3 goose economy

The first complete animal subsystem uses compact coops and dedicated workers
for animal placement, wheat pickup, FEED, CARE, egg harvest and fertilizer
collection. A seven-job GitHub Actions matrix ran 168 matched games (12 seeds,
both player positions per configuration):

| Geese | Geese/worker | Feed stock days | W-L | Candidate avg | v2 avg |
|---:|---:|---:|---:|---:|---:|
| 5 | 2 | 3 | **24-0** | **40,888** | 26,837 |
| 4 | 2 | 3 | 24-0 | 38,531 | 27,161 |
| 5 | 2 | 2 | 24-0 | 34,266 | 26,941 |
| 5 | 3 | 3 | 24-0 | 33,968 | 25,885 |
| 6 | 3 | 3 | 3-21 | 25,766 | 26,560 |
| 5 | 2 | 4 | 0-24 | 24,185 | 26,337 |
| 6 | 2 | 3 | 0-24 | 20,864 | 26,247 |

Five geese, two per worker and three days of feed stock was selected for v3.
It averaged about 38.2k per side in ten-seed v3 self-play, but its first two
public matches exposed two coupled bugs: the agent sold all home-grown wheat
before buying feed back from a scarcity market, and independently checked each
queued purchase against the same opening balance. Against strong wheat buyers
this starved the geese and sometimes left no cash to rehire workers.

V3.1 retains a three-day feed reserve and tracks spend across the entire order
queue while preserving 300 coins of operating cash. Four parallel GitHub
Actions shards replayed 18 real opponent action streams in their original
seeds and positions:

- submitted policies: 27,028 average;
- v3.1 candidate: 40,451 average;
- average improvement: +13,423;
- candidate result against scripted opponents: 9 wins, 9 losses.

## v4 species sweep

The same logistics state machine was generalized to COOP/PASTURE and tested
with geese, cows and sheep over all 18 collected real opponent streams:

| Candidate | Replay avg | Wins/18 |
|---|---:|---:|
| goose5 (v3.1) | 40,451 | 9 |
| sheep4 | 49,296 | 13 |
| cow4 | 53,953 | 12 |
| cow5 | **55,286** | **16** |
| cow6 | 54,679 | 15 |
| cow8 | 56,700 | 15 |

Cow8 had the highest replay average but excessive variance in self-play
(20.1k–62.2k) and only 7/10 wins against v3.1. Cow5 was selected: it averaged
55.7k versus v3.1's 40.2k with 9/10 wins, and 45.7k in self-play. Future work
can add mixed herds and fertilized high-value crops on top of cow5.

## New online evidence and diversified V5 search

Submission refs are now confirmed: v3 is `56033159`; v3.1 is `56033582`.
Across its first five public games v3.1 scored 3-2 and averaged 41,395 versus
50,369, improving substantially on v3's expanded 11-game record (3-8,
29,575 versus 57,305) but still losing to scaled economies. New opponents
reinforce that there is no single mandatory build: Farmville Redux reached
76,067 with 11 cows, 9 sheep and premium crops; Michael Brown reached 69,721
with 50 strawberries and 25 melons but no animals; JIUZHOU CHAN reached 97,503
with 7 cows, 11 strawberries and 21 melons. This diversity is why V5 is a
multi-profile search rather than another one-dimensional animal count sweep.

The first 20-profile V5 Actions matrix (run `33969663450`) completed over the
original 18-replay corpus. Mixed livestock without strawberries dominated:
8 cows + 6 sheep averaged 82,979 (17/18), 6 cows + 4 sheep averaged 78,460
(18/18), and 5 cows + 4 sheep averaged 74,640 (17/18). A fertilized
5-cow/4-sheep/16-strawberry profile reached 66,785 (17/18) when raw fertilizer
was sold rather than stockpiled. Several crop-heavy profiles collapsed,
showing that premium diversity must be funded and routed coherently rather
than copied as tile counts. The next matrix re-runs against all 32 collected
real streams and adds 8C/4S, 10C/4S, 8C/8S, 20-animal, 42-strawberry/12-melon,
and fertilizer-sale variants.

The 28-profile rerun on all 32 streams (`33969901774`) selected 8 cows +
6 sheep while selling raw fertilizer: **82,552.5 average and 31/32 wins**.
The only loss was against Zikai Chen's visible 12-cow/21-sheep farm: our wool
supply helped create the wrong shared-market interaction. A deterministic
counter switches to eight cows when at least ten opposing sheep become
visible. The exact 32-replay rerun then scored **83,045.7 and 32/32 wins**,
including 80,999 versus Zikai's replayed 55,121 and 102,324 versus Dmitri's
96,200.

## V5 refinement sweeps

Four further Actions matrices measured **134 refinements** of that adaptive
8-cow/6-sheep baseline over all 32 real replay streams (`33971136612`,
`33971836674`, `33972399603`, `33972812879`). They varied land timing, animal
workers, feed reserve, purchase batches, staffing capacity, service priority,
operating cash, sell floor, endgame liquidation, opponent-response threshold,
herd composition, melon count/layout and small strawberry additions.

The large gains came from coherent interactions rather than adding every
feature: early NE/SW expansion raised the mean to 86,652; six compact melons
raised it to 92,644; selling even at the $1 floor and ending melon planting on
day 18 selected the finalist at **93,615 average with 32/32 wins**. It scored
110,860 against Dmitri's replayed 94,307, 87,815 against Zikai's 60,957, and
98,927 against Michael Brown's crop-heavy 74,227. Small strawberry additions
still hurt (72,284 for four; 8,724 for two), proving the current strawberry
routing/capital schedule is defective rather than that strawberries are
intrinsically bad.

The finalist defaults now live in `agent_v5.py`: 8 cows, 6 sheep, adaptive
cow-only response to at least 10 visible opposing sheep, six melons, three
animals per livestock worker, three feed days, early land thresholds 3/30,
raw fertilizer sales, $1 sell floor, and melon cutoff day 18. Against cow5 V4
over ten new seeds it averaged **68,309 versus 34,491 and won 10/10**.
Ten-seed finalist self-play averaged **51,049 per side**, range
29,978–70,881. It remains an offline candidate and is not approved for Kaggle
submission.

`podpowiedzi2.txt` contains useful hypotheses that match real telemetry—mixed
cows/sheep, larger crews, feed safety, premium crops and endgame sales—but its
claims about 117 mined top games and fixed 96k/158k recipes are not verified
by files available here. Also, selling wheat cannot lower the milk or wool
price: every product has an independent market inventory. “Premium first” is
useful for the ten-order cap, not as cross-product price manipulation.

Compressed public replays and available agent logs live under
`kaggriculture/online/<episode_id>/`. The `[kaggr-collect]` workflow downloads
every missing public episode rather than only the newest one, so matches that
finish between polling runs are not skipped.

## Advice, scale, and timed-land validation

Runs `33974856409`, `33975880688`, and `33976351405` added **88 full
32-replay profiles** derived from both advice files and from the 100k–120k
opponents' visible staffing, land, crop, livestock, fertilizer, and sale
patterns. Larger economies did not transfer to this planner: eight melons
peaked at 85,413, ten at 81,135, twelve at 75,152, Dmitri staffing at 78,501,
and fertilizer reserves fell as low as 66,504. Sale batching was effectively
a tie (at most +0.2), while global crop-task claiming and reserving fallow
strawberry cells were harmful and were removed.

One controlled change did survive both the broad and interaction sweeps:
buying NE no later than day 8 and SW on day 10. The selected day-8/day-10
profile scored **94,409.0 average and 32/32 wins**, +794 over the 93,615.0
finalist. NE days 6, 7, and 8 tied exactly when SW remained day 10; SW day 9
fell to 89,405 and day 11 to 89,758. Reserve and staffing interactions did not
improve it. Morning-only selling scored 94,409.2, an immaterial two-tenths, so
immediate selling remains selected. This is still an offline candidate and
must not be uploaded without explicit approval.
