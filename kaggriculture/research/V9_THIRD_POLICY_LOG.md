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
## Stage O — exact opening-boundary attribution

Actions run `34054841810` tested 12 isolated delayed28-01 → Aastik transfers:
market-only and full-action prefixes ending after steps 1, 2, 3, 5, 8, and 16.
Every variant scored **0/8** on the common-loss set. Market-only variants fell
to roughly 0–20k mean cash; full-prefix variants to roughly 0–28k. Replacing
only step 0 could even produce zero reward because delayed28 buys seven hands
and a different estate while the resumed Aastik logistics assume its original
five-hand/wheat opening.

This is decisive negative attribution: the four rescues are not carried by a
small opening primitive. The delayed28 economy is tightly coupled across its
full trajectory. Do not run these boundary variants on broader corpora and do
not fuse the opening into Aastik.

- Do not extract delayed28-01's opening into Aastik; Stage O rejected it.
- Continue contrastive feature analysis of the four rescued versus four
  unrescued common losses, but any selector must acknowledge that the policies
  diverge at step 0 before opponent style is observable.

## Stage P — episode-level TOP49 failure contrast

Run `34086722994` retained paired outcomes for 245 player-tapes (490 games per
agent). Aastik and the Renoir-opening hybrid both won 64 tapes, only Aastik won
10, only hybrid won 10, and both lost 161. Thus the hybrid opening changes only
a small boundary of outcomes and does not solve the dominant loss family.

Among strict zero-win tapes, Aastik had 171 losses: 16 near losses with mean
margin in (-1000, 0), 42 severe losses below -10k, 39 low-output failures below
60k, and 34 high-output failures above 100k. These are distinct mechanisms:
market-regime collapse, close-game conversion, and insufficient production
ceiling. Treating them as one opening problem is invalid.

The V7-versus-B11/S07 contrast was also complementary: V7 won 35 tapes that
B11/S07 did not, while B11/S07 won 24 that V7 did not. Opponents on B11-only
wins emitted much heavier early wheat churn (through step 5: mean buys 33.9 and
sells 29.1) than opponents on V7-only wins (buys 13.0, sells 8.4). This explains
why one fixed opening cannot dominate every market regime, but it is an
association from replay-emitted actions rather than a causal selector available
at step 0. Full details are in `V9_CONTRAST_REPORT.md` and `V9_CONTRAST.json`.

## Stage Q — V7-based V9 opening isolation

Run `34088298486` screened 21 isolated V7 wheat openings on one latest tape per
TOP49 player, both seats. Frozen V7 B30/S25 scored 33/98 with mean margin -1612.
B21/S16 and B13/S08 each improved to 35/98; B21/S16 also improved mean score to
90,192 and margin to +1,517.

Run `34089748376` then tested the three finalists on all five tapes per player:

| candidate | wins/490 | mean cash | mean margin |
|---|---:|---:|---:|
| B21/S16 | **184** | **89,115** | **+835** |
| B13/S08 | **184** | 88,404 | -1,112 |
| B25/S20 | 182 | 88,717 | -74 |
| frozen V7 control | **188** | 88,409 | -901 |
| frozen V8 Aastik | 140 | 86,591 | -1,996 |

B21/S16 is economically stronger than V7 and far stronger than V8 on this set,
but remains four wins behind V7. It therefore fails the agreed promotion and
submission gate. No Kaggle upload is authorized by this result.

The first grid run `34088033922` was red because generated candidates exposed
`agent` but not `act`, while the screen loader eagerly evaluated `m.act` as a
default argument. No simulations from that run were accepted. The entrypoint
and loader were fixed; `34088298486` is the clean successful rerun.
