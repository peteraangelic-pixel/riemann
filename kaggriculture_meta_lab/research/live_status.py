#!/usr/bin/env python3
"""Read-only Kaggle status. Uses an existing environment secret, never chat data.

Only public leaderboard fields and public submission scores are emitted.
No submission, selection, team mutation or secret-writing API is called.
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import re
import tempfile
import zipfile


def redacted(text):
    for value in (os.environ.get("KAGGLE_API_TOKEN", ""),):
        if value:
            text = text.replace(value, "[REDACTED]")
    return re.sub(r"KGAT_[A-Za-z0-9_-]+", "[REDACTED]", text)


def emit(report):
    text = redacted(json.dumps(report, ensure_ascii=False, indent=2))
    print(text)
    # Keep annotations small; unlike artifact downloads these are visible via GH API.
    compact = redacted(json.dumps(report, ensure_ascii=False, separators=(",", ":")))
    for i in range(0, len(compact), 2800):
        chunk = compact[i:i + 2800].replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print(f"::notice title=Kaggle live audit part {i // 2800 + 1}::{chunk}")


def main():
    report = {"as_of_utc": datetime.now(timezone.utc).isoformat(), "competition": "kaggriculture", "mode": "read-only", "errors": []}
    value = "".join(os.environ.get("KAGGLE_API_TOKEN", "").split())
    if not value:
        report["errors"].append("KAGGLE_API_TOKEN repository secret is missing; configure it outside chat")
        emit(report)
        return 2
    os.environ["KAGGLE_API_TOKEN"] = value
    try:
        from kaggle import api
        with tempfile.TemporaryDirectory(prefix="kg-public-status-") as directory:
            api.competition_leaderboard_download("kaggriculture", directory, quiet=True)
            archive_path = Path(directory) / "kaggriculture.zip"
            with zipfile.ZipFile(archive_path) as archive:
                files = [name for name in archive.namelist() if name.lower().endswith(".csv") and "private" not in name.lower()]
                if not files:
                    raise ValueError("no public CSV found in leaderboard download")
                public = next((name for name in files if "public" in name.lower()), files[0])
                rows = list(csv.DictReader(io.StringIO(archive.read(public).decode("utf-8-sig"))))
            norm = lambda key: re.sub(r"[ _-]", "", key).lower()
            normalized = [{norm(k): v for k, v in row.items()} for row in rows]
            def safe_row(row):
                return {k: row[k] for k in ("rank", "teamid", "teamname", "score", "submissiondate", "lastsubmissiondate") if k in row}
            ours = [row for row in normalized if "lauresowe" in row.get("teamname", "").casefold()]
            report["leaderboard_rows"] = len(rows)
            report["leaderboard_headers"] = list(rows[0]) if rows else []
            report["our_team"] = [safe_row(row) for row in ours]
            report["top12"] = [safe_row(row) for row in normalized[:12]]
        # Explicitly project away private scores, user identity and descriptions.
        submissions = api.competition_submissions("kaggriculture", page_size=20) or []
        report["recent_submission_public_scores"] = [
            {"ref": s.ref, "date": str(s.date), "status": str(s.status), "public_score": s.public_score}
            for s in submissions[:10]
        ]
    except Exception as error:
        report["errors"].append(redacted(f"{type(error).__name__}: {error}")[:1400])
    emit(report)
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
