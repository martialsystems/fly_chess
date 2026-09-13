# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_search_lock_beats_1ply_and_does_not_call_same_policy_a_draw() -> None:
    raw = json.loads((REPO / "logs" / "search_lock.json").read_text(encoding="utf-8"))
    eth = json.loads((REPO / "logs" / "ethology_gate.json").read_text(encoding="utf-8"))
    two = raw["two_vs_one"]
    one = raw["one_vs_one_control"]
    assert raw["new_head"] is False
    assert raw["distill_is_A"] is True
    assert raw["canary"]["search_differs_from_1ply"] is True
    assert raw["canary"]["ply1"] == "e2e7"
    assert raw["canary"]["ply2"] != "e2e7"
    assert two["n_games"] == 200
    assert two["n_decisive"] == 200
    assert two["n_same_policy"] == 0
    assert two["score_decisive"] == 0.995
    assert two["same_policy_is_not_a_match"] is True
    assert one["n_same_policy"] == 200
    assert one["n_excluding_same"] == 0
    assert raw["three_vs_one"]["n_games"] == 40
    assert raw["three_vs_one"]["score_decisive"] == 1.0
    assert eth["real"]["score"] == 0.4875
    assert raw["unfreeze_allowed"] is False
    assert raw["elo"] is None


def test_mix1_child_distill_lock_does_not_help() -> None:
    raw = json.loads((REPO / "logs" / "mix1_distill.json").read_text(encoding="utf-8"))
    a = json.loads((REPO / "logs" / "value_lock.json").read_text(encoding="utf-8"))
    assert raw["real"]["silent"] is True
    assert raw["real"]["held_out"]["pearson"] == 0.0
    assert raw["real"]["vs_A"]["n_games"] == 200
    assert raw["real"]["vs_A"]["score_decisive"] == 0.025
    assert raw["shuffle"]["seeds"] == [1, 2, 3, 4, 5]
    assert raw["wiring_helped"] is False
    assert raw["unfreeze_allowed"] is False
    assert a["A"]["games"]["score"] == 0.91
    assert a["wiring_helped"] is False
