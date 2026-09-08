# Current TOP30 replay snapshot — 2026-09-08

The immutable source is the repository-root `TOP30.7z`, uploaded by the user in
commit `1ebeefd`. It contains the leaderboard manifest, 30 player folders with
five selected raw Kaggle replays each, the source `analyze_replays.py`, and 180
precomputed `per_replay` reports.

Archive identity:

- bytes: `23,127,528`
- SHA-256: `f6c68c7475128aad850b9462cf89a7948565a254d5eb493e54923b3b5320f592`
- unpacked payload: `4,907,584,893` bytes across 394 archive entries

Extract outside Git (about 4.6 GiB on disk), then reproduce the audit:

```bash
7z x TOP30.7z -o/tmp/top30
python kaggriculture_meta_lab/scripts/audit_top30.py /tmp/top30/TOP30 \
  --archive TOP30.7z \
  --output kaggriculture_meta_lab/corpus/top30_2026-09-08/inventory.json
```

## Integrity result

The independent raw-data audit passed:

- 30 ranks and 30 distinct player folders;
- 150/150 selected replay files present and valid JSON;
- 129 unique episodes/seeds (21 slots intentionally repeat an episode selected
  for another team);
- every replay has 720 two-player steps, an integer `info.seed`, finite final
  rewards, and exact agreement between top-level and final-step rewards/status;
- 300/300 final player statuses are `DONE`; no failed game is admitted;
- repeated copies of the same episode are byte-identical;
- reward range is 41,955–171,211;
- all 180 precomputed report files map one-to-one to the 150 raw replays and 30
  player manifests.

`inventory.json` records every slot's episode, submission, seed, rewards, size,
and SHA-256 so later calculations can prove their input identity.

## Important selection and analysis caveats

The source selection rule chooses the newest episodes across all listed active
submissions, not five episodes from each team's leaderboard-best submission.
Only 72/150 selected slots come from the highest-scoring active submission
listed for that team. Cumulative coverage is 16 slots/9 teams in TOP10, 42/19
in TOP20, and 72/29 in TOP30; `binghua` has no selected replay from its best
listed submission. Therefore calculations must report both:

1. all recent selected records (behavioral recency/robustness), and
2. the best-listed-submission subset (stronger but incomplete elite evidence).

The bundled `per_replay` output is useful for exploratory action counts, but it
is not a scoring oracle. All 150 native replay reports have empty
`final_scores` and no `winner`; the analyzer also processed 30 manifest files as
generic pseudo-replays. Promotion decisions must use the audited raw JSON and
our fail-closed LAB adapters instead.

Use `scripts/benchmark_top30.py` for a bounded baseline. It preserves each raw
seed, selects the named team's recorded seat, and evaluates the candidate in
both physical seats through the parity-gated Rust raw-tape adapter. Its result
labels the test as open-loop replay stress, never as closed-loop leaderboard
reproduction.
