# V8 fertilizer router LAB — 2026-09-10

## Source review

Re-audited `arena/01a087c0-riemann` through `1ebc219`. The branch completed the final old-population holdout and correctly rejected the unconditional step-153 fertilizer pulse:

- old representative population: V7 2191–113 versus pulse 2189–115;
- complete external 105-policy result already shared from this branch: V7 2387–133 versus pulse 2379–141;
- its new router foundation added a default-disabled Rust pulse at a configurable step with quantity, opponent-money bounds, fertilizer-market bounds, and own-fertilizer minimum.

Both branch CI runs at `1ebc219` failed only because the new unit test was not rustfmt-clean. Generic Rust compilation, Clippy, debug/release tests, differential tests and the pulse unit test itself passed. The exact rustfmt patch was recovered from the check annotation.

## Imported mechanism

The pulse primitive was integrated with our existing turn-1 selector rather than replacing `overlay.rs`. Formatting was corrected before launch. Our generic Rust run `34508799142` passed all 23 unit tests, Clippy, adapters, differential validation, benchmark and tracked-format enforcement.

The mechanism is fail-closed:

- default `pulse_turn = -1` and quantity zero preserve exact V7;
- every enabled bound must match;
- an unmatched condition leaves the source action unchanged;
- normal sale budgets cap the appended order to actually available fertilizer.

## Evolution

Run `34509428727` searched a depth-two rectangle over:

- opponent money: ignored / below / above plus threshold;
- fertilizer market inventory: ignored / below / above plus threshold;
- pulse quantity 1–8;
- V7 identity injected into every generation and holdout;
- all 105 TOP15 policies, both physical seats;
- per-team regression floor before total wins, lower-tail margin, mean margin and reward.

Total: **766,080 Rust games**.

The apparent holdout winner was `[0,500,0,10062,2]`. Both modes are zero, so both thresholds are ignored: evolution selected an **unconditional quantity-2 pulse**, not a genuinely conditional router.

Holdout seeds 141000–141011, 2,520 games each:

| Candidate | W–L | Score | Own reward | Margin | q10 margin | Worst team |
|---|---:|---:|---:|---:|---:|---:|
| quantity-2 pulse | 2394–126 | 0.95000 | 108,614.13 | +27,793.20 | +2,220 | 0.83929 |
| V7 identity | 2392–128 | 0.94921 | 108,598.61 | +27,789.29 | +2,177 | 0.83929 |

Only one team contributed the two additional wins. This was treated as a weak hypothesis, not promotion evidence.

## Independent dose gate

Run `34510297857` tested static-equivalent quantities 1, 2 and 3 against V7 on new seeds, avoiding Python-router overhead and making every policy Rust-auditable.

### Complete 105-policy TOP15, seeds 143000–143023

5,040 games per candidate:

| Candidate | W–L | Own reward | Margin | Paired margin vs V7 |
|---|---:|---:|---:|---:|
| V7 | **4768–272** | 106,471.15 | +27,833.97 | — |
| pulse 1 | **4768–272** | 106,553.30 | +27,915.12 | +81.15 |
| pulse 2 | **4768–272** | 106,554.54 | +27,918.37 | +84.40 |
| pulse 3 | **4768–272** | **106,563.45** | **+27,953.31** | **+119.34** |

No dose added a win. The economic effect is real and predominantly positive, but binary performance was identical.

### Refreshed 84-policy TOP7, seeds 145000–145011

2,016 games per candidate:

| Candidate | W–L | Own reward | Margin |
|---|---:|---:|---:|
| **V7** | **1848–168** | 110,581.85 | +29,874.02 |
| pulse 1 | 1846–170 | 110,606.50 | +29,868.68 |
| pulse 2 | 1846–170 | 110,630.89 | +29,941.11 |
| pulse 3 | 1846–170 | **110,653.23** | **+29,964.60** |

Every pulse lost two wins. Quantity 2 remained binary-identical to V7 on recovered TOP30 at 178–122, but slightly reduced reward and margin relative to the previously matched V7 result.

## Decision

**No promotion.** The router features did not discover a stable conditional partition; the best evolved gene disabled both conditions. Its two-win selection gain disappeared on independent TOP15 and reversed on refreshed TOP7. The pulse remains a reproducible economic feature, but not a stronger V8.

The useful transferable result is methodological: a small router is viable infrastructure, but opponent money and fertilizer-market inventory at step 153 do not separate the beneficial and harmful cases robustly enough. A next router should only be attempted with richer counterfactual labels or additional public trajectory features, not by repeating this threshold grid.

## Artifacts

- `kaggriculture_meta_lab/results/v8-fertilizer-router-evolution-20260910.json`
- `kaggriculture_meta_lab/results/v8-fertilizer-dose-top15-independent-20260910.json`
- `kaggriculture_meta_lab/results/v8-fertilizer-dose-top7-independent-20260910.json`
- `kaggriculture_meta_lab/results/v8-fertilizer-dose2-top30-20260910.json`
- `kaggriculture_meta_lab/scripts/search_v8_fertilizer_router.py`
- `kaggriculture_meta_lab/agents/candidates/agent_v8_fertilizer_router.py`
