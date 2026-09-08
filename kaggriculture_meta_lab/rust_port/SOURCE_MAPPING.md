# Mapping the pinned Python rules to Rust

Authority: `reference/kaggriculture_sim.py`, byte-identical to
`kaggle-environments==1.32.7`. See `reference/provenance.json` for hashes.
This table is for audits when upstream changes; it does not replace differential
state/reward tests. The explicit mapping format was a useful idea in the
alternate port supplied on 2026-09-08.

| Python responsibility / functions | Rust implementation | Important preserved behavior |
|---|---|---|
| `CROPS`, `ANIMALS`, `PRODUCTS`, `SHOPS` | `src/data.rs` | Exact indices/constants; shop-choice table sorted as in Python |
| Configuration defaults and sparse market overrides | `Config::from_json`, `market::default_params` | Flat overrides distinct from specification descriptors; unknown products ignored |
| `_shape`, `market_price` | `Shape::apply`, `PriceCurve::from_json/price` | Ties-to-even, floor 1, `log(1+x)`, independent scarcity/glut shapes |
| `_new_farm`, `_new_private`, `_new_market`, `_new_town`, initialization | `Game::new`, `Farm::new` | Two farms and one market; inventory starts at each configured I0 |
| Integer-seeded `random.Random`, `random()`, `choice(sorted(SHOPS))` | `src/rng.rs` | Wide signed day-seed expression; MT19937 and rejection sampling |
| Atomic per-crop PLANT demand validation | `Farm::apply_actions` | Raw nonexistent-hand requests still count; optional wrapper clipping occurs first |
| `_apply_unit_action` | `Farm::apply_unit` | Farmer then hands; shed actions before locked-tile restrictions |
| `_inv_add`, `_inv_take`, inventory dictionary ordering | `Inventory::add/take` | Removal and reinsertion change key order exactly as Python dicts |
| `_spawn_hand`, Fibonacci HIRE, `_do_hire` | `Farm::hire` | Least-occupied shed access tile; deterministic tie order; purchases after actions |
| `_do_buy_land` | `Farm::buy_land` | NW already owned; NE, SW, SE unlock in order at fixed costs |
| `_process_market` | `Game::process_market` | Preserve order slots; quote both seats before committing either unit |
| `_commit_unit` | `Farm::commit` | BUY_PRODUCT post-buy quote; $1 SELL does not add supply |
| `_town_consume` | `Game::town_consume` | Consumption also at step 0; duplicate shops; no town-center fertilizer demand |
| `_decay_plants` | `Farm::decay_plants` | Decay after unit/market actions, every other turn from lifespan boundary |
| `_daily_refresh_plants` | `Farm::refresh_plants` | Planting-day drought, ongoing production schedule and fertilization windows |
| `_daily_refresh_animals` | `Farm::refresh_animals` | Delayed care bonus; unfed production clears the bank; escape leaves structure |
| `_spawn_weeds` | `Farm::end_day` | Row-major; draws only on empty tiles, including when chance is zero |
| `_drop_inventories_to_shed`, daily unit reset | `Inventory::drop_to_shed`, `Farm::end_day` | Farmer-first insertion order; overflow discarded; reusable hand allocation |
| `_end_of_day` | `Game::step_with_hand_trimming`, `Farm::end_day` | One stream: seat 0 weeds, seat 1 weeds, then shop selection |
| Interpreter turn order / episode horizon | `Game::step*`, `Replay`, CLI `StepMode` | 720 Kaggle recorded states mean 719 actions; literal-turn mode is explicit |
| Public/private observations for diagnosis | `Game::snapshot`, `src/snapshot.rs` | Full mechanics state, allocation-heavy and never used by the fast stepping loop |

## Deliberate implementation differences, not rule changes

- Arrays/enums replace Python dictionaries/strings in the hot path.
- Each tape is normalized once; helper capacity is reserved before simulation.
- Curve amplitudes are precomputed once. Prices used in transactions are still
  calculated unit by unit against the shared inventory.
- Observation-only cached prices are materialized for snapshots, not refreshed
  repeatedly when no tape reads them.
- `Replay::new_with_hand_trimming` takes rules in input A/B order and transfers
  them with each tape when seats reverse. `Game::step_with_hand_trimming` takes
  physical-seat order. The existing uniform-boolean methods remain aliases.
- Only independent games are parallelized. No per-seat simulation split or
  shared mutable global market/RNG is introduced.

The binary remains strict `[seat][step]` JSON. A single policy stream can be
mirrored explicitly by `tools/export_tape.py --single-stream`, outside the
simulation core.
