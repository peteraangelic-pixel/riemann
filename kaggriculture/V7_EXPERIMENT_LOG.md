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
