# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_distill_lock_beats_truncated_selfplay() -> None:
    d = json.loads((REPO / "logs" / "value_distill.json").read_text(encoding="utf-8"))
    sp = json.loads((REPO / "logs" / "value_selfplay.json").read_text(encoding="utf-8"))
    a = json.loads((REPO / "logs" / "value_lock.json").read_text(encoding="utf-8"))
    eth = json.loads((REPO / "logs" / "ethology_gate.json").read_text(encoding="utf-8"))
    assert d["child_label"] == "hand_eval"
    assert d["not_truncated_return"] is True
    assert d["generator"] == "A_vs_A_after_random_opening"
    assert d["matches_A"] is True
    assert d["distill_vs_random"]["n_games"] == 200
    assert d["distill_vs_random"]["score"] == 0.905
    assert d["distill_vs_random"]["score"] > sp["selfplay_vs_random"]["score"]
    assert d["outcome"]["vs_random"]["score"] == 0.83
    assert d["outcome"]["vs_2ply_search"]["score"] == 0.0
    assert d["synapses_used"] is False
    assert d["unfreeze_allowed"] is False
    assert a["A"]["games"]["score"] == 0.91
    assert eth["real"]["score"] == 0.4875
    assert d["held_out"]["n_children"] == 50812
