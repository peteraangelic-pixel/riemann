# Rust + rayon port — what to hand the AI coding assistant

## TL;DR recommendation

Do **not** ask Fable (or any AI) to "rewrite Python to Rust" from a single dump.
The simulator is the only part worth porting; the agents are data (tapes) and the
harness is orchestration. Give the assistant the **environment simulator file**
plus this spec, and keep the tournament/statistics layer thin.

## Where the time goes

A closed-loop game runs the `kaggle-environments` Python simulator for 720
steps, advancing BOTH agents and the shared market. Profile shows ~95% of wall
time is inside the simulator's `interpreter()` (`kaggriculture.py`, ~1086 lines
in the installed `kaggle_environments` package). The tournament harness
(processes, aggregation) is <5% and already parallel.

So a Rust port should reimplement **only the simulator** (`kaggriculture.py`),
expose it as a library that drives two agent policies, and call into the agent
tapes (which are just JSON action lists — trivial in Rust via serde_json).

## Expected speedup (honest estimate)

- The "10-20x" intuition is directionally right for the SIMULATOR: CPython
  interpreter overhead on the per-tile step loop is the cost, and a tight Rust
  reimplementation of the board/market state machine is typically 15-40x on
  this kind of grid simulation (no allocation per step, fixed arrays, rayon).
- End-to-end, because two agents also run, realistically **8-20x**. On a
  5950X (16 cores) with rayon that turns a 3-hour 14k-game run into
  **~10-20 minutes**.
- Bigger win for the search: an opening sweep / parameter grid that was
  "hours" becomes "minutes", so hundreds of configs become routine.

## Files to hand to the assistant (in this order)

1. **`kaggriculture.py`** (the simulator) — the entire file. Get it from the
   installed package:
   `python -c "import kaggle_environments,os;print(os.path.dirname(kaggle_environments.__file__))"`
   then `envs/kaggriculture/kaggriculture.py`. This is the core: state
   (`_initialize`, `interpreter`, `_apply_unit_action`, `_process_market`,
   `_town_consume`, `_end_of_day`), market pricing (`market_price`,
   `MARKET_PARAMS`), crops/animals tables.
2. **`kaggriculture.json`** next to it — the environment configuration
   (board size, money, intervals) the simulator reads.
3. **`docs/RUST_PORT_SPEC.md`** (below) — the contract the port must meet.
4. One reference tape agent, e.g. **`agents/current/agent_v9_b21_s16.py`**, so
   the assistant sees the action format (zlib+base85 JSON of per-seat,
   per-step action dicts with keys `farmer`, `hands`, `market`).

Do NOT port the sweep/validate/stats Python first — those stay Python and just
shell out to a fast Rust binary (CLI: given two tape files + seed + seats,
print final rewards JSON). That boundary keeps iteration simple and lets the
Python harness keep Wilson/Bradley-Terry reporting.

## Acceptance contract for the port

- Determinism: identical seed + identical two agent action streams =>
  IDENTICAL final rewards to the Python sim, for all 720 steps. Validate by
  cross-playing 50-100 seeds Python-vs-Rust with the same two tapes and
  asserting rewards match to the dollar (a `--check` mode).
- Parallelism: rayon over `(seed × seats × variant)` job list; each game is
  independent. Use fixed-size arrays for the 10x10 board, no per-step heap
  allocation on the hot path.
- Agents are data: a tape is `Vec<Vec<Action>>` indexed `[seat][step]`.
  Reactive agents (the future) can be a trait object later; tapes first.
- Market state MUST be shared between the two seats in one game (prices move
  with total inventory) — the single most common porting bug.

## On "do you use an ML/AI generation system like in training?"

No — and deliberately. The current generator is an **exhaustive grid over
opening parameters** (buy × reserve), scored by actual game outcomes with a
Wilson gate. That is a black-box, derivative-free optimizer. We do NOT train a
neural policy, because (a) the action space is large and coupled, (b) we can
run the true game cheaply, so policy-gradient/evolution would add noise and
need far more samples than a targeted parameter sweep for the same confidence.

If we later want smarter-than-grid generation, the right step is not an ML
model but **Bayesian optimization / CMA-ES over the tape parameters** (buy,
sell, seed counts, hire counts, animal counts) using the Rust simulator as the
fast objective — that gives sample efficiency far beyond a grid, still with
zero training instability. That is the natural phase 2 once the Rust sim exists.
