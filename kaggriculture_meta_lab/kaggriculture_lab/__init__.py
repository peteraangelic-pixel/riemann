"""Kaggriculture Meta-Lab: closed-loop tournament + open-loop corpus + sweeps.

A self-contained, Windows-friendly local research harness built *on top of* the
mature V7 agent work. It adds the one piece V7 was missing: a high-throughput
**closed-loop** evaluator where two real agents react to each other on the same
seeds, from both seats, with a Wilson statistical gate - plus an open-loop
replay benchmark against the real elite corpus and a fertilizer-leverage probe.

Modules:
    engine      - one game wrapper (deterministic seeds, isolated crashes)
    agents      - load .py policies / builtins / replay tapes
    stats       - Wilson CI, aggregation, promotion gate
    tournament  - parallel closed-loop paired-seat league
    corpus      - open-loop replay benchmark (.json.gz corpora)
    fertilizer  - fertilizer-leverage probe (cheap $1 fertilizer doubles yield)
"""

__version__ = "1.0.0"
EPISODE_STEPS = 720
