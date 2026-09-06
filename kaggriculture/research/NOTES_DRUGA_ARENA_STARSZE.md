# Valuable findings from `druga arena starsze wyniki.txt`

## Durable engineering lessons

- Distinguish open-loop tape benchmarks from closed-loop executable-agent tournaments. Tape opponents preserve realistic actions and shared-market pressure but cannot react to changed state.
- Use process parallelism, resolve/cache agents once per worker, pair the same seed across both seats, preserve errors as rows, and report Wilson intervals plus mean/median/p10 margins.
- A promotion gate should require a confidence-bound win-rate advantage, positive margin, zero crashes, and no regression on frozen replay holdouts.
- Fingerprints must include farmer, hands, market actions, economy mix, hiring/land timing, and cash trajectory. A farmer-only fingerprint cannot distinguish strong tapes.
- Pin the simulator version. The transcript corrected its own earlier error: Kaggriculture exists in PyPI `kaggle-environments` 1.32.4 and 1.32.7.
- Do not measure strength against starter/pass/random and infer top-level quality. These are smoke tests only.

## Data-source corrections

- The initially suggested `nnmax/kaggriculture-top10-replay-archive` slug was wrong.
- Verified sources discussed later are the official daily index/dumps and the public archive now exposed as `ashok205/kaggriculture-top10-replay-archive`.
- Replay archives do not provide private executable bot code. Closed-loop top-agent testing needs genuinely public `.py` agents; otherwise the test is open-loop.

## Applicability to this repository

Much of the proposed lab already existed here: replay collection, tape reconstruction, replay benchmarking, market sweeps, loss attribution, and a persistent experiment log. The genuinely useful additions are the closed-loop paired-seed tournament, Wilson gate, process scheduling, and richer fingerprinting.

## Obsolete advice

Early discussion assessed V2 at 25-29k and recommended adding animals/premium crops. Current V7/V8 already has those economies and 85 public V7 matches, so those recommendations are historical rather than new experiments.
