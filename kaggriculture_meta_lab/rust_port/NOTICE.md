# Attribution and source provenance

This Rust simulator is a new implementation of the Kaggriculture game rules
from **kaggle-environments 1.32.7**, distributed under the Apache License 2.0.
The upstream package is maintained by Kaggle; its utilities carry
“Copyright 2020 Kaggle Inc”. The upstream Apache license is included as `LICENSE`.

`reference/kaggriculture_sim.py` and `reference/kaggriculture_config.json` are
unmodified copies supplied through the user's repository. They were independently
compared byte for byte against the wheel published on PyPI. The wheel and file
SHA-256 hashes, and the input GitHub commit, are recorded in `reference/provenance.json`.

`reference/seed_utils.py` retains the upstream copyright/license notice and the
unmodified `resolve_episode_seed` function, extracted from the same package's
`utils.py`. Only standalone imports and an explanatory extraction comment were
added around that function. The test adapter substitutes this tiny dependency
at import time; it never replaces game-rule functions with a Python rewrite.

The example agent and handoff document are preserved as user-provided reference
material. The safe exporter reads only the supported data format and explicitly
supported tape mutations; it does not execute arbitrary agent code.

All Rust files, CLI/batch handling, snapshots, Python adapters and tests in this
directory are new or adapted implementations, not unmodified upstream code.
The RNG reproduces CPython integer-seeded MT19937 behavior; it is not NumPy's RNG.
