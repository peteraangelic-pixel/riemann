# Rust + rayon port — handoff for Fable 5.1

Goal: reimplement ONLY the game simulator in Rust (fast, parallel), expose a
small CLI that replays two agent "tape" files for a given seed and prints final
rewards. Keep everything else (sweep, statistics) in Python — it will shell out
to this binary.

## Files to give Fable (exact list — give these, not a repo dump)

Give these files in THIS folder (`kaggriculture_meta_lab/rust_port/`):

1. **`kaggriculture_sim.py`** (1086 lines) — THE simulator to port. This is the
   authoritative game rules. Key functions:
   - `interpreter(state, env)` — the per-step state machine (main loop).
   - `_initialize`, `_apply_unit_action`, `_process_market`, `_town_consume`,
     `_end_of_day`, `_daily_refresh_plants`, `_daily_refresh_animals`,
     `_spawn_weeds`, `_do_hire`, `_do_buy_land`, `market_price`, `_commit_unit`.
   - Tables: `CROPS`, `ANIMALS`, `MARKET_PARAMS`, `SHOPS`, `LAND_ORDER`,
     `FARMER_MOVES`, `PRODUCTS`, prices (`market_price` with below/above funcs).
2. **`kaggriculture_config.json`** — environment configuration defaults
   (boardSize, startingMoney, sell intervals, stepsPerEpisode).
3. **`agent_v9_b21_s16.example.py`** (copied from
   `agents/current/agent_v9_b21_s16.py`) — shows the ACTION DATA FORMAT: a tape
   is `zlib.decompress(base64.b85decode(...))` -> JSON of
   `[seat][step] = {"farmer": [...], "hands": [[...],...], "market": [[op,item,qty],...]}`.

## What to build (CLI contract)

```
./kg_sim --tape-a <a.json> --tape-b <b.json> --seed <int> --steps 720 [--reverse-seats]
# prints one JSON line: {"rewards":[cash_a, cash_b], "errors":[...]}
```
- Tape JSON on disk: already-decoded `[seat][step]` action lists (Python side
  does the zlib/base85 decode and writes plain JSON, so Rust does NOT need
  base85/zlib for v1).
- Run BOTH seats' actions through the shared state machine for `steps` steps.
- Parallel: a separate `--jobs <file>` mode where each line of a jobs file is
  `seed,tape_a,tape_b,reverse`; use rayon to process them all and print
  `rewards` per line in input order.

## Non-negotiable correctness

- **Bit-exact rewards**: same seed + same two tapes => rewards identical to the
  Python sim to the dollar, all 720 steps. We will verify with a Python
  `--check` cross-run over 50+ seeds.
- **The market is SHARED between the two farms in one game** — prices move on
  TOTAL inventory. This is the #1 porting bug; do not give each seat its own market.
- Deterministic RNG seeded by the episode seed (match numpy/python RNG usage in
  `_end_of_day` shop draws and `_spawn_weeds`; inspect how `resolve_episode_seed`
  and `rng` are created and replicate the exact RNG stream).
- 10x10 board as fixed arrays; no per-step heap allocation on the hot path.

## Performance target

8-20x end-to-end vs the Python sim; 16-core rayon. That turns a 3-hour 14k-game
run into ~10-20 minutes.

## Do NOT port (out of scope)

- The tournament/sweep/statistics layer (stays Python).
- "Reactive" agent policies (the 900-line decision agents) — v1 replays tapes
  only; reactive support comes later as a trait.
