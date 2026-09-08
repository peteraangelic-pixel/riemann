"""Prepare an isolated, narrowly patched copy of the pinned primary LAB.

The source branch and its frozen agents are never changed. The resulting patch
is an integration artifact, not an automatic deployment or promotion.
"""
from __future__ import annotations

import difflib
from pathlib import Path
import shutil


def prepare(source_root, destination):
    source_root, destination = Path(source_root), Path(destination)
    lab = destination / "kaggriculture_meta_lab"
    shutil.copytree(source_root / "kaggriculture_meta_lab", lab, dirs_exist_ok=True)
    source = (lab / "scripts/sweep.py").read_text()
    text = source

    def replace(old, new):
        nonlocal text
        if text.count(old) != 1:
            raise ValueError("pinned sweep context changed; do not force the patch")
        text = text.replace(old, new)

    replace("import argparse\n", "import argparse\nfrom collections import Counter\nimport math\n")
    replace('''        sig = (v.get("base", ""), json.dumps(v["params"], sort_keys=True))''',
            '''        # Prebuilt paths are part of variant identity, not merely metadata.
        sig = (v.get("base", ""), v.get("path", ""), json.dumps(v.get("params", {}), sort_keys=True))''')
    replace('''    return uniq


def project_game_budget''',
            '''    names = [v.get("name") for v in uniq]
    if any(not isinstance(name, str) or not name for name in names) or len(set(names)) != len(names):
        raise ValueError("variant names must be nonempty and unique")
    return uniq


def project_game_budget''')
    replace('''def _agg_by_tag(rows: list[dict]) -> dict[str, object]:''',
            '''def _require_stage_rows(rows: list[dict], jobs: list[tuple], stage: str) -> None:
    if not isinstance(rows, list) or len(rows) != len(jobs) or any(not isinstance(row, dict) for row in rows):
        raise RuntimeError(f"{stage}: incomplete or malformed result batch")
    expected = Counter((j[5], j[0], j[3], j[2]) for j in jobs)
    try:
        actual = Counter((r.get("tag"), r.get("seed"), r.get("seat"), r.get("opponent")) for r in rows)
    except TypeError as error:
        raise RuntimeError(f"{stage}: invalid result identity") from error
    if actual != expected:
        raise RuntimeError(f"{stage}: duplicate, missing or foreign result identity")
    _require_no_errors(rows, stage)
    for row in rows:
        own, opponent, margin = (row.get(k) for k in ("self_reward", "opp_reward", "margin"))
        try:
            valid = all(type(v) in (int, float) and math.isfinite(v) for v in (own, opponent, margin))
        except OverflowError:
            valid = False
        if not valid:
            raise RuntimeError(f"{stage}: non-finite or missing result values")
        outcome = "win" if own > opponent else "loss" if own < opponent else "tie"
        if margin != own - opponent or row.get("outcome") != outcome:
            raise RuntimeError(f"{stage}: inconsistent outcome or margin")


def _agg_by_tag(rows: list[dict]) -> dict[str, object]:''')
    for stage in ("screen", "promotion", "finals"):
        replace(f'    _require_no_errors(rows, "{stage}")', f'    _require_stage_rows(rows, jobs, "{stage}")')
    replace('''    stem2name = {p.stem: n for n, p in finalists}  # opponent path stem -> tag
    jobs, wins, games_map = [], {}, {}
    for i, (na, pa) in enumerate(finalists):
        for nb, pb in finalists[i + 1:]:
            jobs += build_jobs(str(pa), [str(pb)], games, seed,
                               swap_seats=True, steps=720, tag=na)''',
            '''    if len(set(names)) != len(names):
        raise ValueError("finalist names must be unique")
    # Filenames (even canonical paths) are not finalist identity: labels may
    # share a basename or intentionally refer to the same frozen policy.
    pairs = {}
    jobs, wins, games_map = [], {}, {}
    for i, (na, pa) in enumerate(finalists):
        for j, (nb, pb) in enumerate(finalists[i + 1:], start=i + 1):
            tag = f"__final_pair_{i}_{j}"
            pairs[tag] = (na, nb)
            jobs += build_jobs(str(pa), [str(pb)], games, seed,
                               swap_seats=True, steps=720, tag=tag)''')
    replace('''    # rows are tagged with the FIRST-listed agent of each pair; opponent path
    # stem maps back to its tag. Accumulate from a's perspective, then mirror.
    for r in rows:
        a = r["tag"]
        b = stem2name.get(Path(str(r["opponent"])).stem, Path(str(r["opponent"])).stem)''',
            '''    # Opaque pair tags travel only as metadata, never into an agent.
    for r in rows:
        a, b = pairs[r["tag"]]''')
    replace('''    return {"bt": dict(bt), "ranked": [n for n, _ in ranked]}''',
            '''    pairwise = {a: {b: {"games": games_map.get((a, b), 0),
                           "score": wins.get((a, b), 0.0) / games_map[(a, b)]
                           if games_map.get((a, b), 0) else None}
                    for b in names if b != a} for a in names}
    return {"bt": dict(bt), "ranked": [n for n, _ in ranked], "pairwise": pairwise}''')
    replace('    include_base = cfg.get("include_untouched_base", True)',
            '    baseline_spec = str(baseline_path.resolve())\n    include_base = cfg.get("include_untouched_base", True)')
    replace('stage_screen(variants, baseline, screen_games, seed0,',
            'stage_screen(variants, baseline_spec, screen_games, seed0,')
    replace('stage_promote(top, baseline, promote_games, seed0 + 10000,',
            'stage_promote(top, baseline_spec, promote_games, seed0 + 10000,')
    (lab / "scripts/sweep.py").write_text(text)
    name = "kaggriculture_meta_lab/scripts/sweep.py"
    patch = "diff --git a/" + name + " b/" + name + "\n"
    patch += "".join(difflib.unified_diff(source.splitlines(keepends=True), text.splitlines(keepends=True), fromfile="a/" + name, tofile="b/" + name))
    patch_path = destination / "funnel-identity-and-completeness.patch"
    patch_path.write_text(patch)
    return lab, patch_path
