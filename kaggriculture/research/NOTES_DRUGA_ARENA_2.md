# Valuable findings from `druga arena 2.txt`

## Proven or actionable

- Closed-loop evaluation is the main missing complement to the mature open-loop replay benchmark. Use paired seeds, both seats, process workers, Wilson confidence intervals, positive mean margin, and zero crashes as a promotion gate.
- A naive fertilizer buyer is invalid. `BUY_PRODUCT FERTILIZER` puts fertilizer in the shed; `FERTILIZE` consumes it from a unit inventory. Buying without pickup/use wastes cash.
- Setting a positive shed fertilizer reserve in the old planner activates a routing failure: the farmer repeatedly detours to the shed and starves watering/harvesting. Cheap fertilizer can also fill the 100-unit shed and block valuable deposits.
- The safe planner experiment applies cow-collected fertilizer directly from an animal hand, only after animal chores, with a bounded radius-2 detour. Radius 4/unbounded regressed.
- The other branch measured 27-13 over 40 paired closed-loop games, Wilson 95% interval 52.0-79.9%, margin +634, for fertilizer-only versus its old planner baseline. This merits follow-up, not automatic promotion.
- Do not bundle strawberry expansion with fertilizer. The transcript caught a misleading comparison where both candidate/control had strawberries; against the true control, adding 12 strawberries regressed.
- The Windows lab should start with 16 processes on a 5950X. Hundreds of total games can run concurrently in batches; 32 simultaneous Python processes are not automatically faster because SMT and memory pressure matter.

## Critical applicability caveat

The 67.5% fertilizer result uses `kaggriculture/agent_v7.py`, the unsuccessful planner family, not the selected Renoir/Aastik tapes. It does not establish a gain over V8 Aastik. Aastik already buys 67 fertilizer units, requests 371 fertilizer sales, collects fertilizer 379 times, and executes 96 `FERTILIZE` actions in its source trajectory; Renoir executes 75. Therefore the claim that our selected strategy simply ignores fertilizer is false for the current finalists.

## Ideas worth testing

1. Transfer only coherent opening primitives, not whole mismatched market/physical schedules.
2. Mine the eight Aastik/Renoir common-loss episodes to discover a third policy.
3. Evaluate any fertilizer change directly against Aastik and the submitted hybrid, first as a no-detour opportunistic primitive, then closed-loop.
4. Use a fresh replay archive and public executable opponents for validation; tapes remain open-loop.

## Rejected or already known

- Buy fertilizer blindly: rejected by 0-16 and approximately -84k in the transcript.
- Positive shed reserve without routing redesign: catastrophic.
- More strawberries as part of the same fertilizer test: confounded and then rejected.
- Wholesale tape fusion: our Stages F-I already showed physical, market, inventory, and cash schedules are tightly coupled.
