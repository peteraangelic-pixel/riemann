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
| 105792708 | 0 | loss | 27,289 | Sai_Dattu | 37,361 |
| 105793659 | 0 | loss | 27,811 | Rudransh Singh Rathore | 69,255 |
| 105794581 | 0 | loss | 26,210 | Pavel Filin | 47,897 |
| 105795574 | 1 | win | 29,266 | Ivan Zagorulko | 12,697 |
| 105796497 | 1 | win | 28,864 | Teja Pattem | 16,215 |
| 105797403 | 0 | loss | 29,163 | phoenix_merk | 66,240 |
| 105798313 | 1 | loss | 26,546 | dauriel | 70,730 |
| 105799286 | 0 | win | 30,663 | Shrey Modi | 17,222 |

Complete v2 sample at the snapshot: 6 wins, 9 losses. V2 averaged 27,607;
opponents averaged 45,680. Our output stayed narrow while opponent strength
varied widely, confirming that the wheat/carrot/melon economy is reliable but
has a low earnings ceiling.

## Pattern separating wins from losses

The 15-match sample separates strong and weak opponents quantitatively:

| Matches | Opponent avg | Peak animals avg | Peak strawberries avg | Peak melons avg |
|---|---:|---:|---:|---:|
| Our 6 wins | 15,944 | 4.5 | 6.2 | 7.8 |
| Our 9 losses | 65,503 | 15.1 | 22.1 | 13.1 |

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

Five geese, two per worker and three days of feed stock is the selected v3.
It also averaged about 38.2k per side in ten-seed v3 self-play. Future work
can add demand-sensitive cows/sheep and premium crops on top of this validated
logistics subsystem rather than replacing it.

Compressed public replays and available agent logs live under
`kaggriculture/online/<episode_id>/`. The `[kaggr-collect]` workflow downloads
every missing public episode rather than only the newest one, so matches that
finish between polling runs are not skipped.
