# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import json
from pathlib import Path

from fly_chess.claims import scan_text
from fly_chess.lif import GAIN_PICK_NOTE, HOP_BUDGET_NOTE, MN9_MEAN_NOTE, SIGNS_MIX_NOTE

REPO = Path(__file__).resolve().parents[1]


def test_readme_is_closed_and_quotes_locks() -> None:
    text = (REPO / "README.md").read_text(encoding="utf-8")
    note = (REPO / "docs" / "planes_note.md").read_text(encoding="utf-8")
    eth = json.loads((REPO / "logs" / "ethology_gate.json").read_text(encoding="utf-8"))
    planes = json.loads((REPO / "logs" / "planes_gate.json").read_text(encoding="utf-8"))
    ident = json.loads((REPO / "logs" / "malecns_identity.json").read_text(encoding="utf-8"))
    circuit = json.loads((REPO / "logs" / "malecns_circuit.json").read_text(encoding="utf-8"))
    hop = json.loads((REPO / "logs" / "malecns_hop_probe.json").read_text(encoding="utf-8"))
    labels = json.loads((REPO / "logs" / "planes_labels.json").read_text(encoding="utf-8"))
    mix = json.loads((REPO / "logs" / "planes_mix.json").read_text(encoding="utf-8"))
    assert text.lower().startswith("# fly_chess\n\nclosed")
    assert "docs/planes_note.md" in text
    assert "Reserved pools reconstruct occupancy" in text
    assert "One mix ply removes those labels" in text
    assert "the labeled move does not" in text
    assert "typed occupancy register" in text
    assert "The 475-cell MaleCNS identity/circuit work is a different object" in text
    assert "The 475-cell MaleCNS identity/circuit work is a different object" in note
    assert "not the planes readout" in text
    assert "not the planes readout" in note
    assert f"{eth['real']['score']}" in text
    assert f"{eth['shuffled']['score']}" in text
    assert "0.50" in text
    assert str(eth["n_games"]) in text
    assert "774 vs 668" in text
    assert "41 vs 31" in text
    assert "1,007" in text or "1007" in text
    assert "475" in text
    assert "MaleCNS" in text
    assert "CC BY" in text
    assert ".venv/bin/python" in text
    assert "logs/ethology_gate.json" in text
    assert "logs/planes_gate.json" in text
    assert "logs/planes_head.json" in text
    assert "logs/planes_mix.json" in text
    assert "logs/planes_labels.json" in text
    assert "logs/malecns_identity.json" in text
    assert "logs/malecns_circuit.json" in text
    assert "logs/malecns_hop_probe.json" in text
    assert "docs/dynamics.md" in text
    assert "0.887" in text
    assert "0.693" in text
    assert "0.261" in text
    assert "legal mask is the decoder" in text
    assert circuit["games"] == 0
    assert circuit["elo"] is None
    assert circuit["gate2_quoted"] is False
    assert circuit["n_neurons"] == 475
    assert circuit["real"]["sugar"]["feed_mn"] == 37.5
    assert ident["real"]["sugar_on"]["feed_mn"] == 12.5
    assert ident["games"] == 0
    assert hop["n_neurons"] == 917
    assert hop["used_as_circuit_graph"] is False
    assert labels["gate2_quoted"] is False
    assert mix["n_eval"] == 62
    assert MN9_MEAN_NOTE in text
    assert GAIN_PICK_NOTE in text
    assert SIGNS_MIX_NOTE in text
    assert HOP_BUDGET_NOTE in text
    assert "What it is not" not in text
    assert "—" not in text
    assert scan_text(text) == []
    assert "learned chess" not in text.lower()
    assert "eyes learned" not in text.lower()
    assert "understands chess" not in text.lower()
    assert "plays on chess.com" not in text.lower()
    assert planes["n_games"] == 40
    assert eth["n_games"] == 40
    assert planes["load_bearing"]["wiring_is_encoder"] is False
    assert eth["load_bearing"]["wiring_is_encoder"] is False
    assert eth["real"]["hanging_chances"] == 774
    assert eth["shuffled"]["hanging_chances"] == 668
    assert "What it is not" not in note
    assert "—" not in note
    assert scan_text(note) == []
    assert "learned chess" not in note.lower()
    assert "Reserved pools reconstruct occupancy" in note
    assert "legal mask is the decoder" in note
    assert "Do not quote 0.771" in note
    dyn = (REPO / "docs" / "dynamics.md").read_text(encoding="utf-8")
    assert "current-based" in dyn.lower()
    assert "not Gate 2" in dyn
    assert MN9_MEAN_NOTE in dyn
    assert GAIN_PICK_NOTE in dyn
    assert SIGNS_MIX_NOTE in dyn
    assert HOP_BUDGET_NOTE in dyn
