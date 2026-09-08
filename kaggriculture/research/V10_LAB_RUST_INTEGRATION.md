# V10 LAB correctness and Rust integration

Date: 2026-09-08.

## Correctness repairs

The three independently reported LAB defects were confirmed and repaired:

1. corpus replay evaluation now uses `info.seed`, with a legacy
   `configuration.seed` fallback; a missing/invalid seed is an error rather than
   invented seed 0;
2. both replay loaders map environment step N to replay row N+1 and reject an
   invalid replay seat;
3. the engine audits historical ERROR/INVALID/TIMEOUT states, terminal status,
   reward shape, finiteness and missing values. Tournament rows preserve errors,
   and every sweep stage now refuses to calculate rankings when any game failed.

The dedicated regression suite includes seed zero, absent seeds, first/last
replay actions, invalid seats, hidden final-turn exceptions, malformed rewards,
and sweep failure gating.

The direct TOP49 workflows used `info.seed` and `step + 1` explicitly, so these
repairs do not invalidate their recorded B21/opening comparisons. Older generic
`run_corpus.py` and `tape:` results require selective revalidation; they must not
be discarded or trusted wholesale.

## Rust source and provenance

The integrated core comes from `arena/01a075fa-riemann` at `99c364e`, whose
new update incorporated the replay cache, mixed-hand contract, config hardening,
and batch audit from `arena/01a07c52-riemann`. Current source/docs were compared
against the latter branch at `20f7a9d`; their simulator code, tests, and tools
match, while the latter carries clearer final validation/source-mapping docs.
Those docs were retained.

Published upstream evidence before repository-native gating:

- 585 bit-exact Python reward comparisons and 22,597 exact states;
- 17/17 Rust debug and 17/17 Rust release tests;
- 32/32 Python protocol/CLI tests;
- 14,000-result deterministic batches across thread counts;
- measured small-batch speedup around 112-222x on a four-logical-CPU runner.

These are simulator measurements, not guarantees for a whole sweep.

## LAB adapter hardening

The imported adapter pattern was extended rather than copied blindly:

- static Python ACTIONS modules are exported once and cached;
- raw `tape:replay[#seat]` is Rust-capable and duplicates the selected recorded
  policy for either physical seat;
- jobs are partitioned by horizon and independent hand semantics;
- static candidate vs raw replay uses `trim_hands_a=true` and
  `trim_hands_b=false`;
- `RUST_TAPE_SAFE=False` forces any reactive module exposing ACTIONS back to
  Python;
- malformed Rust results become error rows;
- a Rust runtime/protocol failure is fatal and never silently causes a large,
  expensive Python rerun;
- temporary exports are cleaned automatically.

`scripts/sweep.py --backend auto|rust|python` controls execution. No agent logic
or Kaggle submission was changed.

## Required gate

Before a large Rust-backed experiment, `scripts/check_rust_lab_parity.py` must
compare exact binary64 rewards between the audited Python LAB and Rust for:

- B21/B20 static jobs;
- seed 0 and ordinary seeds;
- both seats;
- raw TOP49 replay opponents;
- mixed hand semantics.

The integration commit requests this gate in GitHub Actions. Large strategic
sweeps remain blocked until it passes.
