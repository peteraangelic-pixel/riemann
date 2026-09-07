# V10 B21 seat-specific B20/S15 — TOP49

| Agent | Wins / 490 | Mean score | Mean opponent | Mean margin |
|---|---:|---:|---:|---:|
| control_b21s16 | 184 | 89,115 | 88,280 | +835 |
| p1_b20s15 | 184 | 88,968 | 88,233 | +735 |
| p0_b20s15 | 184 | 88,957 | 88,230 | +728 |
| both_b20s15 | 184 | 88,811 | 88,183 | +628 |

Same 245 player-tape records and both seats. Full rows retained for seat/loss attribution.

All four policies won on exactly the same records; neither one-seat change
recovered a loss. Relative to B21, each one-seat policy improved margin on 155
records, was identical on 77, and declined on 13. Only three `ymg_aq` records
had material regressions (approximately -8k to -19k); most other negative
deltas were two coins or less. This makes B20/S15 a plausible *conditional*
component, but rejects both P0-only and P1-only unconditional promotion. Any
condition must use observable market state and fall back exactly to B21.
