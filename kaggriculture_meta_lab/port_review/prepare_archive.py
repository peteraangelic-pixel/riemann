"""Isolate the uploaded archive and make an explicitly labelled compile-only copy.

The ZIP and the production simulator are never edited. All extraction/build
outputs live in ignored storage. This is an audit, not an alternate-engine fix.
"""
from __future__ import annotations

import difflib
import hashlib
from pathlib import Path, PurePosixPath
import shutil
import stat
import zipfile

ZIP_SHA256 = "d194d7197f0adcad4a6e6a1eedde6b6eb319e3748d55437f63da9a96c9b7b740"


def prepare(archive, directory):
    archive, directory = Path(archive), Path(directory)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != ZIP_SHA256:
        raise ValueError("archive changed; review and pin its new checksum first")
    original = directory / "original"
    original.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as source:
        if sum(i.file_size for i in source.infolist()) > 20_000_000:
            raise ValueError("oversized source archive")
        for entry in source.infolist():
            path = PurePosixPath(entry.filename)
            if path.is_absolute() or ".." in path.parts or "\\" in entry.filename or ".git" in path.parts:
                raise ValueError("unsafe archive path")
            if stat.S_ISLNK(entry.external_attr >> 16) or entry.file_size > 5_000_000:
                raise ValueError("unsafe archive member")
            if "__pycache__" in path.parts or entry.is_dir():
                continue
            destination = original.joinpath(*path.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read(entry))
    original = original / "kaggriculture_rust"
    if (original / "build.rs").exists() or (original / ".cargo").exists():
        raise ValueError("unreviewed build hooks/configuration")
    fixed = directory / "compile-only" / "kaggriculture_rust"
    shutil.copytree(original, fixed, dirs_exist_ok=True)
    replacements = {
        "src/main.rs": [
            ('get_i("shedCapacity",d.shed_capacity)', 'get_i("shedCapacity",i64::from(d.shed_capacity))', 1),
            ("tape::Tape", "model::Tape", 3),
            ("let seed64=match checked_i128_to_i64(seed){Ok(v)=>v,Err(e)=>error_json(e)};",
             "let seed64=checked_i128_to_i64(seed).map_err(error_json);", 1),
        ],
        "src/sim.rs": [
            ("use crate::{model::*, py_rng::PythonRandom, tape::Tape};", "use crate::{model::*, py_rng::PythonRandom};", 1),
            ("step as i32 < plant.max_lifespan_step", "(step as i32) < plant.max_lifespan_step", 1),
        ],
    }
    patch = []
    for name, changes in replacements.items():
        old = (fixed / name).read_text()
        text = old
        for before, after, count in changes:
            if text.count(before) != count:
                raise ValueError(f"compile-only patch context changed: {name}")
            text = text.replace(before, after)
        (fixed / name).write_text(text)
        patch.append(f"diff --git a/{name} b/{name}\n")
        patch.extend(difflib.unified_diff(old.splitlines(keepends=True), text.splitlines(keepends=True), fromfile=f"a/{name}", tofile=f"b/{name}"))
    patch_path = directory / "compile-only.patch"
    patch_path.write_text("".join(patch))
    return original, fixed, patch_path
