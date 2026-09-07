#!/usr/bin/env python3
"""Run CI checks, publishing compact diagnostics to GitHub Check annotations.

This also works when the client can access GitHub's API but not the separate
Actions log/artifact hosts. No credentials or environment variables are logged.
"""
from __future__ import annotations
import subprocess
import sys


def notice(title, message):
    escape = lambda s: s.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    print(f"::notice title={escape(title)}::{escape(message)}", flush=True)


def main():
    if sys.argv[1:] == ["--format"]:
        subprocess.run(["cargo", "fmt", "--all"], check=True)
        diff = subprocess.check_output(["git", "diff", "--", "*.rs"], text=True)
        if diff:
            chunks = [diff[i:i + 40000] for i in range(0, len(diff), 40000)]
            for i, chunk in enumerate(chunks):
                notice(f"rustfmt patch {i + 1}/{len(chunks)}", chunk)
        else:
            notice("Rust formatting", "Tracked Rust sources are rustfmt-clean.")
        return 0
    if sys.argv[1:] == ["--lockfile"]:
        from pathlib import Path
        notice("Cargo.lock", Path("Cargo.lock").read_text())
        return 0
    command = sys.argv[1:]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(result.stdout, end="", flush=True)
    notice(" ".join(command)[:180], f"exit_code={result.returncode}\n{result.stdout[-45000:]}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
