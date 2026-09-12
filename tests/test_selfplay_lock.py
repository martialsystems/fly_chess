# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_selfplay_lock_loses_to_a_and_keeps_freeze() -> None:
    raw = json.loads((REPO / "logs" / "value_selfplay.json").read_text(encoding="utf-8"))
    a = json.loads((REPO / "logs" / "value_lock.json").read_text(encoding="utf-8"))
    eth = json.loads((REPO / "logs" / "ethology_gate.json").read_text(encoding="utf-8"))
    assert raw["selfplay_vs_random"]["n_games"] == 200
    assert raw["selfplay_vs_random"]["score"] == 0.6075
    assert raw["hand_eval_A_vs_random"]["score"] == 0.91
    assert raw["hand_eval_A_vs_random"]["score"] == a["A"]["games"]["score"]
    assert raw["selfplay_vs_A"]["score"] == 0.25
    assert raw["beats_random"] is True
    assert raw["beats_A"] is False
    assert raw["wiring_helped"] is False
    assert raw["unfreeze_allowed"] is False
    assert raw["synapses_used"] is False
    assert raw["elo"] is None
    assert raw["n_games_generated"] == 400
    assert eth["real"]["score"] == 0.4875
    assert a["wiring_helped"] is False
