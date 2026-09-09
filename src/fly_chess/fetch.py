# Copyright (c) 2026 Martial Systems LLC
"""Opt-in MaleCNS v1.0 download. Hash-locked. Not used by pytest."""

from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path

from fly_chess.paths import CONFIG, DATA, PROVENANCE

CHUNK = 8 * 1024 * 1024


def datasets_path() -> Path:
    return CONFIG / "datasets.json"


def lock_path() -> Path:
    return PROVENANCE / "malecns_v1" / "source.lock.json"


def malecns_dir() -> Path:
    return DATA / "malecns" / "malecns_v1"


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def load_lock() -> dict:
    return json.loads(lock_path().read_text(encoding="utf-8"))


def malecns_present() -> bool:
    lock = load_lock()
    root = malecns_dir()
    for name, info in lock.items():
        dest = root / name
        if not dest.is_file():
            return False
        if dest.stat().st_size != int(info["bytes"]):
            return False
    return True


def fetch_malecns(*, force: bool = False) -> dict:
    """Download the three locked MaleCNS files and refuse a hash mismatch."""
    registry = json.loads(datasets_path().read_text(encoding="utf-8"))
    lock = load_lock()
    files = registry["datasets"]["malecns_v1"]["files"]
    root = malecns_dir()
    root.mkdir(parents=True, exist_ok=True)
    report = {}
    for name, url in files.items():
        expected = lock[name]
        if expected["url"] != url:
            raise RuntimeError(f"{name}: datasets.json URL does not match source.lock.json")
        dest = root / name
        if dest.is_file() and not force:
            digest = file_digest(dest)
            if digest != expected["sha256"] or dest.stat().st_size != int(expected["bytes"]):
                raise RuntimeError(f"{name}: local file does not match lock")
            report[name] = {"path": str(dest), "status": "present"}
            continue
        partial = dest.with_suffix(dest.suffix + ".partial")
        urllib.request.urlretrieve(url, partial)
        digest = file_digest(partial)
        size = partial.stat().st_size
        if digest != expected["sha256"] or size != int(expected["bytes"]):
            partial.unlink(missing_ok=True)
            raise RuntimeError(
                f"{name}: sha256/size mismatch (got {digest} {size}, "
                f"want {expected['sha256']} {expected['bytes']})"
            )
        partial.replace(dest)
        report[name] = {"path": str(dest), "status": "downloaded"}
    return report
