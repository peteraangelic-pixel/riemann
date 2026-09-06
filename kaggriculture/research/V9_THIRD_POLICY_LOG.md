# V9 third-policy reconstruction log

## Stage M — ten full-policy reconstructions

Five standalone 720-action candidates were reconstructed from `我都先道歉` and
five from SJY321. Frozen V8 files were not modified. Actions run `34053122465`
screened each candidate against four selected TOP49 tape families, five episode
seeds mirrored across both seats (40 games per candidate).

| Candidate | Wins/40 | Mean cash | Mean margin |
|---|---:|---:|---:|
| delayed28-03 | **31** | 88,084 | **+10,379** |
| delayed28-01 | 27 | **91,992** | +6,242 |
| delayed28-02 | 23 | 78,245 | +1,477 |
| delayed28-05 | 20 | 79,281 | +201 |
| delayed28-04 | 17 | 90,290 | +1,345 |
| SJY321-01 | 11 | 81,583 | -7,286 |
| SJY321-02 | 11 | 79,946 | -14,081 |
| SJY321-03 | 7 | 78,674 | -13,161 |
| SJY321-05 | 7 | 73,058 | -14,390 |
| SJY321-04 | 2 | 59,660 | -37,708 |

The direct SJY trajectories do not transfer robustly. The delayed-sale family
does, but this selected-family screen is only a discovery funnel.

## Stage N — broad replay validation

Actions run `34053468737` compared the top three delayed-sale reconstructions
with both frozen V8 controls.

### Current V8 online corpus (170 episodes)

| Agent | Wins | Win rate | Mean cash | Mean margin |
|---|---:|---:|---:|---:|
| V8 Aastik | **130** | **76.5%** | 88,670 | **+7,005** |
| V8 hybrid | 125 | 73.5% | 87,968 | +5,532 |
| delayed28-01 | 78 | 45.9% | **91,347** | -510 |
| delayed28-02 | 82 | 48.2% | 78,993 | -1,799 |
| delayed28-03 | 48 | 28.2% | 82,845 | -12,258 |

### Scripted-V7 public corpus (112 episodes)

| Agent | Wins | Win rate | Mean cash | Mean margin |
|---|---:|---:|---:|---:|
| V8 Aastik | **93** | **83.0%** | 86,391 | **+9,040** |
| V8 hybrid | 89 | 79.5% | 86,554 | +8,422 |
| delayed28-01 | 50 | 44.6% | **91,742** | +593 |
| delayed28-02 | 47 | 42.0% | 76,606 | -1,716 |
| delayed28-03 | 28 | 25.0% | 80,878 | -13,287 |

### Eight prior Aastik/Renoir common losses

| Agent | Wins/8 | Mean cash | Mean margin |
|---|---:|---:|---:|
| V8 Aastik | 0 | 79,049 | -7,877 |
| V8 hybrid | 0 | 79,035 | -7,888 |
| delayed28-01 | **4** | **91,453** | -5,648 |
| delayed28-02 | 1 | 64,656 | -16,765 |
| delayed28-03 | 1 | 63,146 | -31,402 |

`delayed28-03` was the Stage-M winner and then collapsed on both broad corpora:
a clear selected-TOP49 overfit. `delayed28-01` is the only strategically useful
reconstruction: it rescues four formerly universal losses
(105990797, 105992649, 106027867, 106037741) and raises mean cash, but its broad
win rate is far below Aastik. It is a complementary policy source, not a new
main agent.

## Decision

- Reject all SJY full-tape candidates as standalone transfers.
- Reject delayed28-02/03 as promotion candidates.
- Retain delayed28-01 only for primitive extraction and selector research.
- Keep V8 Aastik as the rating-first baseline; no submission.
- Next isolate delayed28-01's no-wheat/early-estate opening at exact boundaries,
  then test whether a small module can retain its four common-loss rescues
  without sacrificing Aastik's broad win rate.
