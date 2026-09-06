# Audit of `arena/01a075fa-riemann/kaggriculture_meta_lab`

Reviewed through updated branch commit `e4198e020d67259da2e43b3ff3925d441c3f29f7` without switching this session's fixed branch.

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
- The newer `scripts/sweep.py` implements the right broad funnel: cheap same-seed/both-seat screening, a fresh seed range for promotion, Wilson gating, then a third fresh seed range and Bradley–Terry round robin. Explicit variants plus Cartesian grids and an untouched base control are useful mechanics.
- The adaptive-animal experiment is correctly retained as a negative result: expanding to 7-8 sheep hurt, while conservative adaptation was at best neutral relative to its V8-fertilizer control.

## Limitations and corrections

- “Hundreds of parallel tests” should mean hundreds of queued games processed by about 16 worker processes, not hundreds of simultaneous Python engines. Start at 12-16 workers and benchmark memory/throughput before trying 24/32.
- Closed-loop quality is limited by the executable opponent pool. Replay tapes are still open-loop even when run through this package.
- The bundled corpus is only a smoke sample and has a team-seat fallback that can select the wrong seat when the configured team is absent; use explicit metadata/team mapping for scientific results.
- The promoted fertilizer agent and the one-command default comparison are based on the old planner `agent_v7.py`, not current V8 Aastik. Its 27-13 result cannot be treated as evidence over our current finalist. Change `--candidate` and `--baseline` before using the harness for current decisions.
- The tracked sample report's open-loop 8-0 compares candidate mean 84.9k with recorded mean 26.9k from an old low-score sample; it is a smoke result, not elite evidence.
- The later 200- and 1,000-game reports tighten the fertilizer-vs-old-V7 estimate, but more repetitions cannot repair the stale comparator. They still do not compare against current Aastik or the newly reconstructed TOP49 families.
- The supplied `v8_tuning.json` and `v9_adapt.json` still optimize fertilizer/adaptive variants against old planner V7. A PASS or sweep winner is not a current promotion. Repoint `base`, `baseline`, and the finalist pool before using results for V9 decisions.
- `sweep.py` does not enforce the README's open-loop regression requirement; it only writes closed-loop screen/promote/finals results. Run corpus and fresh holdout gates separately.
- Top-K selection is handled reasonably with fresh seed ranges, but the finals can omit the true current control unless it is explicitly included as a variant. Always include frozen Aastik and hybrid controls.
- A 40-game Wilson lower bound barely above 50% is promising but weak. Confirm with at least 500 paired games on the PC and a diverse executable opponent pool.
- Pin the exact engine version used by Kaggle and include version/hash in every report.

## Performance assessment

The current runner already uses worker **processes**, so it bypasses Python's GIL. On a 5950X, `--workers 16` intentionally uses all 16 physical cores while appearing as half of the 32 logical threads. Test 12/16/20/24 empirically; SMT may help slightly or hurt through memory pressure.

Rust + Rayon around the existing Python simulator would not produce a major speedup because the sequential environment remains Python. A large gain requires porting/batching the simulator itself and validating exact parity, which is a separate high-risk project. Before that, improve Python throughput by keeping pools alive across sweep stages, chunking jobs instead of submitting one future per game, reducing repeated imports/serialization, and recording games/second for each worker count.

## Recommended division of labor

- Local PC: 500-10,000 closed-loop paired games, factorial sweeps, round robins, confidence intervals.
- GitHub Actions: CI, reproducibility, small independent screens, Kaggle API automation, and confirmation of finalists.
- Current replay corpus: realistic open-loop shared-market regression and loss attribution.

## Suggested Windows starting command

Use 16 workers, 250 seeds and both seats (500 games) before increasing parallelism. Monitor RAM and games/second, then compare 12, 16, 20, and 24 workers. Do not assume 32 SMT workers wins.
