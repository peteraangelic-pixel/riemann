#!/usr/bin/env python3
"""Inventory current TOP12 policies that can coherently branch from the V2 tape.

This is a structural census, not a promotion benchmark.  It finds replay policies
whose unit/logistics stream is identical (or has a long exact prefix) to V2 and
therefore may supply market alternatives without pretending an incompatible
opening was executed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmark_top30 import build_top30_jobs  # noqa: E402
from kaggriculture_lab.rust_backend import TapeSource, _source  # noqa: E402


def unit_part(action: dict[str, Any]) -> tuple[Any, ...]:
    return (
        tuple(action.get("farmer") or ["PASS"]),
        tuple(tuple(x) for x in (action.get("hands") or [])),
    )


def market_part(action: dict[str, Any]) -> tuple[tuple[Any, ...], ...]:
    return tuple(tuple(x) for x in (action.get("market") or []))


def prefix_length(left: list[Any], right: list[Any], projection) -> int:
    for index, (a, b) in enumerate(zip(left, right)):
        if projection(a) != projection(b):
            return index
    return min(len(left), len(right))


def equal_count(left: list[Any], right: list[Any], projection) -> int:
    return sum(projection(a) == projection(b) for a, b in zip(left, right))


def action_digest(actions: list[dict[str, Any]], projection) -> str:
    payload = [projection(action) for action in actions]
    return hashlib.sha256(repr(payload).encode()).hexdigest()[:16]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    base = _source(str(args.base.resolve()))
    if base is None:
        raise ValueError("base is not a static tape")
    base_actions = base.actions[0]
    jobs, metadata = build_top30_jobs(args.corpus.resolve(), args.base.resolve(), 12)

    records: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()
    for job, meta in zip(jobs, metadata):
        # build_top30_jobs emits the same replay twice for candidate seats.
        spec = job[2]
        key = (str(meta["replay_file"]), int(meta["recorded_team_seat"]))
        if key in seen:
            continue
        seen.add(key)
        donor = _source(spec)
        if donor is None:
            raise ValueError(f"cannot compile donor: {spec}")
        actions = donor.actions[0]
        compared = min(len(base_actions), len(actions))
        unit_prefix = prefix_length(base_actions, actions, unit_part)
        full_prefix = prefix_length(base_actions, actions, lambda x: (unit_part(x), market_part(x)))
        market_prefix = prefix_length(base_actions, actions, market_part)
        unit_equal = equal_count(base_actions, actions, unit_part)
        market_equal = equal_count(base_actions, actions, market_part)
        records.append({
            **{k: meta[k] for k in (
                "rank", "team", "slot", "episode_id", "submission_id",
                "submission_public_score", "best_listed_submission", "replay_file",
                "recorded_team_seat",
            )},
            "steps": len(actions),
            "compared_steps": compared,
            "full_prefix_steps": full_prefix,
            "unit_prefix_steps": unit_prefix,
            "market_prefix_steps": market_prefix,
            "unit_equal_steps": unit_equal,
            "unit_equal_rate": unit_equal / compared if compared else 0.0,
            "market_equal_steps": market_equal,
            "market_equal_rate": market_equal / compared if compared else 0.0,
            "unit_digest": action_digest(actions, unit_part),
            "market_digest": action_digest(actions, market_part),
        })

    records.sort(key=lambda r: (
        -r["unit_prefix_steps"], -r["unit_equal_rate"], -r["full_prefix_steps"],
        r["rank"], r["slot"], r["episode_id"],
    ))
    exact_unit = [r for r in records if r["unit_equal_steps"] == r["compared_steps"]]
    long_prefix = [r for r in records if r["unit_prefix_steps"] >= 24]
    digest_counts = Counter(r["unit_digest"] for r in records)
    payload = {
        "format": "v26-prefix-compatible-top12-census-v1",
        "definition": {
            "full_prefix": "consecutive identical farmer, hands, and market actions from step 0",
            "unit_prefix": "consecutive identical farmer and hands actions from step 0",
            "exact_unit_stream": "farmer and hands actions identical at every compared step",
            "warning": "market substitutions still require acquisition/legality and fresh holdout gates",
        },
        "base": str(args.base),
        "records": len(records),
        "exact_unit_stream_records": len(exact_unit),
        "long_unit_prefix_records": len(long_prefix),
        "distinct_unit_streams": len(digest_counts),
        "largest_unit_stream_families": [
            {"digest": digest, "records": count}
            for digest, count in digest_counts.most_common(20)
        ],
        "exact_unit_candidates": exact_unit,
        "long_prefix_candidates": long_prefix,
        "all": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: payload[k] for k in (
        "records", "exact_unit_stream_records", "long_unit_prefix_records",
        "distinct_unit_streams", "largest_unit_stream_families",
    )}, indent=2))


if __name__ == "__main__":
    main()
