#!/usr/bin/env python3
"""Read-only Kaggle live snapshot for seat 087c0 (competition kaggriculture).

Writes JSON to --output: our team rows (lauresowe), top-20, and recent
submissions (ref/date/status/publicScore/description). No uploads, no
selection, no team mutation. Auth: KAGGLE_API_TOKEN env (repo secret).
"""
import argparse
import csv
import io
import json
import os
import re
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def redacted(text):
    for value in (os.environ.get("KAGGLE_API_TOKEN", ""),):
        if value:
            text = text.replace(value, "[REDACTED]")
    return re.sub(r"KGAT_[A-Za-z0-9_-]+", "[REDACTED]", text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    report = {"as_of_utc": datetime.now(timezone.utc).isoformat(),
              "competition": "kaggriculture", "mode": "read-only", "errors": []}
    value = "".join(os.environ.get("KAGGLE_API_TOKEN", "").split())
    if not value:
        report["errors"].append("KAGGLE_API_TOKEN secret missing")
        a.output.write_text(json.dumps(report, indent=2))
        return 2
    os.environ["KAGGLE_API_TOKEN"] = value
    try:
        from kaggle import api
        with tempfile.TemporaryDirectory(prefix="kg-live-") as directory:
            api.competition_leaderboard_download("kaggriculture", directory, quiet=True)
            archive_path = Path(directory) / "kaggriculture.zip"
            with zipfile.ZipFile(archive_path) as archive:
                files = [n for n in archive.namelist()
                         if n.lower().endswith(".csv") and "private" not in n.lower()]
                if not files:
                    raise ValueError("no public CSV in leaderboard download")
                public = next((n for n in files if "public" in n.lower()), files[0])
                rows = list(csv.DictReader(io.StringIO(archive.read(public).decode("utf-8-sig"))))
        norm = lambda k: re.sub(r"[ _-]", "", k).lower()
        normalized = [{norm(k): v for k, v in row.items()} for row in rows]
        ours = [r for r in normalized if "lauresowe" in r.get("teamname", "").casefold()]
        report["leaderboard_rows"] = len(rows)
        report["our_team"] = ours
        report["top20"] = normalized[:20]
        subs = api.competition_submissions("kaggriculture", page_size=20) or []
        report["recent_submissions"] = [
            {"ref": s.ref, "file": getattr(s, "fileName", ""), "date": str(s.date),
             "status": str(s.status), "public_score": s.public_score,
             "private_score": getattr(s, "privateScore", ""),
             "description": (s.description or "")[:300]} for s in subs[:15]]
    except Exception as error:  # noqa: BLE001 - report, don't crash blind
        report["errors"].append(redacted(f"{type(error).__name__}: {error}")[:1400])
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(redacted(json.dumps(report, indent=2, ensure_ascii=False)))
    print(redacted(json.dumps({k: report[k] for k in ("as_of_utc", "leaderboard_rows")}, indent=2)))
    print(f"our_team rows: {len(report.get('our_team', []))}")
    for r in report.get("our_team", []):
        print(" ", redacted(json.dumps(r, ensure_ascii=False)))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
