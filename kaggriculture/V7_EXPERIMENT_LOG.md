# V7 experiment log

This log records replay-derived facts, hypotheses, tests, and rejected ideas so later sweeps do not lose attribution.

## Established facts

- V6's broad baseline is 88,259.6 over 70 public scripts (64 wins).
- The first 36-way full phased-planner ablation failed: full V7 scored 58,759.9; removing strawberries recovered only 70,646.4.
- A second 36-way forward-selection sweep found no planner phase above the V6-equivalent control (88,229.4). Target counts do not reproduce elite execution.
- Across six Renoir matches, farmer actions match on 720/720 turns and complete hand-action arrays match on 720/720 turns. Full actions differ on only 0–4 market turns.
- Raw automatic-seat reconstruction scores 147,543.1/68W on 70 public scripts, 87,178.3/15W on 24 champion trials, 116,519.3/4W on ten Renoir trials, and 91,689.1/6W on ten `inni.zip` trials.
- Clamping SELL quantities to the pre-action shed is invalid because hands can drop products before market processing in the same turn. It collapses public performance to 60,714.7.
- P0, P1, and automatic raw Renoir schedules tie on all aggregate corpora. Their physical schedules are identical; minor market-order differences do not affect those aggregate results.

## Current hypothesis

Keep Renoir's verified physical schedule fixed. Search only market schedules and late liquidation using demonstrations from Renoir, CoorDi, Jordi Corbilla, Zhongyi Dai, and Jesse Bullard. Evaluate every profile separately on the 70-public, 24-champion, ten-Renoir, and ten-other trial sets.

## Guardrails

- Never combine corpus means into one headline number.
- Candidate score is the first replay score; scripted-opponent score changes with the shared market.
- Preserve raw same-turn SELL orders unless a replacement explicitly models carried inventory and DROP operations.
- Do not upload another Kaggle submission without fresh explicit approval.

## Market stage A results

- Renoir AUTO/P0/P1 raw tied exactly and remain best: public 147,543.1/68, champions 87,178.3/15, Renoir 116,519.3/4, others 91,689.1/6.
- Wholesale CoorDi, Jordi, Zhongyi, or Jesse market schedules collapse to 54-58k public because market purchases are tightly coupled to their slightly different physical schedules.
- Replacing only days 27-29 also regresses every corpus; Renoir's endgame must stay coupled to its earlier inventory flow.
- Global SELL-first ordering raises public wins from 68 to 69 but lowers public mean to 146,293.8, Renoir mean to 103,910.5, champion wins to 13, and other mean to 86,518.0.
- HIRE-first and BUY-first collapse to roughly 70k public. Sequential order is economically meaningful, not cosmetic.

## Next hypothesis

The extra SELL-first win may originate on one particular day, while applying it globally causes the score loss. Stage B changes ordering on each day 0-29 independently (30 ablations plus control/global) before combining only beneficial days.

## Market stage B results

- Day 4 is the strongest 70-public mean result: 147,975.4/69W. It also improves the champion mean to 87,996.3, but lowers Renoir to 112,334.4/6W and others to 87,436.8/6W.
- Day 8 is the best balanced isolated change: public 147,548.4/69W, champions 87,198.0/15W, Renoir 116,724.0/8W, and others unchanged at 91,689.1/6W.
- Days 15, 16, 21, 26, and 27 independently reach 69 public wins with approximately neutral means. Days 16 and 21 also reach 7/10 Renoir wins.
- Days 6, 7, 10, and 22-24 regress and are excluded from combination testing.

## Live V7 evidence (85 public matches collected 2026-09-06)

- Submitted V7 is 59-26, averages 91,365.8 cash against 81,581.1, median 86,702, and ranges from 44,801 to 171,146. Its leaderboard score increased from the earlier 1188.0 snapshot to 2179.9 as more matches completed.
- Top games are 171,146-99,739 against XiweiZhou, 167,694-78,660 against soumic 1088, and 161,710-159,403 against momoon.
- The strongest observed opponent score is 159,403 (momoon). None of our 85 collected matches, nor the supplied champion/Renoir/inni archives, contains a 200k result yet.
- Most runs reach the identical intended physical maxima (8 cows, 9 sheep, 12 melons, 41 wheat, 33 strawberries, 23 carrots), despite a 126k cash range. Shared demand, sale priority, and the opponent's liquidation dominate final-money variance; the physical schedule itself already demonstrates 170k capability.
- Across all 85 games, the sum of requested SELL quantity times the contemporaneous quote correlates 0.890 with final cash. This is diagnostic rather than realized revenue because requested quantities can exceed accepted inventory.
- Premium quotes separate the score tails. In the bottom ten games (53,687.9 mean), mean quotes at our sale turns are milk 43.7, strawberries 61.8, wool 22.5, and melons 167.6. In the top ten (140,748.6 mean), they are milk 190.7, strawberries 204.8, wool 83.7, and melons 182.9. Product-level correlations with final cash are milk 0.726, strawberries 0.614, melons 0.428, fertilizer 0.371, wool 0.206, wheat -0.064, and carrots -0.224.
- The 171,146 game combines exceptional milk (237.9 mean quote at sale turns) and wool (201.6); the 167,694 game combines milk 230.8 and strawberries 244.0; the 161,710 game has milk 193.1, wool 211.6, and strawberries 196.4. There is no single required premium product, but at least two high-price premium channels appear in every 160k+ game.
- Follow-up after Stage C: test price-aware deferral/priority for milk and strawberries while preserving all physical actions. It must be replay-tested because delaying low-price sales can overflow the shed or miss later demand; static quote correlation alone does not establish causality.

## Market stage C design

Test singles, selected pairs, and increasingly broad bundles composed only of days 4, 8, 15, 16, 21, 26, and 27. Report the current 85-match V7 public corpus, champions, Renoir, and others separately. Day 4 remains isolated in most bundles because its larger public gain trades away elite robustness. The public benchmark is explicitly filtered to submission 56044395 so future replay collection cannot silently change the corpus.

## Market stage C results

- On the frozen 85-match live corpus, day 8 is the clear isolated winner: 91,373.7/59W versus control 91,365.8/59W. It also remains 87,198.0/15W champions, 116,724.0/8W Renoir, and 91,689.1/6W others.
- Day 8 plus day 21 is nearly tied on live money (91,373.4/59W), improves Renoir further to 116,745.7/8W, and gives the best useful other-player gain (91,714.9/6W). Day 8+16 reaches 91,372.2/59W live and 116,730.6/8W Renoir.
- The broad non-day-4 bundle [8,15,16,21,26,27] maximizes Renoir at 116,753.1/8W and champions at 87,229.4/15W, but slips to 91,357.3/59W live. Interactions do not justify bundling all individually neutral days.
- Day 4 does not transfer to current matches: 91,337.0/58W live, losing one real win. Adding day 8 gives only 91,344.9/58W. Day 4 and all bundles containing it are rejected despite their 70-replay and champion mean gains.
- Conclusion: retain day 8 as the robust ordering finalist; optionally compare day 8+21 when optimizing cross-corpus robustness. The changes are tiny in final money but the Renoir win gain from 4/10 to 8/10 is repeatable.

## Market stage D hypothesis

Low premium prices are strongly associated with low outcomes. Independently test deferring Renoir SELL orders for one product when its current quote is below a threshold, always releasing by a configured late day. First isolate milk, strawberries, wool, and melon threshold/hold-day pairs; combine only thresholds that improve the frozen live corpus without damaging champion/Renoir/other robustness. Deferral can also starve same-turn purchases or overflow storage, so it is an experiment rather than an assumed improvement.
