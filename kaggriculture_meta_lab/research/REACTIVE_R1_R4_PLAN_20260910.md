# Reactive roadmap R1–R4

G4 remains the strongest open-loop structural control. The next workstream is
not another unconstrained profile sweep; it is a bounded reactive planner.

## R1 — unit/field planner

Implemented primitives in `kaggriculture_lab/reactive_planner.py`:

- deterministic observation adapter boundary;
- urgent work before expansion;
- bounded legal-action candidates;
- water, harvest, fertilize, plant and move hooks;
- inventory liquidation with price floor and endgame override;
- cash reserve safety gate;
- deterministic scoring and PASS fallback.

R1 is intentionally not presented as a submission agent yet. It needs an
adapter for the exact simulator observation schema and replay tests before
integration.

## R2 — farm systems

Add land unlock, pasture/coop construction, animal placement, feed and care.
Each action must have a precondition and a material-cost budget. Compare each
module against G4 independently before composing them.

## R3 — bounded opponent response

Infer only public state classes, never player names:

- price pressure;
- production pressure;
- land race;
- cash race;
- endgame race.

Select a safe planner mode; do not allow the opponent classifier to emit raw
actions.

## R4 — policy selector

Select among audited modes: production, market, animals, expansion, recovery,
and endgame. Optional learned model may rank these modes only; the safety
layer owns legality and resource constraints.

## Promotion gates

Every R1–R4 candidate must pass paired seats with identical seeds, zero crashes,
positive material margin against frozen B21/S16, old TOP30 transfer, and fresh
holdout. Open-loop mirror score is diagnostic only.
