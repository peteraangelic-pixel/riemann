#!/usr/bin/env python3
"""Regenerate small CPython RNG / reference market conformance fingerprints."""
from __future__ import annotations
import json
from pathlib import Path
import random
from py_reference import SIM

ROOT = Path(__file__).resolve().parents[1]
OFFSET = 14695981039346656037
PRIME = 1099511628211
MASK = (1 << 64) - 1


def digest(values):
    h = OFFSET
    for n in values:
        h = ((h * PRIME) ^ n) & MASK
    return h


def main():
    rng_vectors = []
    for seed in [0, 1, -1, 2**32, 2**63 - 1, -(2**63)]:
        for day in [0, 3, 29, 1000000]:
            mixed = (seed * 1000003) ^ day
            r = random.Random(mixed)
            words = digest(r.getrandbits(32) for _ in range(5000))
            r = random.Random(mixed)
            mixed_calls = [[r.random(), r.choice(range(8))] for _ in range(20)]
            rng_vectors.append({"seed": seed, "day": day, "words_fnv64": words, "mixed_calls": mixed_calls})
    prices = []
    for item in SIM.PRODUCTS:
        values = (SIM.market_price(item, inventory) for inventory in range(-10000, 20001))
        prices.append({"item": item, "fnv64": digest(values)})
    out = ROOT / "tests/fixtures/conformance.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"rng": rng_vectors, "market_range": [-10000, 20001], "prices": prices}, indent=2) + "\n")
    print(out)


if __name__ == "__main__":
    main()
