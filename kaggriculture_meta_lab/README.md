# Kaggriculture Meta-Lab — active workspace

This directory now contains only the active research path and reproducible
controls. Historical TOP49/TOP30 corpora, generated candidate farms, one-shot
workflows and rejected agent snapshots were removed on 2026-09-10; Git history
retains them if an old experiment ever needs reconstruction.

## Active policies

- `agents/current/agent_v9_b21_s16.py` — frozen strongest closed-loop control.
- `agents/ref/agent_v7.py` — simple reactive reference.
- `agents/variants/agent_v10_subin_106845775.py` — static Subin structural source.
- `agents/variants/agent_v11_subin_g4_29.py` — compact submitted G4 control.
- `agents/variants/agent_v11_reactive_score.py` — active reactive planner.

## Active corpus and evidence

`../TOP15.7z` is the sole primary replay archive. Extract it only to temporary
or ignored storage. Current records live in `results/`; the main interpretation
is `../kaggriculture/research/TOP15_REACTIVE_RECONSTRUCTION.md`.

## Development loop

1. Build exact observation state from the simulator schema.
2. Generate a bounded set of legal unit and market candidates.
3. Apply hard safety/resource constraints.
4. Rank safe actions by immediate value, future production and travel cost.
5. Screen both seats on identical seeds against V7 and B21.
6. Only then run TOP15 transfer and bounded population search.

Useful commands:

```bash
PYTHONPATH=. python -m pytest -q tests
python scripts/generate_reactive_population.py --output /tmp/reactive --population 16
python scripts/validate_current.py --candidate agents/variants/agent_v11_reactive_score.py \
  --control agents/current/agent_v9_b21_s16.py --games 16
```

Rust remains the preferred backend for compatible static/tape workloads. The
large 14k-game CI benchmark is opt-in and must not run on ordinary pushes.
