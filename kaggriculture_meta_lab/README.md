# Kaggriculture Meta-Lab

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

Current baseline result (deterministic, re-runs to identical numbers):

```
27W 13L 0T  score 67.5%  95% Wilson 52.0-79.9
mean margin +634  errors 0   seat0 13-7 | seat1 14-6   GATE: PASS
corpus 8W 0L over 8 episodes, candidate mean cash 84.9k vs recorded 26.9k
```

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
