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
    assert "0.4875" in text
    assert str(eth["real"]["score"]) in text
    assert str(eth["shuffled"]["score"]) in text
    assert "wiring is not an encoder" in text.lower()
    assert "it flees check when it can" not in text
    assert "not evidence the graph flees" in text
    assert "774 vs 668" in text
    assert "do not promote" in text.lower()
    assert eth["fixture_sha256"] in text
    assert "290" in text
    assert "Approach/avoid controller, local score 0.4875 vs random, shuffled wiring 0.4875." in text
    assert "Piece-plane encoding plus a trained legal-move readout" in text
    assert "MaleCNS" in text
    assert "CC BY" in text
    assert ".venv/bin/python" in text
    assert "APP_LOCUS" in text
    assert "lif.json" in text
    assert "What it is not" not in text
    assert "—" not in text
    assert scan_text(text) == []
    assert "learned chess" not in text.lower()
    assert "chess.com" not in text.lower()
    assert planes["n_games"] == 40
    assert eth["n_games"] == 40
    assert "31/32" in text
    assert planes["load_bearing"]["wiring_is_encoder"] is False
    assert eth["load_bearing"]["wiring_is_encoder"] is False
