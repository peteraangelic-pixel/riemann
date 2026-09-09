from __future__ import annotations

import ast
import random
from pathlib import Path

from kaggriculture_lab.reactive_genetics import (
    baseline, crossover, load_genes, mutate, render, sample,
)

BASE = Path(__file__).resolve().parents[1] / "agents/variants/agent_v10_reactive_subin.py"


def test_real_profile_loads_without_importing_and_baseline_renders():
    source, genes = load_genes(BASE)
    assert len(genes) >= 12
    genome = baseline(genes)
    rendered = render(source, genome, genes)
    assert ast.parse(rendered)
    assert "SUBIN_OPENING" in rendered


def test_sampling_mutation_and_crossover_are_deterministic_and_bounded():
    source, genes = load_genes(BASE)
    a = sample(genes, random.Random(7))
    assert a == sample(genes, random.Random(7))
    b = mutate(a, genes, random.Random(8), rate=1.0, scale=0.2)
    child = crossover(a, b, genes, random.Random(9))
    for genome in (a, b, child):
        for gene in genes:
            assert gene.low <= genome[gene.name] <= gene.high
            assert isinstance(genome[gene.name], int) if gene.integral else isinstance(genome[gene.name], float)
        ast.parse(render(source, genome, genes))


def test_unknown_or_missing_genome_keys_fail_closed():
    source, genes = load_genes(BASE)
    genome = baseline(genes)
    genome.pop(genes[0].name)
    try:
        render(source, genome, genes)
    except ValueError as exc:
        assert "keys" in str(exc)
    else:
        raise AssertionError("incomplete genome was accepted")
