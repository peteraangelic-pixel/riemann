# Audit of `arena/01a075fa-riemann/kaggriculture_meta_lab`

Reviewed through updated branch commit `d70634412e92d5cf92d52414c0958cc8e31a223b` without switching this session's fixed branch.

## Verdict

The lab is useful and substantially better for large closed-loop experiments than GitHub Actions. It is complementary to, not a replacement for, this branch's open-loop replay benchmark.

## What is sound

- `ProcessPoolExecutor` uses processes rather than threads.
- Jobs pair seeds and run both seats.
- Agent resolution occurs within persistent worker processes.
- Errors become result rows rather than killing the batch.
- Wilson confidence intervals and promotion gates are appropriate for win-rate decisions.
- It supports true callable-vs-callable closed-loop matches and separate open-loop replay-corpus evaluation.
- Windows setup and `run_windows.bat` are straightforward; 16 physical-core workers are a sensible starting point on a Ryzen 5950X with 64 GB RAM.
- Tests cover statistics, loading, tournament mechanics, corpus parsing, and fertilizer behavior.
- The updated `scripts/validate.py` is a useful one-command harness: closed-loop gate plus open-loop corpus, memory-aware worker cap, and tracked UTF-8 JSON/Markdown reports. The updated Windows batch now runs this real validation instead of only smoke opponents.

## Limitations and corrections

- “Hundreds of parallel tests” should mean hundreds of queued games processed by about 16 worker processes, not hundreds of simultaneous Python engines. Start at 12-16 workers and benchmark memory/throughput before trying 24/32.
- Closed-loop quality is limited by the executable opponent pool. Replay tapes are still open-loop even when run through this package.
- The bundled corpus is only a smoke sample and has a team-seat fallback that can select the wrong seat when the configured team is absent; use explicit metadata/team mapping for scientific results.
- The promoted fertilizer agent and the one-command default comparison are based on the old planner `agent_v7.py`, not current V8 Aastik. Its 27-13 result cannot be treated as evidence over our current finalist. Change `--candidate` and `--baseline` before using the harness for current decisions.
- The tracked sample report's open-loop 8-0 compares candidate mean 84.9k with recorded mean 26.9k from an old low-score sample; it is a smoke result, not elite evidence.
- A 40-game Wilson lower bound barely above 50% is promising but weak. Confirm with at least 500 paired games on the PC and a diverse opponent pool.
- Pin the exact engine version used by Kaggle and include version/hash in every report.

## Recommended division of labor

- Local PC: 500-10,000 closed-loop paired games, factorial sweeps, round robins, confidence intervals.
- GitHub Actions: CI, reproducibility, small independent screens, Kaggle API automation, and confirmation of finalists.
- Current replay corpus: realistic open-loop shared-market regression and loss attribution.

## Suggested Windows starting command

Use 16 workers, 250 seeds and both seats (500 games) before increasing parallelism. Monitor RAM and games/second, then compare 12, 16, 20, and 24 workers. Do not assume 32 SMT workers wins.
