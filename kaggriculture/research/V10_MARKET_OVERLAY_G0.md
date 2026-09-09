# V10 market overlay — Generation 0

## Screen

Actions run `34376125158` evaluated 1,000 deterministic bounded profiles over
30,000 Rust games. Every profile used the static Subin 106845775 unit tape
against 15 non-source best-listed TOP10 records, both physical seats. Profiles
were ranked team-balanced; any simulator error was rejected.

The disabled control reproduced the earlier source-excluded result exactly:
14-16 (46.7%), team-balanced 48.15%, mean margin -282.13. It ranked first.
Every enabled random profile lost all 30 games. The least-bad enabled profile
had mean margin -36,687.

## Interpretation

This is a valid negative result, not evidence that reactive overlays are
intrinsically harmful. The first overlay clamps sale quantities from the shed
visible before unit actions. The static tape often drops carried harvest into
the shed during the same turn and sells it afterward. Therefore the overlay
systematically suppresses valid same-turn sales and destroys the policy.

Before Generation 1, saleable inventory must include inventory carried by live
units whose tape action will successfully DROP/PLACE beside an access tile,
subject to shed capacity and insertion order. The next population should also
be local mutations around the identity control rather than another broad
uniform draw. No enabled Generation-0 profile is eligible for promotion.
