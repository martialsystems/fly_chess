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
    ident = json.loads((REPO / "logs" / "malecns_identity.json").read_text(encoding="utf-8"))
    assert f"{eth['real']['score']}" in text
    assert f"{eth['shuffled']['score']}" in text
    assert "0.50" in text
    assert str(eth["n_games"]) in text
    assert "774 vs 668" in text
    assert "290" in text
    assert "475" in text
    assert "MaleCNS" in text
    assert "CC BY" in text
    assert ".venv/bin/python" in text
    assert "## Numbers" in text
    assert "logs/ethology_gate.json" in text
    assert "logs/planes_gate.json" in text
    assert "logs/malecns_identity.json" in text
    assert "the wiring is not doing the chess work" in text
    assert "What it is not" not in text
    assert "—" not in text
    assert scan_text(text) == []
    assert "learned chess" not in text.lower()
    assert "eyes learned" not in text.lower()
    assert "understands chess" not in text.lower()
    assert "plays on chess.com" not in text.lower()
    assert ident["n_neurons_real"] == 475
    assert ident["passed"]["identity"] is True
    assert ident["gate2_quoted"] is False
    assert planes["n_games"] == 40
    assert eth["n_games"] == 40
    assert planes["load_bearing"]["wiring_is_encoder"] is False
    assert eth["load_bearing"]["wiring_is_encoder"] is False
    assert eth["real"]["hanging_chances"] == 774
    assert eth["shuffled"]["hanging_chances"] == 668
