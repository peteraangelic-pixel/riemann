# Kaggriculture Meta-Lab

## Current controls and safe workflow (2026-09-07)

The old fertilizer/V7 examples below are retained as experiment history, not as
promotion evidence. Current snapshots live in `agents/current/`:

- `agent_v7_scripted.py`: strongest TOP49 win-count control, 188/490;
- `agent_v8_aastik.py`: immutable V8 control, 140/490;
- `agent_v8_hybrid.py`: immutable 203,785-peak control, 140/490;
- `agent_v9_b21_s16.py`: current candidate, 184/490, mean margin +835.

Use this bounded comparison first:

```powershell
python scripts\validate_current.py --games 50 --workers 16
```

It uses identical seeds and both seats against all three current controls. For a
focused opening sweep, double-click `run_sweep.bat` or run:

```powershell
python scripts\sweep.py --config sweeps\v10_b21_rating_finalists.json --workers 30
```

The first direct B21 run discovered three rating candidates (`b18s13`,
`b19s14`, `b20s15`) at **186W-14L each over 200 fresh promotion games** against
untouched B21, but the old balanced gate rejected them solely because their
mean coin margins were -14 to -21. Kaggle and final Bradley-Terry use W/L/T, not
coin margin, so `promotion_objective="rating"` now applies the Wilson/no-error
gate and reports margin separately. The focused confirmation above projects
exactly 3,000 games and anchors untouched B21 in finals.

Every mutation plays untouched B21/S16 in screen and promotion, and B21 is
forcibly anchored in the finals so noisy top-K selection cannot discard the
champion. `sweep.py` prints the projected
cost and refuses more than 3,000 games unless `--allow-large` is explicitly
passed. The previous `v8_tuning.json` worst case was about **18,240 full
720-step games** (240 screen + 4,000 promotion + 14,000 finals), explaining the
many-hour run and enormous terminal output.

A local closed-loop winner is not automatically promotable. Final promotion
still requires the main repository's exact 245 TOP49 player-tapes, both seats,
plus V7, both V8 controls, public-live regression, crashes, and fresh holdouts.
The TOP49 set is 245 player-policy records from 49 leading players (196 unique
underlying episodes), not 245 weak historical team matches.

> The sections below describe the original lab and contain legacy V7/fertilizer
> numbers. Do not use those old defaults to approve a new submission.

A self-contained, **Windows-friendly local lab** that adds the one piece the
mature V7 work was missing: a high-throughput **closed-loop** evaluator (two real
agents reacting to each other, paired seeds, both seats, Wilson gate), plus the
V7-style **open-loop** replay benchmark packaged and parallelized, a round-robin
**Bradley–Terry/Elo** rater (the same model as the final), and a **fertilizer
probe**. It builds *on top of* the V7 policy (`agents/ref/agent_v7.py`) — it does
not replace it.

## Why this lab exists

The final ranking is a Bradley–Terry model over head-to-head episodes between
active agents. Open-loop replay tapes (V7's strength) reproduce Kaggle results
and test the shared market, but they do **not** react when your agent changes the
state. True win-rate needs a **closed loop**. This lab gives you both:

| Question | Tool | Mode |
|---|---|---|
| Did I break the shared-market schedule? | `run_corpus.py` | open-loop (real elite replays) |
| Does my change actually BEAT another live policy? | `run_tournament.py` | **closed loop** |
| Who is strongest across a pool (Elo/BT)? | `rate.py` | closed loop |
| Does the fertilizer fix beat V7? | `run_tournament.py` vs `agent_v8_fert.py` | closed loop |
| Is a mutation safe to submit? | `--gate` (Wilson CI) | decision rule |

## Setup (Windows / PowerShell)

```powershell
# Python 3.11+; the kaggriculture env IS in kaggle-environments on PyPI (>=1.32.4)
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install kaggle-environments==1.32.7 pandas pytest
```

(or `pip install -r requirements.txt`). No Kaggle credentials are needed for the
closed-loop tools or the bundled sample corpus.

Bundled: `agents/ref/` holds V7, the Renoir tape, V8-fusion and V4 for reference;
`corpus/sample/` ships 8 real elite replays (point `--corpus` at your full
`online/` folder to use all 177+).

## One-command validation (run this after every change)

```powershell
# or just double-click run_windows.bat (sets GAMES=20, WORKERS=8)
python scripts\validate.py --games 20 --workers 16
```

Runs **both** deciding tests in one go and writes a committable, UTF-8 summary
to `results/validate-<timestamp>.md` (+ `.json`):

1. **Closed loop** — V8 vs V7, 20 seeds × 2 seats = 40 games, Wilson gate.
   Exits non-zero unless the 95% Wilson lower bound clears 50%, mean margin is
   positive, and there are zero crashes.
2. **Open loop** — V8 replayed into every recorded elite game in the corpus
   (`corpus/sample`, or point `--corpus ..\kaggriculture\online` at your full
   set); wins/losses and cash delta vs the recorded original.

`results/` **is tracked in git** (unlike the bulky `reports/`), so commit the
new file and push — that is how the team shares verified numbers. Worker count
is auto-clamped to available RAM (~0.45 GB/worker); on a 5950X/64 GB use 16.

Current baseline result (V8 vs V7, user's Ryzen 9 5950X, 2026-09-06;
see `results/validate-windows-5950x-200games.md`):

```
200 closed-loop games (100 seeds x 2 seats):
146W 54L 0T  score 73.0%  95% Wilson 66.5-78.7
mean margin +733  errors 0   seat0 73-27 | seat1 73-27   GATE: PASS
corpus 8W 0L over 8 episodes, candidate mean cash 84.9k vs recorded 26.9k
```

The 40-game run is deterministic and re-runs to identical numbers
(27W 13L, 67.5%); the 200-game run tightens the picture to a solid 73%.

## Parameter sweep: hundreds of configs -> best 10 -> champion

`validate.py` tests ONE agent. `scripts/sweep.py` automates the search over a
whole grid of parameter configurations (the funnel you want for 100s of
configs):

```powershell
python scripts\sweep.py --config sweeps\v8_tuning.json --workers 16
```

It runs three stages, each with a different cost/precision trade-off:

1. **SCREEN** — every generated variant vs V7 on few seeds (8 → 16 games each),
   one parallel job pool. Cheap; rejects garbage. Top `top_k` advance.
2. **PROMOTE** — survivors vs V7 on 250 seeds (500 games each) through the
   Wilson gate. Only configs whose 95% lower bound clears 50% survive.
3. **FINALS** — round-robin among the survivors (every pair, both seats);
   Bradley–Terry strengths name the single best version, plus a pairwise
   win-rate table so you see who beats whom directly.

Configurations are plain JSON in `sweeps/`: an explicit `variants` list and/or a
`grid` (cartesian product of constant values). Variants are generated by
rewriting module-level constants of the base agent into `agents/sweeps/`
(gitignored). Ordinary sweeps add the untouched base as `BASE_*`. For local
champion refinement, set `baseline` equal to `base`, disable
`include_untouched_base`, and enable `finals_include_baseline`: the champion is
then the direct opponent in every screen/promotion game and a forced finals
anchor. Results land in committable `results/sweep-<name>-<timestamp>.md`
(+`.json`).

A full run of `v8_tuning.json` (14 configs, 250-seed gates, 5950X/16 workers) is
~15 minutes. To search hundreds of configs, keep `screen_games` at 6–8 (stage 1
cost is configs × seeds × 2) and let the gates concentrate compute on survivors.

> Small-sample caution: stage-1 and a handful of games only **rank** candidates.
> A variant that looks great in screen/few-game finals (e.g. an 81% pairwise win
> over 8 seeds) must clear the 250-seed gate — the funnel is built so that cheap
> noise never gets promoted.

## Closed-loop tournament (the headline tool)

```powershell
# candidate vs a pool, paired seeds, both seats, all cores
python scripts\run_tournament.py `
  --candidate agents\ref\agent_v7.py `
  --opponent starter=starter `
  --opponent v4=agents\ref\agent_v4.py `
  --games 200 --workers 16 --gate
```

`--gate` exits non-zero unless the pooled score-rate's **95% Wilson lower bound
clears 50%**, mean margin is positive, and there are zero crash games — your
submit/no-submit rule. Use **16 worker processes** on a 5950X (physical cores);
SMT threads rarely help this Python engine.

## Open-loop elite corpus (V7-style, packaged)

```powershell
python scripts\run_corpus.py --candidate agents\ref\agent_v7.py `
  --corpus corpus\sample --team "Lauresowe" --workers 16
# full corpus: --corpus ..\kaggriculture\online   (your 177+ episodes)
```

With the *submitted* agent this reproduces recorded scores; with a candidate it
shows the change against realistic market pressure. `--shard/--shards` splits
work for parallel runs.

## Round-robin rating

```powershell
python scripts\rate.py --agents v7=agents\ref\agent_v7.py `
  --agents v4=agents\ref\agent_v4.py --agents starter=starter `
  --games 60 --workers 16
```

## Variants

Two kinds of experiment:

- **Standalone policy** — `agents/variants/agent_v8_fert.py` is V7 with the
  fertilizer subsystem fixed (applied in-field by the animal hand that collects
  it, never stored in the shed, same crop mix as V7). The lab ran it through the
  closed-loop gate: **67.5% score rate vs pure V7 over 40 games (95% Wilson CI
  52–80), +634 margin, zero crashes** — promoted. See `docs/FINDINGS.md`.
- **Wrapper** — `wrap:<base policy>:<wrapper module>` post-processes a base
  action for quick market-layer probes without touching the verified planner.

Promote a candidate only when `run_tournament.py --gate` passes (Wilson low >
50%, positive margin, no error games) **and** the open-loop corpus does not
regress.

## Experiment loop

```text
edit / new wrapper
  -> run_tournament --gate  (200-500 closed-loop games vs pool)
  -> run_corpus            (open-loop elite, both corpora)
  -> rate.py               (relative strength)
  -> promote ONLY if gate passes AND corpus does not regress
```
