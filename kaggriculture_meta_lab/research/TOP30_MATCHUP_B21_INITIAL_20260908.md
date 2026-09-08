# B21/S16 kontra TOP30 — replay matchup

Data: 2026-09-08. Candidate: `agents/current/agent_v9_b21_s16.py`.
Source: `TOP30.7z` from branch `arena/01a0712c-riemann`, commit `1ebeefd`.
The test used original replay seeds, original seat, and five replay episodes per
team. The opponent was the recorded action stream from the replay.

## Full result

B21 scored **150-0 across 150 replay games**, with no errors.
The per-team average margin ranged from +43,575 to +74,236:

| Team | W-L | Mean margin | Minimum margin |
|---|---:|---:|---:|
| Subramanya N | 5-0 | +43,575 | +22,639 |
| 自己找差距 | 5-0 | +43,595 | +27,270 |
| SpaTaro | 5-0 | +44,185 | +24,596 |
| carbonapi | 5-0 | +44,525 | +29,703 |
| Follow Me Gradient | 5-0 | +44,949 | +15,481 |
| mandgeee | 5-0 | +45,638 | +38,149 |
| kwa | 5-0 | +46,065 | +35,099 |
| Suliman Tadros | 5-0 | +46,356 | +27,594 |
| THUNDER THUNDER | 5-0 | +48,336 | +38,466 |
| Subin An | 5-0 | +50,696 | +19,763 |
| Mengfei Li | 5-0 | +51,081 | +35,399 |
| mtmr_s1 | 5-0 | +54,364 | +20,063 |
| bharat | 5-0 | +54,596 | +27,222 |
| JustinLee | 5-0 | +55,235 | +28,852 |
| Jun_value | 5-0 | +57,169 | +41,543 |
| Agent 0 | 5-0 | +57,284 | +13,260 |
| Ad Space Available | 5-0 | +58,076 | +28,277 |
| binghua | 5-0 | +58,141 | +37,373 |
| track | 5-0 | +59,553 | +36,024 |
| AI是我的豆包 | 5-0 | +61,294 | +29,763 |
| Pramit Das | 5-0 | +61,327 | +35,356 |
| Matthew Huang | 5-0 | +61,857 | +35,987 |
| peikopon | 5-0 | +64,698 | +40,406 |
| Gleb Tumanov | 5-0 | +66,493 | +49,877 |
| Syed Asad Ali | 5-0 | +68,621 | +29,093 |
| Otter Vibe | 5-0 | +71,894 | +50,336 |
| John Doge | 5-0 | +73,086 | +36,356 |
| Tarang222 | 5-0 | +73,657 | +36,679 |
| jasonstillchasin | 5-0 | +73,831 | +22,522 |
| by | 5-0 | +74,236 | +47,491 |

## Critical interpretation

This is not evidence that B21 would achieve a 150-0 closed-loop result against
these submissions. It is an **open-loop replay diagnostic**: the recorded TOP30
agent does not react to the fact that B21 changed prices, inventories and market
availability. A large margin can therefore mean that B21 disrupts the recorded
trajectory, not that B21 has a universal strategic advantage.

The result is nevertheless useful: no recorded TOP30 trajectory remains a
credible fixed tape that beats B21. The likely source of TOP30 strength is
conditional response to the current state, not a static action schedule.

The lowest margins are the best targets for reconstruction because they are
closest to a robust challenge: Agent 0 (+13,260 minimum), Follow Me Gradient
(+15,481), Subin An (+19,763), mtmr_s1 (+20,063), jasonstillchasin (+22,522),
Subramanya N (+22,639), SpaTaro (+24,596), and 自己找差距 (+27,270).

## Next experiment

1. Compare state traces at 10–24 step intervals and locate the first material
   divergence, not just the final margin.
2. Reconstruct closed-loop representatives of delayed-sale, high-turnover and
   intermediate-sale families.
3. Prioritize the eight minimum-margin profiles above for reconstruction.
4. Run reconstructed policies against B21, v12 and a fresh holdout.
5. Keep the recorded-tape result separate from closed-loop promotion evidence.

Reproduction tool:

```bash
python scripts/top30_matchup.py /path/to/extracted/TOP30 \
  --team SpaTaro --team "Otter Vibe" --team binghua
```
