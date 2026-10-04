# Current evaluation policy: newest TOP12 only

Per user direction, new agent development and promotion will use only the
newest TOP12 corpus from `arena/01a08fb2-riemann`.

## Active benchmark

```text
TOP12.7z / newest TOP12 manifests
all current TOP12 tapes
both seats
common fresh seeds
Rust fast runner + slow parity sample
```

## Not used for promotion

```text
old TOP7
old TOP15
old TOP30
old B21/S16 as a ranking corpus
historical V3/V4/V5 H2H alone
```

Older corpora may remain as diagnostic regressions or provenance, but they
cannot decide promotion because they are stale relative to the current live
population.

## Required report

Every V12/V13/V8 candidate report must contain one row per current TOP12 team:

```text
W-L-T
score rate
mean candidate cash
mean material margin
worst margin
errors/timeouts
P0/P1 split
```

A candidate must have zero errors/timeouts and positive aggregate material
margin. It must not lose catastrophically to any single current TOP12 team;
per-team regression floors are retained even when aggregate score improves.

## Development sequence

1. Screen the complete current TOP12.
2. Diagnose losses by observable state: seat, cash, animals, fertilizer,
   market queue, shed headroom and opening day.
3. Evolve only state-gated changes that improve the current TOP12 holdout.
4. Re-run all TOP12 teams on fresh common seeds.
5. Only then consider a live transfer test.

The old TOP15/TOP30 results remain historical context and are not used to
select the next agent.
