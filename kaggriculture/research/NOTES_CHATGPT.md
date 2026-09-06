# Valuable findings from `opinie chatgpt.txt`

The last 30% is weighted most heavily because it incorporates Stages H-K and the two V8 submissions.

## Current strategic conclusions

- Aastik is the broad-population rating baseline (73/85); Renoir is an elite/high-money specialist. A perfect selector between only those two tops out at 77/85 because eight losses are shared.
- Therefore an Aastik/Renoir selector is not the final solution. The eight shared failures should be treated as the training/evaluation set for discovering a third policy.
- The 203,785 hybrid is not a generally stronger agent. It identifies a coherent opening primitive: Renoir's first three wheat-market actions can be attached to Aastik while preserving downstream state.
- Build a library of primitives with explicit preconditions and state deltas: duration, inventory delta, cash delta, market delta, and compatibility conditions. This is safer than switching whole tapes.
- Before machine learning, perform contrastive analysis at horizons 5/10/15/20/25 over Aastik-only wins, Renoir-only wins, common losses, and rescued losses.
- Candidate regime features should include price levels and velocities, market inventory/volume, opponent opening orders, first purchases/sales, cash trajectory, our inventory, and temporal deltas—not one threshold such as milk price.
- With only 85 tuned episodes, use leave-one-out or cross-validation and a fresh holdout. Avoid a high-capacity selector that memorizes episode fingerprints.
- Hard experimental controls: same seeds, both seats, baseline/control/mutation, confidence intervals, margins, tails/crashes, and an untouched holdout.

## Priority order extracted from the current portion

1. Monitor real V8 Aastik and hybrid submissions.
2. Common-loss mining and third-policy discovery.
3. Opening-primitive library and compatibility checking.
4. Validate fertilizer only against the current Aastik baseline; do not assume an old-planner result transfers.
5. Expand daily top replay acquisition/fingerprinting.
6. Only later consider random forests/RL/genetic search.

## Already tested here

- Global and day-specific market ordering.
- Premium-price sale deferral (strongly negative).
- Whole-tape and physical/market fusion (mostly catastrophic).
- Aastik/Renoir switch days and exact opening steps.
- Renoir three-action opening primitive, which produced 203,785 but one fewer live win.

## Warnings retained

- Final-money records and Bradley-Terry strength are different objectives.
- Open-loop replay wins are not closed-loop wins against adaptive private code.
- Repeatedly tuning on the same 85 episodes risks selection bias.
- Do not infer a gain from a mutation unless the control differs only in that mutation.
