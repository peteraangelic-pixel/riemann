# Frozen LAB opponents (seat 087c0)

Static tape agents used as regression controls in H2H LAB runs
(`fast_h2h.py` locally, `rust_h2h.py` in Actions). All files are
bitwise-frozen copies of the exact modules used in the v2/v3/v4
validation campaigns (previously ephemeral under `/tmp/opp` and
`/tmp/top7/agents`); committing them makes CI batches reproducible.

- `raw_b21.py`, `raw_subin.py` — raw recorded tapes of the B21 and Subin
  strategies (V7-family, two-seat).
- `*_t7.py` — TOP7 best-submission tapes, one per team
  (binghua, dewangshu, himanshu_kumar, kanno, otter_vibe, spataro,
  yusuke_hayashi), single-stream mirrored to both seats by the loader.

Reactive agents (G2/G4 overlays) are NOT valid inputs for the static
runners; they stay in the slow framework harness (`h2h_tape_runner.py`).
Do not modify these files: if a control needs to change, add a new file
and note the reason here.
