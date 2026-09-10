# Peer artifacts from `arena/01a0712c-riemann` (verbatim copies)

Used as donors/controls for the V5 evolution. Method credit: day-crossover
and market-block genetic search were invented on that branch; the hybrid
below already contains our V4 as a parent.

- `v3_market_genetic_holdout_winner.py` — their Kanno market-timing
  evolution winner (V3 units, 30 evolved market steps; 484-28 vs V3 on
  their independent gate). From `kaggriculture_meta_lab/agents/candidates/`
  at 0712c commit `d855f6ab` (still present at `d969c683`).
- `ours_peer_v4_hybrid_holdout_winner.py` — joint hybrid: their market
  parent x our V4 (`5842819c`); German units days 0-4, Kanno from day 5,
  70/39/11 market blocks (theirs/V4/V3). Independent gate 10240 games:
  481-31 (+350/g) vs our V4. From the same directory at `e9190b86`.
- `peer_v4_german9_kanno_v3.py` — their reconstruction of our V4,
  verified 719/719 identical (our check: 2-2-4 ties, margin 0.0).

Do not modify: re-fetch from the source branch if an update is needed.
