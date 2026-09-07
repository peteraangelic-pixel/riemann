# What the Rust+Rayon port must match to plug into the sweep funnel

These are the exact Python files the funnel uses, copied verbatim so a second
Rust implementation can be built to the same contract and diffed against the
existing port (`../src`, `../tools/rust_client.py`). You only port the
**simulator**; the search / stats stay in Python.

## Files

| File | Role for the port |
|---|---|
| `engine.py` | `play_game(agent0, agent1, seed, steps=720) -> {"rewards":[c0,c1], "statuses":[...], "error":None}`. Uses `kaggle_environments.make("kaggriculture", configuration={"episodeSteps":steps,"seed":seed}, debug=False)`. `debug=False` => illegal actions are silent no-ops; never raise. |
| `agents.py` | `resolve(spec)` turns a spec into a callable. A **tape agent** is a `.py` exposing a 2-seat `ACTIONS` list (`ACTIONS[player][step]`) and `act(obs,cfg)` that replays it, trimming `hands[:len(live_hands)]`. All agents in `agents/current/` (champion + the 3 frozen controls) are tapes. Reactive `def agent(obs,cfg)` policies must keep using the Python engine. |
| `tournament.py` | `build_jobs(candidate, opponents, games, start_seed, swap_seats=True, steps=720, tag)` produces job tuples `(seed, cand_spec, opp_spec, seat, steps, tag)`; `run(jobs, workers)` plays them in parallel and returns rows. **Your batch CLI replaces `run` for tape-vs-tape jobs.** |
| `stats.py` | `aggregate(rows)`, `promotion_gate(agg, min_games, ci_threshold=0.5, max_errors=0, require_positive_margin=...)` (Wilson CI on win rate), `bradley_terry(wins, games, names)`. Consumed unchanged. |
| `sweep.py` | The funnel: screen -> Wilson promote -> Bradley-Terry finals. Already wired with `--backend {auto,rust,python}`; it calls a runner of signature `runner(jobs, workers, progress_every=...) -> rows`. |
| `rust_client.py` | The reference thin client (from the existing port): `Job(seed, tape_a, tape_b, reverse)` and `replay_many(jobs, binary=..., steps=720, step_mode="kaggle", threads=N, trim_hands=True, allow_errors=...) -> [{"rewards":[a,b],"errors":[]}]`. Match this interface. |

## Row contract (what each game must produce)

For every job `(seed, cand, opp, seat, steps, tag)` return:

```
{ "tag", "seed", "seat", "opponent": opp_spec,
  "self_reward": <candidate cash>, "opp_reward": <opponent cash>,
  "margin": self_reward - opp_reward,
  "outcome": "win"|"loss"|"tie"|"error", "error": None|str }
```

## Binary contract (batch mode is where Rayon matters)

- `kg_sim --jobs jobs.csv --steps 720 --step-mode kaggle --threads N --trim-hands`
- `jobs.csv`: rows `seed,tape_a,tape_b,reverse` (header optional). Tape paths
  are relative to the **CSV directory**. Parse each unique tape once, share it
  read-only across threads; per job: own RNG, two farms, ONE shared market.
- Output one JSON line per input job, in **input order** (not completion order).
- `rewards` always in input order (A, B). `reverse=1` only swaps which physical
  seat each tape plays. With seat mapping: `reverse = (job.seat == 1)` and
  tape A = candidate, tape B = opponent, then `rewards[0]` = candidate cash,
  `rewards[1]` = opponent cash for both seats.
- Bad job -> `{"rewards":null,"errors":[...]}`, exit 1 if any job errored;
  never count an errored job as a tie. Identical results for 1..N threads.

## Correctness bar

Byte-identical final f64 rewards vs `engine.play_game` (not "within a dollar"),
for arbitrary 64-bit seeds, self-play and asymmetric tapes, both seat orders.
`episodeSteps=720` => 719 action turns (initial state is state 0). Shared market,
MT19937 parity, silent no-op on illegal orders, tape `hands` trimming. The
existing port's `VALIDATION.md` records the parity methodology to reproduce.
