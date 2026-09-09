"""Safe bounded genomes for the V10 reactive policy.

Only literal module constants explicitly named by EVOLUTION_BOUNDS can change.
Candidate source is parsed, never imported or executed, during generation.
"""
from __future__ import annotations

import ast
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

Number = int | float


@dataclass(frozen=True)
class Gene:
    name: str
    current: Number
    low: Number
    high: Number

    @property
    def integral(self) -> bool:
        return isinstance(self.current, int) and not isinstance(self.current, bool)

    def clamp(self, value: Number) -> Number:
        value = max(self.low, min(self.high, value))
        return int(round(value)) if self.integral else float(value)


def _literal_assignments(source: str) -> dict[str, Any]:
    tree = ast.parse(source)
    values: dict[str, Any] = {}
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        target = node.targets[0] if isinstance(node, ast.Assign) and len(node.targets) == 1 else (
            node.target if isinstance(node, ast.AnnAssign) else None)
        if not isinstance(target, ast.Name) or node.value is None:
            continue
        try:
            values[target.id] = ast.literal_eval(node.value)
        except (ValueError, TypeError):
            continue
    return values


def load_genes(path: Path) -> tuple[str, list[Gene]]:
    source = path.read_text(encoding="utf-8")
    values = _literal_assignments(source)
    bounds = values.get("EVOLUTION_BOUNDS")
    if not isinstance(bounds, dict) or not bounds:
        raise ValueError("base must define a nonempty literal EVOLUTION_BOUNDS dict")
    genes: list[Gene] = []
    for name, limits in bounds.items():
        current = values.get(name)
        if not isinstance(name, str) or not isinstance(current, (int, float)) or isinstance(current, bool):
            raise ValueError(f"bounded constant must be a numeric literal: {name!r}")
        if not isinstance(limits, (tuple, list)) or len(limits) != 2:
            raise ValueError(f"bad bounds for {name}")
        low, high = limits
        if not all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in limits):
            raise ValueError(f"nonnumeric bounds for {name}")
        if low > current or current > high:
            raise ValueError(f"current {name}={current} outside [{low}, {high}]")
        genes.append(Gene(name, current, low, high))
    return source, genes


def baseline(genes: list[Gene]) -> dict[str, Number]:
    return {gene.name: gene.current for gene in genes}


def sample(genes: list[Gene], rng: random.Random) -> dict[str, Number]:
    result: dict[str, Number] = {}
    for gene in genes:
        value: Number = (rng.randint(int(gene.low), int(gene.high)) if gene.integral
                         else rng.uniform(float(gene.low), float(gene.high)))
        result[gene.name] = gene.clamp(value)
    return result


def mutate(genome: dict[str, Number], genes: list[Gene], rng: random.Random,
           rate: float = 0.25, scale: float = 0.15) -> dict[str, Number]:
    if not 0 <= rate <= 1 or scale < 0:
        raise ValueError("invalid mutation rate/scale")
    result = dict(genome)
    changed = False
    for gene in genes:
        if rng.random() >= rate:
            continue
        width = float(gene.high) - float(gene.low)
        result[gene.name] = gene.clamp(float(result[gene.name]) + rng.gauss(0.0, width * scale))
        changed = changed or result[gene.name] != genome[gene.name]
    if not changed and genes:
        gene = rng.choice(genes)
        # A forced local move prevents accidental clones in small integer ranges.
        delta = 1 if gene.integral else max((float(gene.high) - float(gene.low)) * scale, 1e-9)
        direction = -1 if float(result[gene.name]) >= float(gene.high) else 1
        result[gene.name] = gene.clamp(float(result[gene.name]) + direction * delta)
    return result


def crossover(a: dict[str, Number], b: dict[str, Number], genes: list[Gene],
              rng: random.Random) -> dict[str, Number]:
    return {gene.name: (a[gene.name] if rng.random() < 0.5 else b[gene.name]) for gene in genes}


def render(source: str, genome: dict[str, Number], genes: list[Gene]) -> str:
    allowed = {gene.name: gene for gene in genes}
    if set(genome) != set(allowed):
        raise ValueError("genome keys do not exactly match EVOLUTION_BOUNDS")
    rendered = source
    for name, value in genome.items():
        gene = allowed[name]
        value = gene.clamp(value)
        pattern = re.compile(rf"^{re.escape(name)}\s*=.*$", re.MULTILINE)
        matches = pattern.findall(rendered)
        if len(matches) != 1:
            raise ValueError(f"expected one module assignment for {name}, found {len(matches)}")
        rendered = pattern.sub(f"{name} = {value!r}", rendered, count=1)
    # Parse the product before writing it; generation must never emit bad Python.
    ast.parse(rendered)
    return rendered
