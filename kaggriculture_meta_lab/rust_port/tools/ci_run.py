#!/usr/bin/env python3
"""Run CI checks, publishing compact diagnostics to GitHub Check annotations.

This also works when the client can access GitHub's API but not the separate
Actions log/artifact hosts. No credentials or environment variables are logged.
Compressed text patches use small chunks to avoid annotation truncation.
"""
from __future__ import annotations
import base64
from pathlib import Path
import re
import subprocess
import sys
import zlib


def notice(title, message):
    escape = lambda s: s.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    print(f"::notice title={escape(title)}::{escape(message)}", flush=True)


def text_artifact(title, text):
    encoded = base64.b85encode(zlib.compress(text.encode(), 9)).decode()
    chunks = [encoded[i:i + 3000] for i in range(0, len(encoded), 3000)]
    for i, chunk in enumerate(chunks):
        notice(f"{title} z85 {i + 1}/{len(chunks)}", chunk)


def main():
    if sys.argv[1:] == ["--format"]:
        subprocess.run(["cargo", "fmt", "--all"], check=True)
        diff = subprocess.check_output(["git", "diff", "--", "*.rs"], text=True)
        if diff:
            text_artifact("rustfmt patch", diff)
        else:
            notice("Rust formatting", "Tracked Rust sources are rustfmt-clean.")
        return 0
    if sys.argv[1:] == ["--lockfile"]:
        text_artifact("Cargo.lock", Path("Cargo.lock").read_text())
        return 0
    command = sys.argv[1:]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(result.stdout, end="", flush=True)
    cleaned = re.sub(r"\x1b\[[0-9;]*m", "", result.stdout)
    notice(" ".join(command)[:180], f"exit_code={result.returncode}\n{cleaned[-3000:]}")
    if result.returncode:
        text_artifact("failure log " + " ".join(command)[:120], cleaned)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
