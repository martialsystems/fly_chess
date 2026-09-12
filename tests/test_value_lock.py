# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_value_lock_table_and_freeze() -> None:
    raw = json.loads((REPO / "logs" / "value_lock.json").read_text(encoding="utf-8"))
    eth = json.loads((REPO / "logs" / "ethology_gate.json").read_text(encoding="utf-8"))
    assert raw["A"]["games"]["n_games"] == 200
    assert raw["A"]["games"]["score"] == 0.91
    assert raw["A"]["beats_random"] is True
    assert raw["A"]["synapses_used"] is False
    assert raw["B_real"]["games"]["n_games"] == 200
    assert raw["B_real"]["games"]["score"] == 0.4825
    assert raw["B_real"]["hidden_rates_silent"] is True
    assert raw["B_shuffle"]["shuffle_seeds"] == [1, 2, 3, 4, 5]
    assert raw["B_shuffle"]["games"]["n_games_per_seed"] == 200
    assert raw["B_shuffle"]["games"]["score"] == 0.5665
    assert raw["table"]["A_games"] == 0.91
    assert raw["table"]["B_real_games"] == 0.4825
    assert raw["table"]["B_shuffle_games"] == 0.5665
    assert raw["wiring_helped"] is False
    assert raw["unfreeze_allowed"] is False
    assert raw["elo"] is None
    assert raw["gate2_quoted"] is False
    assert raw["C"]["head"] == "mlp_two_layer"
    assert raw["C"]["held_out"]["child_pairwise"] == raw["B_real"]["held_out"]["child_pairwise"]
    assert eth["real"]["score"] == 0.4875
    assert eth["n_games"] == 40
