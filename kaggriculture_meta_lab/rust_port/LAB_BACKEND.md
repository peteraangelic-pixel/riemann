# Verified tape backend for the Python LAB

This boundary adopts the useful architecture from `arena/01a075fa-riemann`:
run static games in a single Rust/Rayon batch and leave reactive agents in
Python. The native simulator is unchanged. The adapter adds stricter eligibility,
identity, failure and snapshot handling.

## Integration

The existing six-field jobs are preserved:

```python
(seed, candidate_spec, opponent_spec, candidate_seat, episode_steps, tag)
```

From the LAB directory (the directory containing `rust_port/`):

```python
from kaggriculture_lab import tournament
from rust_port.tools.lab_backend import run_auto, run_report

rows = run_auto(jobs, workers=16, python_runner=tournament.run)
report = run_report(jobs, workers=16, python_runner=tournament.run)
print(report.metrics)
```

Use `mode="rust"` with `run_report`, or `run_rust`, to require ALL policies to
be supported before any game executes. `mode="python"` forces Python.
`run_auto(..., prefer_rust=False)` remains a convenience alias for that mode.
An explicit `binary=...`, `timeout=...`, and a filesystem-only `resolver(spec)`
are optional. For short relative specs the caller can pass
`resolver=kaggriculture_lab.agents._resolve_path`; absolute paths need no resolver.

The adapter discovers `kg_sim.exe` on Windows, `kg_sim` on POSIX. A missing
binary in auto mode falls back before parsing agents. It never submits to Kaggle.

## Native eligibility is proven, not guessed

`ACTIONS` alone does not make a Python policy static. `tools/agent_tape.py`:

- reads a bounded source snapshot, **without import, exec or eval**;
- checks complete function ASTs against narrowly audited templates;
- evaluates only literal data, known JSON/zlib/base85 decoding and recognized
  static tape mutations;
- accounts for V7's fixed schedule side and rejects state-dependent CLAMP_SELL;
- compiles V8's single-stream opening switch into data for both seats;
- recognizes frozen B21 and the structural generator's static wrapper;
- infers whether the verified wrapper clips hands, per input agent;
- sends every other policy to the caller's Python runner.

Unrecognized but equivalent source formatting/variable names may cause a safe
Python fallback. This is intentional: false negatives cost time; a false
positive silently changes the policy being evaluated. New templates should be
admitted only after independent action and full-game parity tests.

For your own static data, use an explicitly recognized standalone template:

```python
from rust_port.tools.agent_tape import emit_source
path.write_text(emit_source(two_seat_actions, trim_hands=True), encoding="utf8")
```

Auto-compilation is deliberately narrower than the raw JSON simulator API:
the audited templates require list-shaped actions and integer quantity
arguments. Data that could make a Python wrapper throw instead of emitting an
action is not silently normalized into a successful native game.

This does not execute agents inside Rust, and does not turn a frozen opponent
replay into a reactive policy. `tape:` and `wrap:` LAB specs currently remain on
the Python path rather than guessing their semantics.

## Correctness protections

- Each distinct path is resolved/read once per call; identical source content
  is decoded once. A new call sees edited files, even at the same path/mtime.
- Immutable JSON snapshots use precomputed normalized-operation fingerprints
  as export filenames.
  Two different `main.py` files cannot overwrite each other's tape.
- Native jobs are grouped by **horizon and both hand rules**, not run with the
  first job's settings.
- Hand rules follow A/B through reversed physical seats.
- Identical verified native games (including missing fields versus explicit
  default actions) may reuse results; original tags and opponent
  specs are restored for every request. Python/reactive games are not deduplicated.
- Fallback gets unique opaque correlation tags, then original tags are restored.
  Out-of-order `as_completed` responses and duplicate user tags do not reorder
  or misassociate results. A Python callback must echo the requested tag/seed/
  seat/opponent and treat tag as metadata, not an agent input.
- Incomplete/malformed/non-finite responses fail explicitly. An unexplained
  Rust failure is **not** silently replayed as an entire Python batch.
- Temporary exports are removed, including after a native error.
- Metrics include classification, exports, client I/O and fallback time.
  Native-only time is not presented as full sweep time.

## Python fallback contract

The callback has the signature of `tournament.run(jobs, workers,
progress_every=...)` and returns the standard result dictionaries. The adapter
checks their shape, identity, outcome and finite rewards, but cannot discover a
hidden agent exception if the callback itself falsely reports success.
Apply the earlier `patches/lab-replay-correctness.patch` to the legacy LAB
error/replay handling, or supply an independently validated Python runner.

This file does not replace your tournament statistics, selectors or agent
policies. Generator mutations still need separate routing/market validation;
content deduplication is not proof that a mutation is profitable.
