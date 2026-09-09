# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import json
from pathlib import Path

from fly_chess import QUESTION
from fly_chess.claims import scan_text

REPO = Path(__file__).resolve().parents[1]


def test_readme_opens_with_the_question() -> None:
    text = (REPO / "README.md").read_text(encoding="utf-8")
    body = "\n".join(text.splitlines()[1:]).lstrip()
    assert body.startswith(QUESTION)
    eth = json.loads((REPO / "logs" / "ethology_gate.json").read_text(encoding="utf-8"))
    planes = json.loads((REPO / "logs" / "planes_gate.json").read_text(encoding="utf-8"))
    assert f"{eth['real']['score']:.3f}" in text
    assert f"{eth['shuffled']['score']:.3f}" in text
    assert f"{eth['real']['hanging_capture_rate']:.3f}" in text
    assert f"{eth['shuffled']['hanging_capture_rate']:.3f}" in text
    assert eth["fixture_sha256"] in text
    assert "290" in text
    assert "Approach/avoid controller" in text
    assert "Piece-plane encoding plus a trained legal-move readout" in text
    assert "MaleCNS" in text
    assert "CC BY" in text
    assert ".venv/bin/python" in text
    assert "APP_LOCUS" in text
    assert "voltage" in text.lower() or "lif.json" in text
    assert "What it is not" not in text
    assert "—" not in text
    assert scan_text(text) == []
    assert "learned chess" not in text.lower()
    assert "chess.com" not in text.lower()
    assert planes["n_games"] == 40
    assert eth["n_games"] == 40
    assert f"{planes['gate1_real']['accuracy']:.3f}" in text
