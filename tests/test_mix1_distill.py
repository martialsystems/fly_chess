# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import json
from pathlib import Path

from fly_chess.mix1_distill import run_mix1_distill
from fly_chess.search_table import run_search_table
from fly_chess.session import open_session
from fly_chess.value_feats import graph_fingerprint

REPO = Path(__file__).resolve().parents[1]


def test_tiny_search_table_canary() -> None:
    payload = run_search_table(tiny=True, n=4)
    assert payload["new_head"] is False
    assert payload["distill_is_A"] is True
    assert payload["canary"]["ply1_takes_e7"] is True
    assert payload["canary"]["ply2_avoids_e7"] is True
    assert payload["canary"]["search_differs_from_1ply"] is True
    assert payload["one_vs_one_control"]["n_same_policy"] == payload["one_vs_one_control"]["n_games"]
    assert payload["one_vs_one_control"]["same_policy_is_not_a_match"] is True
    assert payload["unfreeze_allowed"] is False


def test_tiny_mix1_distill_keeps_shuffle_and_freeze() -> None:
    session = open_session(source="fixture")
    fp = graph_fingerprint(session)
    payload = run_mix1_distill(tiny=True, n_play=0)
    assert payload["child_label"] == "hand_eval"
    assert payload["features"] == "hidden_64_after_one_ply"
    assert payload["shuffle"]["seeds"] == [1, 2, 3, 4, 5]
    assert payload["unfreeze_allowed"] is False
    assert payload["wiring_helped"] is False
    assert payload["fingerprint"] == fp
    eth = json.loads((REPO / "logs" / "ethology_gate.json").read_text(encoding="utf-8"))
    assert eth["real"]["score"] == 0.4875
    d = json.loads((REPO / "logs" / "value_distill.json").read_text(encoding="utf-8"))
    assert d["distill_vs_random"]["score"] == 0.905
    assert d["outcome"]["vs_2ply_search"]["score"] == 0.0
