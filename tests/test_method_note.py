# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

from pathlib import Path

import pytest

from fly_chess.claims import scan_text

REPO = Path(__file__).resolve().parents[1]
PDF = REPO / "docs" / "method_note.pdf"


def _pdf_text() -> str:
    pypdf = pytest.importorskip("pypdf")
    reader = pypdf.PdfReader(str(PDF))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def test_method_pdf_exists_and_is_dated() -> None:
    assert PDF.is_file()
    assert PDF.read_bytes()[:5] == b"%PDF-"
    text = _pdf_text()
    assert "From a failed move head to child-position value" in text
    assert "2026-09-12" in text
    assert "Revisions" in text
    assert "0.4875" in text
    assert "0.887" in text
    assert "0.91" in text
    assert "0.4825" in text
    assert "0.5665" in text
    assert "0.6075" in text
    assert "0.25" in text
    assert "0.905" in text
    assert "distill" in text.lower()
    assert "wiring_helped is false" in text.lower() or "wiring_helped false" in text.lower()
    assert "child-position value" in text.lower()
    assert "wiring_helped" in text or "wiring helped" in text.lower() or "B-real" in text
    assert "What it is not" not in text
    assert "—" not in text
    assert scan_text(text) == []
    assert "learned chess" not in text.lower()
    src = (REPO / "scripts" / "make_method_note.py").read_text(encoding="utf-8")
    assert "—" not in src
    assert "What it is not" not in src
