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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--population", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=20260909)
    args = ap.parse_args()
    if not 1 <= args.population <= 100_000:
        raise SystemExit("--population must be in 1..100000")
    args.output.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    profiles: list[dict[str, object]] = [{"enabled": False}]
    seen = {json.dumps(profiles[0], sort_keys=True)}
    while len(profiles) < args.population:
        profile: dict[str, object] = {"enabled": True}
        for name, (low, high) in BOUNDS.items():
            profile[name] = rng.randint(low, high)
        key = json.dumps(profile, sort_keys=True)
        if key not in seen:
            seen.add(key)
            profiles.append(profile)
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
