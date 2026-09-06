#!/usr/bin/env python3
"""Fingerprint the compact TOP49 replay export without third-party packages.

The export contains five replay summaries per leaderboard player.  Its generic
parser lost product labels/final rewards, but retained player-specific action
counts and 25 early private/farm snapshots.  Those fields are enough for an
initial, explicitly open-loop policy-family clustering.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

TURNS = (0, 1, 2, 3, 5, 8, 12, 16, 20, 24)
LIFESPANS = (120, 192, 240, 312, 360, 480, 720)


def mean(rows: list[list[float]]) -> list[float]:
    return [sum(col) / len(rows) for col in zip(*rows)]


def dist(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def target_name(doc: dict) -> str:
    return doc["replay"].split("/")[1]


def own_farm(snapshot: dict, seat: int) -> dict[str, float]:
    prefix = f"farms[{seat}]."
    return {key[len(prefix):]: float(value) for key, value in snapshot["farms_numeric"].items()
            if key.startswith(prefix)}


def vector(doc: dict) -> tuple[str, list[str], list[float]]:
    target = target_name(doc)
    seat = doc["players"].index(target)
    player = next(row for row in doc["features"] if row["player"] == target)
    names = ["action_count", "buy_count", "sell_count", "buy_sell_count_ratio",
             "first_buy_turn", "first_sell_turn", "sell_activity_span"]
    values = [float(player.get(name) or 0.0) for name in names]

    snapshots = {int(row["turn"]): row for row in doc["native_observations_sample"]
                 if row["player"] == target}
    for turn in TURNS:
        snap = snapshots.get(turn)
        private = snap["private_numeric"] if snap else {}
        farm = own_farm(snap, seat) if snap else {}
        for key in sorted(k for k in private if k.startswith("private.shed.")):
            names.append(f"t{turn}:{key}")
            values.append(float(private[key]))
        for key in sorted(k for k in private if k.startswith("private.seeds.")):
            names.append(f"t{turn}:{key}")
            values.append(float(private[key]))
        for key in ("money", "hires_today", "farmer[0]", "farmer[1]"):
            names.append(f"t{turn}:farm.{key}")
            values.append(float(farm.get(key, 0.0)))

        life = Counter(int(v) for k, v in farm.items() if k.endswith(".max_lifespan_step"))
        for lifespan in LIFESPANS:
            names.append(f"t{turn}:lifespan_{lifespan}")
            values.append(float(life[lifespan]))
        placed = sum(k.endswith(".placed_day") for k in farm)
        yield_units = sum(v for k, v in farm.items() if k.endswith(".yield_units"))
        unfed = sum(v for k, v in farm.items() if k.endswith(".consecutive_unfed"))
        unwatered = sum(v for k, v in farm.items() if k.endswith(".consecutive_unwatered"))
        for key, val in (("placed", placed), ("yield", yield_units),
                         ("unfed", unfed), ("unwatered", unwatered)):
            names.append(f"t{turn}:{key}")
            values.append(float(val))
    return target, names, values


def load(path: Path) -> tuple[list[str], dict[str, list[list[float]]], dict]:
    games: dict[str, list[list[float]]] = defaultdict(list)
    episode_ids: list[str] = []
    parser_counts: Counter[str] = Counter()
    feature_names: list[str] | None = None
    with zipfile.ZipFile(path) as archive:
        members = [name for name in archive.namelist()
                   if "_replay_" in name and name.endswith(".json")]
        for member in members:
            doc = json.loads(archive.read(member))
            target, names, values = vector(doc)
            if feature_names is None:
                feature_names = names
            elif names != feature_names:
                raise ValueError(f"inconsistent compact schema in {member}")
            games[target].append(values)
            match = re.search(r"_(\d+)\.json", doc["replay"])
            if match:
                episode_ids.append(match.group(1))
            parser_counts[str(doc.get("parser"))] += 1
    if not feature_names:
        raise ValueError("no compact replay summaries found")
    metadata = {
        "records": sum(map(len, games.values())),
        "players": len(games),
        "unique_episodes": len(set(episode_ids)),
        "duplicate_episode_records": len(episode_ids) - len(set(episode_ids)),
        "parser_counts": dict(parser_counts),
    }
    return feature_names, dict(games), metadata


def standardize(centers: dict[str, list[float]]) -> tuple[dict[str, list[float]], list[float], list[float]]:
    rows = list(centers.values())
    mus = mean(rows)
    sigmas = []
    for i, mu in enumerate(mus):
        sigma = math.sqrt(sum((row[i] - mu) ** 2 for row in rows) / len(rows))
        sigmas.append(sigma if sigma > 1e-9 else 1.0)
    return ({name: [(x - mu) / sigma for x, mu, sigma in zip(row, mus, sigmas)]
             for name, row in centers.items()}, mus, sigmas)


def kmeans(points: dict[str, list[float]], k: int) -> tuple[dict[str, int], float]:
    names = sorted(points)
    best: tuple[dict[str, int], float] | None = None
    for offset in range(min(12, len(names))):
        chosen = [names[offset]]
        while len(chosen) < k:
            remaining = [name for name in names if name not in chosen]
            chosen.append(max(remaining, key=lambda name: min(dist(points[name], points[c]) for c in chosen)))
        centroids = [points[name][:] for name in chosen]
        labels: dict[str, int] = {}
        for _ in range(100):
            updated = {name: min(range(k), key=lambda c: dist(points[name], centroids[c])) for name in names}
            if updated == labels:
                break
            labels = updated
            for c in range(k):
                rows = [points[name] for name in names if labels[name] == c]
                if rows:
                    centroids[c] = mean(rows)
        sse = sum(dist(points[name], centroids[labels[name]]) ** 2 for name in names)
        if best is None or sse < best[1]:
            best = labels, sse
    assert best is not None
    return best


def silhouette(points: dict[str, list[float]], labels: dict[str, int]) -> float:
    result = []
    for name, point in points.items():
        own = [other for other in points if other != name and labels[other] == labels[name]]
        if not own:
            result.append(0.0)
            continue
        a = sum(dist(point, points[other]) for other in own) / len(own)
        other_clusters = set(labels.values()) - {labels[name]}
        b = min(sum(dist(point, points[other]) for other in points if labels[other] == cluster) /
                sum(labels[other] == cluster for other in points) for cluster in other_clusters)
        result.append((b - a) / max(a, b) if max(a, b) else 0.0)
    return sum(result) / len(result)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", nargs="?", type=Path, default=Path("per_replay.zip"))
    parser.add_argument("--json", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()

    feature_names, games, metadata = load(args.archive)
    raw_centers = {name: mean(rows) for name, rows in games.items()}
    points, mus, sigmas = standardize(raw_centers)
    scores = {}
    candidates = {}
    for k in range(2, min(11, len(points))):
        labels, sse = kmeans(points, k)
        scores[k] = {"silhouette": silhouette(points, labels), "sse": sse}
        candidates[k] = labels
    # Avoid selecting a trivial two-way split: choose the best silhouette among 3..10.
    selected_k = max((k for k in scores if k >= 3), key=lambda k: scores[k]["silhouette"])
    labels = candidates[selected_k]
    clusters = {str(c): sorted(name for name in points if labels[name] == c)
                for c in sorted(set(labels.values()))}

    aastik = "Aastik Rajan15"
    distances = {name: dist(points[name], points[aastik]) for name in points}
    stability = {}
    for name, rows in games.items():
        zrows = [[(x - mu) / sigma for x, mu, sigma in zip(row, mus, sigmas)] for row in rows]
        stability[name] = sum(dist(row, points[name]) for row in zrows) / len(zrows)
    stable_cutoff = statistics.median(stability.values())
    shortlist = [name for name in sorted(points, key=lambda n: distances[n], reverse=True)
                 if stability[name] <= stable_cutoff and name not in {aastik, "Crop Dusta", "keiz"}][:10]
    nearest = {name: sorted(((dist(points[name], points[other]), other)
                             for other in points if other != name))[:5] for name in points}

    result = {
        "source": str(args.archive), "limitations": [
            "generic export has null final scores/winners",
            "product labels and quantities were lost by the generic action parser",
            "only turns 0-24 have state snapshots",
            "clusters are discovery aids, not evidence that a policy beats V8",
        ], "metadata": metadata, "feature_count": len(feature_names),
        "k_scores": {str(k): row for k, row in scores.items()}, "selected_k": selected_k,
        "clusters": clusters, "distance_from_aastik": distances,
        "within_player_instability": stability, "stable_cutoff": stable_cutoff,
        "distinct_stable_shortlist": shortlist,
        "nearest_neighbors": {name: [{"player": other, "distance": d} for d, other in rows]
                              for name, rows in nearest.items()},
    }
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf8")

    lines = ["# TOP49 compact replay fingerprint report", "",
             f"- Player records: **{metadata['records']}** ({metadata['players']} players × 5)",
             f"- Unique episodes: **{metadata['unique_episodes']}**; cross-folder duplicates: **{metadata['duplicate_episode_records']}**",
             f"- Fingerprint dimensions: **{len(feature_names)}**", f"- Selected exploratory clusters: **{selected_k}**", "",
             "## Cluster-selection diagnostics", "", "| k | silhouette | SSE |", "|---:|---:|---:|"]
    for k, row in scores.items():
        lines.append(f"| {k} | {row['silhouette']:.3f} | {row['sse']:.1f} |")
    lines += ["", "## Policy-family clusters", ""]
    for cluster, members in clusters.items():
        marker = " (contains Aastik)" if aastik in members else ""
        lines += [f"### Cluster {cluster}{marker}", "", ", ".join(members), ""]
    lines += ["## Distinct and internally stable discovery shortlist", "",
              "This list excludes already-tested Crop Dusta and keiz. Distance is from the Aastik family; lower instability means the player's five samples agree more closely.", "",
              "| player | distance from Aastik | within-player instability | nearest policy |", "|---|---:|---:|---|"]
    for name in shortlist:
        lines.append(f"| {name} | {distances[name]:.2f} | {stability[name]:.2f} | {nearest[name][0][1]} ({nearest[name][0][0]:.2f}) |")
    lines += ["", "## Important limitations", ""] + [f"- {x}" for x in result["limitations"]]
    lines += ["", "The shortlist identifies where full-replay retrieval and executable tape reconstruction should begin. It does not justify modifying or submitting V8.", ""]
    text = "\n".join(lines)
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(text, encoding="utf8")
    print(text)


if __name__ == "__main__":
    main()
