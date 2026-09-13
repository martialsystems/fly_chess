# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_followup_lock_closes_chess_on_wiring() -> None:
    raw = json.loads((REPO / "logs" / "followup_lock.json").read_text(encoding="utf-8"))
    eth = json.loads((REPO / "logs" / "ethology_gate.json").read_text(encoding="utf-8"))
    planes = json.loads((REPO / "logs" / "planes_gate.json").read_text(encoding="utf-8"))
    a = json.loads((REPO / "logs" / "value_lock.json").read_text(encoding="utf-8"))
    search = json.loads((REPO / "logs" / "search_lock.json").read_text(encoding="utf-8"))
    mix1 = json.loads((REPO / "logs" / "mix1_distill.json").read_text(encoding="utf-8"))
    assert raw["closed"] is True
    assert raw["wiring_helped"] is False
    assert raw["mix1_chess_distill"] == "closed"
    assert raw["search_2ply_vs_1ply"] == 0.995
    assert raw["search_n_decisive"] == 200
    assert raw["search_n_same_policy"] == 0
    assert raw["canary_ply1"] == "e2e7"
    assert raw["canary_ply2"] == "e2b5"
    assert raw["mix1_real_hz"] == 0.0
    assert raw["mix1_real_pearson"] == 0.0
    assert raw["three_ply_is_lock"] is False
    assert raw["promote_shuffle_seed_5"] is False
    assert raw["restamp_abc"] is False
    assert raw["restamp_ethology"] is False
    assert raw["elo"] is None
    assert eth["real"]["score"] == 0.4875
    assert eth["n_games"] == 40
    assert planes["n_games"] == 40
    assert a["A"]["games"]["score"] == 0.91
    assert a["wiring_helped"] is False
    assert search["two_vs_one"]["score_decisive"] == 0.995
    assert mix1["real"]["silent"] is True
    assert mix1["wiring_helped"] is False
    src = (REPO / "README.md").read_text(encoding="utf-8")
    assert src.count("wiring_helped") >= 1
    assert "0.225" not in src
