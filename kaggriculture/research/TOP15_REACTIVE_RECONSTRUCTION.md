# TOP15 reactive-policy reconstruction (2026-09-09)

## Corpus identity and validity

`TOP15.7z` is now the primary replay corpus. The fail-closed audit is recorded in
`kaggriculture_meta_lab/results/top15-audit-20260909.json`.

- 15 per-team manifests, ranks 1–15, and exactly 7 selected slots per team;
- 105 distinct replay paths, 94 unique episodes, 94 unique seeds;
- all 210 terminal agent statuses are `DONE` and all selected actions are present;
- every selected `submission_id` belongs to that team's active-submission list;
- one genuine self-play slot has both seats named `ultimatum_game`; seat 0 is selected deterministically;
- one self-play replay explicitly contains integer seed `0`. This is read from `info.seed` and reported as such; there is no missing-seed fallback.

Selected episodes are not assumed to represent the current leaderboard policy.
Only 56/105 slots come from each team's highest-scoring listed active submission.
All policy comparisons below identify and filter by `submission_id` first.

## Backend safeguards

Before running the bounded benchmark, the current tips of both requested peer
branches were inspected:

- `arena/01a075fa-riemann` at `207b861`: its Rust simulator run `34395984842`
  passed, but its current Meta-Lab runs `34395984754` and `34396427082` failed
  in unit tests after reactive-overlay integration.
- `arena/01a07c52-riemann` at `9f54180`: its bounded funnel run `34281049065`
  and the relevant Rust/peer audits passed.

The local path retains the three required protections: replay seed is mandatory,
replay row zero is skipped (`action N` comes from replay row `N+1`), and failed
agent/Rust rows remain errors and make ranking fail closed. Tape source resolution
was additionally changed from eager `dict.setdefault` evaluation to real caching.

## Rust both-seat TOP15 benchmark

Actions run `34398996595` passed Rust tests and completed all 420 games with no
errors. Results:

| Candidate / subset | W-L | Win rate | Mean margin |
|---|---:|---:|---:|
| static Subin, TOP10 all selected | 39-101 | 27.86% | -4,329 |
| G2-83, TOP10 all selected | 38-102 | 27.14% | -3,138 |
| static Subin, TOP10 best-submission only | 14-52 | 21.21% | -8,678 |
| G2-83, TOP10 best-submission only | 14-52 | 21.21% | -6,019 |
| static Subin, TOP15 all selected | 47-163 | 22.38% | -13,423 |
| G2-83, TOP15 all selected | 42-168 | 20.00% | -11,272 |
| static Subin, TOP15 best-submission only | 22-90 | 19.64% | -16,025 |
| G2-83, TOP15 best-submission only | 18-94 | 16.07% | -13,085 |

The two physical seats are balanced for static Subin (23-82 and 24-81 over
TOP15), so seat bias does not explain the result. G2 improves cash margin while
reducing match wins, especially against the strongest active-submission tapes.
This confirms that market clamping is not the missing policy class.

These are open-loop stress tests, not leaderboard reproductions. They establish
that current TOP15 action structures remain much stronger than Subin under the
same simulated market trajectory.

## Policy families in highest-scoring active submissions

Full replay JSON was inspected directly. Counts below are observed ranges across
best-submission episodes, not assumed source constants.

### Otter Vibe (rank 1, 2987.0): broad state-reactive farm planner

Across four matching episodes, every complete action fingerprint differs.

- hires: 272–287 order events;
- land: exactly 2 buys;
- seed order events: 42–51, with total quantities and crop mix changing sharply;
- animal order events: 9–13; observed quantities vary from 3–14 cows, 2–14 sheep,
  and 0–10 geese;
- product buys: only wheat and fertilizer, 28–36 events;
- compact sales: 225–237 events and roughly 1,400–1,900 nominal sold units;
- unit execution also varies substantially (planting, fertilizing, animal care,
  harvesting, and hand movement), so this is not a static unit tape with a market overlay.

The principal reconstruction target is therefore a repeated state feedback loop:
choose crop/animal capacity from current farm and opponent state, maintain working
wheat/fertilizer stock, and sell bounded shed inventory rather than issuing
unlimited liquidation orders.

### SpaTaro (rank 2, 2984.1): inventory/price trader plus adaptive production

Across three matching episodes, all fingerprints differ.

- hires: 274–280;
- land: 2–7 buys, the widest top-policy land response;
- seeds: 109–214 order events;
- animals: 10–16 events, cows/sheep only in the sampled best episodes;
- 315–368 product-buy events across almost every tradable product;
- 286–347 sell events with compact quantities.

SpaTaro is structurally distinct from Otter: it actively buys products that it
also sells and changes land/crop scale aggressively. This suggests price-aware
inventory conversion/arbitrage coupled to production, not merely endgame sales.
It should be reconstructed as a separate family rather than averaged with Otter.

### Compact-sale secondary family

- **binghua (2930.2):** fixed 317 hires and 2 lands, but variable seed quantities,
  7–10 animal events, and only about 1,900–2,000 nominal market units.
- **Mengfei Li (2929.4):** near-static 259–260 hires and 2 lands, stable 12 cows /
  5 sheep, but compact inventory-sized sales around 1,900 units.
- **mtmr_s1 (2916.1):** transitional family. Several episodes repeat a stable
  260-hire/2-land/8-cow/6-sheep/3-goose plan, while others react up to 276 hires,
  3 lands, and altered animal mix. Sales remain compact.

These provide lower-complexity stepping stones for a reactive implementation.

### Overcommitted static family

Himanshu Kumar and many agents from ranks 3–15 repeatedly converge on roughly
260 hires, 2 land buys, 163 wheat seeds plus 31 carrot/33 strawberry/12 melon,
and approximately 8 cows/6 sheep/3 geese. Their nominal sale quantities reach
tens of thousands (for example 89k–123k in sampled Himanshu episodes), relying
on order clamping to actual stock. This family can score near 2900, but it does
not explain why Otter/SpaTaro lead or why their trajectories vary.

## Reconstruction priorities

1. Implement an observation-driven compact planner, beginning with the more
   constrained Otter family: bounded shed sales, wheat/fertilizer working-stock
   targets, adaptive animal capacity, and exactly two default land expansions.
2. Add explicit opponent-animal pressure features and vary cow/sheep/goose targets
   instead of inheriting Subin's fixed 8/6/3 plan.
3. Separate labor demand from a fixed schedule: target a 272–287 Otter-like range
   based on unlocked area, occupied tiles, and remaining day.
4. Make seed orders reflect free crop cells and crop-value/price state. Do not
   reproduce nominal aggregate counts as constants.
5. Treat SpaTaro's cross-product trading and 2–7 land response as a second
   experiment after the compact planner passes parity and controlled holdouts.
6. Gate promotion through both-seat, hard-failure-free Rust screens, then closed-loop
   holdouts. Raw-tape margin alone is diagnostic and is not a submission criterion.
