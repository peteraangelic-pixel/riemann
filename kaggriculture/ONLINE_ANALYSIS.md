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

## v3 direction

Build and benchmark a complete subsystem rather than copy one crop:

1. deterministic pasture coordinates and build/place state machine;
2. daily wheat pickup and animal feeding routes;
3. CARE and fertilizer collection scheduling;
4. demand-sensitive cow/sheep counts from visible shops and market prices;
5. sale of milk, wool and fertilizer;
6. premium crops only when labor and cash-flow constraints are met;
7. direct v3-v2 head-to-head and multi-seed tests before another submission.

Compressed public replays and available agent logs live under
`kaggriculture/online/<episode_id>/`. The `[kaggr-collect]` workflow downloads
every missing public episode rather than only the newest one, so matches that
finish between polling runs are not skipped.
