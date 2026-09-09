#!/usr/bin/env python3
"""Generate deterministic bounded profiles for the native Rust market overlay."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

# Compact Generation-0 search space. Unlisted product thresholds/reserves use
# fail-open zero defaults shared by Python and Rust.
BOUNDS = {
    "start_day": (0, 12), "buy_stop_day": (22, 30), "endgame_day": (24, 29),
    "cash_reserve": (0, 1500), "sell_fraction_bp": (2500, 10000),
    "endgame_sell_fraction_bp": (7500, 10000), "wheat_reserve": (0, 30),
    "melon_reserve": (0, 12), "milk_reserve": (0, 18), "wool_reserve": (0, 18),
    "min_wheat_price": (0, 80), "min_melon_price": (0, 250),
    "min_milk_price": (0, 180), "min_wool_price": (0, 220),
}


def generate_profiles(population: int, seed: int) -> list[dict[str, object]]:
    """Return a unique deterministic Generation-0 population."""
    if not 1 <= population <= 100_000:
        raise ValueError("population must be in 1..100000")
    rng = random.Random(seed)
    profiles: list[dict[str, object]] = [{"enabled": False}]
    seen = {json.dumps(profiles[0], sort_keys=True)}
    while len(profiles) < population:
        profile: dict[str, object] = {"enabled": True}
        for name, (low, high) in BOUNDS.items():
            profile[name] = rng.randint(low, high)
        key = json.dumps(profile, sort_keys=True)
        if key not in seen:
            seen.add(key)
            profiles.append(profile)
    return profiles


LOCAL_OPTIONS = {
    "start_day": tuple(range(8, 25, 4)),
    "buy_stop_day": (27, 28, 29, 30),
    "cash_reserve": (100, 200, 300, 500),
    "sell_fraction_bp": (8500, 9000, 9500, 9750),
    "endgame_sell_fraction_bp": (9000, 9500, 9750, 10000),
    "wheat_reserve": (1, 2, 4, 6),
    "melon_reserve": (1, 2, 3),
    "milk_reserve": (1, 2, 3, 4),
    "wool_reserve": (1, 2, 3, 4),
    "min_wheat_price": (10, 20, 30, 40),
    "min_melon_price": (20, 40, 60, 80),
    "min_milk_price": (20, 40, 60, 80),
    "min_wool_price": (20, 40, 60, 80),
}


def generate_local_profiles(population: int, seed: int) -> list[dict[str, object]]:
    """Identity control plus sparse 1–3 gene mutations for Generation 1."""
    if not 2 <= population <= 100_000:
        raise ValueError("local population must be in 2..100000")
    rng = random.Random(seed)
    profiles: list[dict[str, object]] = [{"enabled": False}, {"enabled": False}]
    seen = {json.dumps(p, sort_keys=True) for p in profiles}
    names = tuple(LOCAL_OPTIONS)
    while len(profiles) < population:
        # Preserve the observed two-turn bootstrap and early market financing.
        profile: dict[str, object] = {"enabled": True, "start_day": 8}
        for name in rng.sample(names, rng.randint(1, 3)):
            profile[name] = rng.choice(LOCAL_OPTIONS[name])
        key = json.dumps(profile, sort_keys=True)
        if key not in seen:
            seen.add(key)
            profiles.append(profile)
    return profiles


def generate_refined_profiles() -> list[dict[str, object]]:
    """Cartesian refinement around the two robust Generation-1 leaders."""
    profiles: list[dict[str, object]] = [{"enabled": False}, {"enabled": False}]
    seen = {json.dumps(p, sort_keys=True) for p in profiles}
    for start_day in (6, 8, 10):
        for cash in (0, 100, 150, 200, 250, 300):
            for wheat_price in (0, 10, 20, 30, 40):
                for milk_reserve in (0, 1, 2, 3):
                    profile = {
                        "enabled": True, "start_day": start_day,
                        "cash_reserve": cash, "min_wheat_price": wheat_price,
                        "milk_reserve": milk_reserve,
                    }
                    key = json.dumps(profile, sort_keys=True)
                    if key not in seen:
                        seen.add(key)
                        profiles.append(profile)
    return profiles


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--population", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=20260909)
    args = ap.parse_args()
    try:
        profiles = generate_profiles(args.population, args.seed)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    args.output.mkdir(parents=True, exist_ok=True)
    candidates = []
    for i, profile in enumerate(profiles):
        name = f"market-g0-{i:05d}"
        text = json.dumps(profile, indent=2, sort_keys=True) + "\n"
        path = args.output / f"{name}.json"
        path.write_text(text, encoding="utf-8")
        candidates.append({"name": name, "file": path.name, "profile": profile,
                           "sha256": hashlib.sha256(text.encode()).hexdigest()})
    manifest = {"format": "kaggriculture-market-overlay-population-v1",
                "seed": args.seed, "population": len(candidates),
                "bounds": BOUNDS, "candidates": candidates}
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"wrote {len(candidates)} market overlays to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
