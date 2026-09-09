#!/usr/bin/env python3
"""Create a deterministic, bounded V10 reactive population without execution."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kaggriculture_lab.reactive_genetics import (  # noqa: E402
    baseline, load_genes, mutate, render, sample,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path,
                        default=ROOT / "agents/variants/agent_v10_reactive_subin.py")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--population", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20260909)
    parser.add_argument("--mutation-rate", type=float, default=0.25)
    parser.add_argument("--mutation-scale", type=float, default=0.15)
    args = parser.parse_args()
    if not 1 <= args.population <= 10_000:
        raise SystemExit("--population must be in 1..10000")
    if not 0.0 < args.mutation_rate <= 1.0:
        raise SystemExit("--mutation-rate must be in (0, 1]")
    if args.mutation_scale <= 0.0:
        raise SystemExit("--mutation-scale must be positive")

    base = args.base.resolve()
    source, genes = load_genes(base)
    rng = random.Random(args.seed)
    args.output.mkdir(parents=True, exist_ok=True)
    genomes = [baseline(genes)]
    attempts = 0
    max_attempts = args.population * 1_000
    while len(genomes) < args.population and attempts < max_attempts:
        attempts += 1
        parent = sample(genes, rng) if len(genomes) == 1 else rng.choice(genomes)
        child = mutate(parent, genes, rng, args.mutation_rate, args.mutation_scale)
        if child not in genomes:
            genomes.append(child)
    if len(genomes) != args.population:
        raise SystemExit("could not construct the requested number of unique genomes")

    entries = []
    for index, genome in enumerate(genomes):
        name = f"g0-{index:05d}"
        text = render(source, genome, genes)
        path = args.output / f"{name}.py"
        path.write_text(text, encoding="utf-8")
        entries.append({
            "name": name,
            "file": path.name,
            "genome": genome,
            "sha256": hashlib.sha256(text.encode()).hexdigest(),
        })
    manifest = {
        "format": "kaggriculture-reactive-population-v1",
        "base": base.name,
        "seed": args.seed,
        "population": len(entries),
        "mutation_rate": args.mutation_rate,
        "mutation_scale": args.mutation_scale,
        "genes": [{"name": g.name, "current": g.current,
                   "low": g.low, "high": g.high} for g in genes],
        "candidates": entries,
    }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(entries)} candidates with {len(genes)} bounded genes to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
