# Copyright (c) 2026 Martial Systems LLC
"""Fail closed on banned claim tokens. Scan designated surfaces only."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

BANNED: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("learned_chess", re.compile(r"learned chess", re.I)),
    ("eyes_learned", re.compile(r"eyes learned", re.I)),
    ("understands_chess", re.compile(r"understands chess", re.I)),
    ("plays_on_chesscom", re.compile(r"plays on chess\.com", re.I)),
    ("fly_learned", re.compile(r"the fly learned", re.I)),
    ("photoreceptors_learning", re.compile(r"photoreceptors learned", re.I)),
)


class ClaimBanError(RuntimeError):
    pass


def scan_text(text: str) -> list[str]:
    return [name for name, pat in BANNED if pat.search(text or "")]


def require_clean(text: str, *, source: str) -> None:
    hits = scan_text(text)
    if hits:
        raise ClaimBanError(f"{source}: banned claims {hits}")
    if "—" in (text or ""):
        raise ClaimBanError(f"{source}: em dash")


def require_paths_clean(paths: Iterable[Path]) -> None:
    for path in paths:
        if path.is_file():
            require_clean(path.read_text(encoding="utf-8"), source=str(path))


def scan_log_claim_fields(path: Path) -> None:
    raw = json.loads(path.read_text(encoding="utf-8"))
    for key in ("claim", "banner", "summary"):
        if key in raw and isinstance(raw[key], str):
            require_clean(raw[key], source=f"{path}:{key}")
