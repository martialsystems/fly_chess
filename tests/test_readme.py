# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

from pathlib import Path

from fly_chess.claims import scan_text

REPO = Path(__file__).resolve().parents[1]


def test_readme_two_experiments_and_allowed_claims() -> None:
    text = (REPO / "README.md").read_text(encoding="utf-8")
    assert text.startswith("# fly_chess")
    assert "Approach/avoid controller" in text
    assert "Piece-plane encoding plus a trained legal-move readout" in text
    assert "MaleCNS" in text
    assert "CC BY" in text
    assert ".venv/bin/python" in text
    assert "synthetic" in text.lower() or "APP_LOCUS" in text
    assert "What it is not" not in text
    assert "—" not in text
    assert scan_text(text) == []
    assert "learned chess" not in text.lower()
    assert "chess.com" not in text.lower()
