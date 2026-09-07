# Audit: other Arena Meta-Lab branch

Source provenance (kept separate):

- Branch: `origin/arena/01a075fa-riemann`, reviewed at `e4198e0`.
- User-supplied conversation transcript: root file
  `2. Miałeś rację — taki lejek trzeba.txt` (commit `0e27823`).
- Review date: 2026-09-07.

No V7/B21 candidate code was changed as part of this audit.

## Executive verdict

The branch contributed a useful closed-loop process and one real old-planner
mechanic: bounded, in-field use of cow fertilizer by animal hands. It did not
produce a new policy competitive with the current scripted V7/B21 family.
Its “V8” and “V9” names belong to its own older heuristic-planner lineage and
must not be confused with current Aastik/hybrid or B21/S16.

## Other branch V8

Implementation: old heuristic `agent_v7.py` plus direct fertilizer application
by an animal hand after animal service, with a bounded detour and no fertilizer
stored in the shed. It also removes the farmer's pre-emptive shed detour.

Historical evidence:

- 733-267 over 1,000 closed-loop games versus that branch's old V7 (73.3%,
  mean margin +649, no errors).
- User's later broad sweep: 18,240 games; `detour1` was strongest directly
  versus old V7, while `endgame24` led the field-wide Bradley-Terry table.

This is credible attribution inside that engine, but not evidence against
current controls. Its scores were around 54k and its comparator was neither
scripted V7, Aastik, hybrid, nor B21/S16.

## Other branch V9

The branch tested demand-adaptive sheep expansion using visible unlocked shops.
It was rejected by its own data:

- conservative adaptation: 62.5% versus old V7 in 40 games, below V8's 67.5%
  on the same scale;
- aggressive expansion: roughly 50-58% in small screens;
- static seven/eight-sheep variants were strongly negative in tiny screens;
- direct V9-versus-V8 probe was 15-17-8 (47.5%, margin +9), effectively neutral.

The committed V9 defaults `ADAPT_ANIMALS=False`; therefore its promoted/default
behavior is V8, not an improved adaptive V9. Its useful negative conclusion is
that extra animals consume scarce hand/routing time, so naive sheep expansion
should not be transferred.

## Valuable ideas to retain

1. The observation exposes shared `market.prices`, `market.inventory`, and
   `town.unlocked_shops`; these are legitimate regime features.
2. Demand adaptation should preserve total labor load. Crop substitution or
   reduction may be safer than adding animals.
3. Fertilizer should be applied opportunistically without shed storage or a
   schedule-preempting fetch loop.
4. Inactive constants must be behavior-deduplicated; the uploaded V8 sweep
   demonstrated several exact duplicates.
5. Early screens rank hypotheses only; promotion needs paired fresh seeds,
   current controls, and elite replay holdouts.

## Ideas not ready to transfer

- More sheep or broad cow/sheep swings: empirically negative in that planner.
- Tomatoes/strawberries selected only from shop counts: proposed in the
  transcript but not implemented or validated there.
- Copying the fertilizer agent wholesale: incompatible with B21's fixed
  trajectory architecture. Any fertilizer experiment needs a B21-compatible,
  isolated action mutation and same-record attribution.
- Treating old-V7 Wilson intervals as current promotion evidence.

## Live B21 status at audit time

Status-only Actions run `34100262156` reported submission `56071535` COMPLETE
at public rating **2062.9**. At the same query: scripted V7 was 2193.5, Aastik
2215.3, and hybrid 2141.0. These ratings are live and can move. The submission
API does not expose a reliable W/L breakdown, so the user's observed early
zero-loss streak, 1,800+ gold after about one hour, and occasional 155k+ scores
are promising behavior observations but not yet enough to overrule the lower
aggregate rating.

## Recommended next gate (not executed in this audit)

Wait for the user's current bounded Lab result, then test only isolated
B21-compatible hypotheses. First priority is loss-family attribution and
late-game/opening mutations already identified for B21; fertilizer and
market-regime crop substitution should enter as separate experimental families,
not one combined agent. Keep V7, Aastik, hybrid, and untouched B21 as controls.
