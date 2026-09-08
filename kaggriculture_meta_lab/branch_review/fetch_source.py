#!/usr/bin/env python3
"""Fetch only the small, pinned source snapshot; never checkout another branch."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
from urllib.parse import quote

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=HERE.parents[1] / ".cache/peer-port")
    args = parser.parse_args()
    manifest = json.loads((HERE / "source_manifest.json").read_text())

    def fetch(entry):
        relative = PurePosixPath(entry["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("unsafe manifest path")
        path = args.destination.joinpath(*relative.parts)
        if path.is_file():
            raw = path.read_bytes()
            if hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest() == entry["blob_sha1"]:
                return
        url = f"repos/{manifest['repository']}/contents/{quote(entry['path'], safe='/')}?ref={manifest['commit']}"
        result = subprocess.run(["gh", "api", "-H", "Accept: application/vnd.github.raw+json", url], capture_output=True, check=True, timeout=60)
        raw = result.stdout
        if len(raw) != entry["size"] or hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest() != entry["blob_sha1"]:
            raise ValueError(f"source hash mismatch: {entry['path']}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(fetch, manifest["files"]))
    print(f"Verified {len(manifest['files'])} source files at {manifest['commit']}")


if __name__ == "__main__":
    main()
