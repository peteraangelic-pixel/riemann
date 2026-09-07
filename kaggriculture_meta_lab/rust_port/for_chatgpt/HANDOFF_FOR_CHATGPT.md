# Handoff: build (or audit) a Rust + Rayon port of the Kaggriculture simulator

You are helping port **only the game simulator** of the Kaggle competition
*Kaggriculture* (package `kaggle-environments==1.32.7`) to fast, parallel Rust.
The agent search / sweep / statistics stay in Python. This file is the full
contract; you should be able to work from this folder alone.

## The 4 files in this folder

| File | What it is |
|---|---|
| `kaggriculture_sim.py` | The **official, byte-exact** simulator from `kaggle-environments` 1.32.7. SHA-256 `bc8a5487…cee653e`. This is the source of truth — port behaviour, do **not** "improve" the rules. |
| `kaggriculture_config.json` | The official environment spec (entities, prices, decays, etc.). SHA-256 `a82c89c1…b6f4867`. |
| `agent_v9_b21_s16.py` | Our current **champion tape agent**. It is pure data: top-level constants `BUY_WHEAT=21`, `SELL_WHEAT=16` and a compressed `ACTIONS` blob (`[seat][step]` action lists, 720 steps × 2 seats). `act()` just replays the precomputed action for the current step. |
| `HANDOFF_FOR_CHATGPT.md` | This file. |

> A complete, already-validated reference Rust port exists in the parent
> folder (`../src/`, `../tests/`, `../tools/`, validated in `../VALIDATION.md`:
> 574 matches and 14 674 per-turn states byte-identical, ~80× faster in batch).
> You may use it as a cross-check / merge source, but produce your own clean
> implementation; we will diff the two and keep the best of each. Do **not**
> assume it is correct — re-derive parity from `kaggriculture_sim.py`.

## What "a game" is (from the Python harness)

Two farmers play on one **shared market** for `episodeSteps = 720` states.
Each agent emits an action dict per turn:

```json
{ "farmer": ["PASS" | ...], "hands": [ ...PLANT orders... ],
  "market": [ ["BUY_PRODUCT","WHEAT",n], ["SELL","WHEAT",n],
              ["BUY_SEED","WHEAT",k], ["HIRE"],
              ["BUY_ANIMAL","COW",2], ... ] }
```

- `env.run([a0, a1])` with `debug=False` → **illegal actions are silent no-ops**
  (exactly like the competition server). Never raise from the sim; a bad agent
  action just does nothing.
- Rewards are final cash for each seat: `rewards = [cash0, cash1]`.
- **`episodeSteps=720` produces 720 saved states but only 719 action turns**
  (the initial state is already state 0). Match the framework exactly; support
  an explicit "turns" mode too.
- Seeds are passed via `configuration={"episodeSteps":720,"seed":<int>}` and are
  used to seed the RNG (MT19937). Parity must hold for arbitrary 64-bit seeds,
  including `0`, `-1`, `2**32`, `-2**63`, `2**63-1`.

## Hard correctness requirements (these are where ports usually break)

1. **Deterministic RNG parity.** The Python sim uses `random.Random(seed)`
   (MT19937). Reproduce the *exact* stream, including `random()` vs `choice()`
   call ordering. Validate against MT19937 reference vectors (the existing port
   fingerprints 120 000 random words and 270 009 prices).
2. **One shared market across both seats**, not a per-seat market. Orders from
   both farmers clear against the same price book in the same order.
3. **Order semantics / no-ops.** Unknown/illegal orders are no-ops; malformed
   order slots are *not* removed (removing them changes market pairing).
4. **Tape trimming.** The tape agent replays `hands[:len(live_hands)]`
   (`--trim-hands`). Without trimming, even PLANT orders for nonexistent
   helpers still count toward seed demand — that is the true interpreter
   behaviour; replicate both modes.
5. **Floating point:** cash is IEEE-754 binary64. Parity means the *bytes* of
   the final f64 rewards match, not "within a dollar".
6. **After the tape ends, the last action repeats**; to do nothing append `{}`.

## Required CLI / batch contract (the Python side already calls this)

Single game:

```
kg_sim --tape-a a.json --tape-b b.json --seed 0 --steps 720 [--reverse-seats] [--trim-hands]
→ stdout one line: {"rewards":[cashA,cashB],"errors":[]}
```

Batch (this is where Rayon matters) — a `jobs.csv` (no header, or header ok):

```
seed,tape_a,tape_b,reverse
0,path/a.json,path/b.json,0
1,path/a.json,path/b.json,1
```

- Tape paths are relative to the **CSV file's directory**.
- Parse each unique tape **once**, share it read-only (`Arc`) across jobs;
  each job gets its own RNG, two farms and one shared market. No global lock.
- Emit one JSON result line per input job **in input order** (not completion
  order). `rewards` are always in input order (A, B); `--reverse-seats` only
  swaps which physical seat each tape plays.
- A bad job → `{"rewards":null,"errors":["..."]}` on its line; good jobs still
  run; exit code 1 if any job errored. Do **not** count an errored job as a tie.
- Thread count via `--threads N` or `RAYON_NUM_THREADS`. Results must be
  identical from 1..N threads.

Tape JSON format (two non-empty lists `[seat][step]`):

```json
[ [ {"farmer":["PASS"],"hands":[],"market":[["BUY_SEED","WHEAT",2]]}, ... ],
  [ {"farmer":["PASS"],"hands":[],"market":[]}, ... ] ]
```

## Performance target

~80× over the CPython interpreter on a many-core box (Ryzen 9 5950X / 16 cores)
in batch mode; zero per-turn allocations on the hot path is the bar the
existing port set (fixed-array state, reuse hand buffers).

## How we will validate your port

- Byte-compare final `rewards` for hundreds of seeds (self-play, passive
  opponent, seat swap, asymmetric tapes), then full per-turn state snapshots.
- Run the same batch under 1, 2, 4, 16 threads and require identical output.
- Cross-check against the real Kaggle framework `Environment.run` with the
  supplied wrapper agent.
- `cargo fmt` clean, `cargo clippy -- -D warnings` clean, release build.

## Python integration target (for context — you don't write this)

`../tools/rust_client.py` calls the binary (`replay` / `replay_many`). The sweep
funnel (`../../scripts/sweep.py`, `../../kaggriculture_lab/{tournament,engine,
agents,stats}.py`) builds jobs as
`(seed, candidate_spec, opponent_spec, seat, steps, tag)` and needs, per game:
`self_reward`, `opp_reward`, `margin = self-opp`, `outcome ∈ win/loss/tie`,
and an `error` flag. All agents in `../../agents/current/` are tape agents
(including the three frozen controls), so pure-tape simulation covers the whole
promotion ladder; reactive `def agent(obs,cfg)` policies must fall back to the
Python engine.
