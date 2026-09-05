# Kaggriculture online analysis

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

Current sample: 3 wins, 4 losses. V2 produced 23.7k–34.1k, but its
wheat/carrot/melon economy has a low earnings ceiling.

## Pattern separating wins from losses

All three opponents that beat v2 operated a coherent animal/premium economy:

- Team21 peaked at 7 cows, 6 sheep, 27 strawberries and 11 melons; requested
  sales included 187 fertilizer, 115 milk and 95 wool.
- Alejandro Rendon B. peaked at 7 cows, 5 sheep, 17 strawberries and 12
  melons; requested sales included 164 fertilizer, 157 milk and 75 wool.
- foundtion peaked at 6 cows, 7 sheep, 25 strawberries and 12 melons; requested
  sales included 251 fertilizer, 102 milk and 94 wool.
- Suresh Chandra Mangena used a different but related route: up to 13 geese,
  62 strawberries and 20 melons, with requested sales of 103 eggs, 78
  fertilizer and 134 strawberries.

The weaker opponents either failed to service their animal economy or stayed
close to a crop-only baseline. Merely possessing premium crops or structures
was not enough.

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

Five geese, two per worker and three days of feed stock is the selected v3.
It also averaged about 38.2k per side in ten-seed v3 self-play. Future work
can add demand-sensitive cows/sheep and premium crops on top of this validated
logistics subsystem rather than replacing it.

Compressed public replays and available agent logs live under
`kaggriculture/online/<episode_id>/`. The `[kaggr-collect]` workflow downloads
every missing public episode rather than only the newest one, so matches that
finish between polling runs are not skipped.
