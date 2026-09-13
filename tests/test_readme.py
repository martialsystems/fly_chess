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
    assert text.lower().startswith("# fly_chess\n\n**methods note (2026-09-12):**")
    assert "](docs/method_note.pdf)" in text
    pdf = REPO / "docs" / "method_note.pdf"
    assert pdf.is_file()
    assert pdf.read_bytes()[:5] == b"%PDF-"
    assert "Two measurements" in text
    assert "Child-position value (closed)" in text
    assert "docs/value_note.md" in text
    assert "chess-on-wiring line is done" in text.lower()
    assert "Mix-0 occupancy plus a child ranker plays" in text
    assert "2-ply search on that eval is a real bot" in text
    assert "real graph is silent at 0 Hz" in text
    assert "shuffled copy is not silent and still cannot play" in text
    assert "The fly is the skin" in text
    assert "0.995" in text
    assert "0.4875" in text
    assert "logs/followup_lock.json" in text
    assert "logs/search_lock.json" in text
    assert "logs/mix1_distill.json" in text
    assert "logs/value_lock.json" in text
    assert "Mix-1 chess distill is closed" in text
    val = json.loads((REPO / "logs" / "value_lock.json").read_text(encoding="utf-8"))
    assert val["A"]["games"]["score"] == 0.91
    assert val["B_real"]["games"]["score"] == 0.4825
    assert val["wiring_helped"] is False
    assert "`wiring_helped` is false" in text
    closed = text.lower().split("planes policy")[1]
    assert closed.strip().startswith("(closed)")
    assert "Closed. A shuffle-controlled measurement" in text
    assert "[Fly research index](https://gist.github.com/martialsystems/12835f747d6360781f3cc7f91f243178)" in text
    assert "docs/planes_note.md" in text
    assert "docs/value_note.md" in text
    assert "logs/value_lock.json" in text
    note_v = (REPO / "docs" / "value_note.md").read_text(encoding="utf-8")
    assert "What it is not" not in note_v
    assert "—" not in note_v
    assert "child-position value" in note_v.lower()
    assert "shuffle seeds {1,2,3,4,5}" in note_v or "{1,2,3,4,5}" in note_v
    assert "Reserved pools reconstruct occupancy" in text
    assert "One mix ply removes those labels" in text
    assert "the labeled move does not" in text
    for name in ("fig_labels.png", "fig_delta.png", "fig_cosine.png"):
        path = REPO / "docs" / name
        assert path.is_file()
        assert path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
        assert f"docs/{name}" in text
    fig_src = (REPO / "scripts" / "make_readme_figures.py").read_text(encoding="utf-8")
    delta_fn = fig_src.split("def fig_delta")[1].split("def fig_cosine")[0]
    assert 'fmt="o-"' in delta_fn
    assert "set_ylim(-0.04, 0.04)" in delta_fn
    assert "Wiring does not make the labeled move linearly easier" in delta_fn
    assert "Shuffle-controlled delta" not in delta_fn
    assert "legend" not in delta_fn
    assert "axes.unicode_minus" in fig_src
    labels_fn = fig_src.split("def fig_labels")[1].split("def fig_delta")[0]
    assert "Occupancy is readable; one mix ply deletes the labels" in labels_fn
    assert "Mix 0 (occupancy)" in labels_fn
    assert "check_escape" not in labels_fn
    assert 'mix_plies"] == 3' not in labels_fn
    assert "_label_bars" in labels_fn
    assert "_acc_label" in labels_fn
    games_fn = fig_src.split("def fig_games")[1].split("def main")[0]
    assert "n={n}" in games_fn
    assert "not restamped" in games_fn
    assert "_label_bars" in games_fn
    assert "def _score_label" in fig_src
    assert "def _acc_label" in fig_src
    assert "def _label_bars" in fig_src
    assert "hanging n_eval=53" in text
    assert "teacher n_eval=88" in text
    assert "n_eval=62, five seeds" in text
    assert "fig_games.png" in text
    assert "Historical" in text
    assert "not restamped" in text.lower() or "Not restamped" in text
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
