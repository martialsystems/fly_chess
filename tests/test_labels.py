# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import json
from pathlib import Path

import chess

from fly_chess.labels import (
    check_escape_family,
    hanging_family,
    load_labels_split,
    teacher_move,
)
from fly_chess.puzzles import labeled_positions

REPO = Path(__file__).resolve().parents[1]


def test_teacher_is_deterministic_and_has_no_engine() -> None:
    board = chess.Board("4k3/8/8/3n4/8/8/8/3QK3 w - - 0 1")
    a = teacher_move(board)
    b = teacher_move(board)
    assert a is not None and a == b
    assert a.uci() == "d1d5"
    src = (REPO / "src" / "fly_chess" / "labels.py").read_text(encoding="utf-8")
    assert "stockfish" not in src.lower()


def test_hanging_family_is_current_catalog() -> None:
    hanging = hanging_family()
    catalog = [b.fen() for b, _m, k in labeled_positions() if k == "hanging"]
    assert set(b.fen() for b, _m, _k in hanging) <= set(catalog)
    assert len(hanging) == 165


def test_labels_split_has_no_overlap() -> None:
    split = load_labels_split()
    assert set(split["train"]).isdisjoint(split["eval"])
    assert len(split["train"]) >= 80
    assert len(split["eval"]) >= 40
    assert len(check_escape_family()) >= 40


def test_labels_lock_does_not_touch_old_objects() -> None:
    path = REPO / "logs" / "planes_labels.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["games"] == 0
    assert raw["elo"] is None
    assert raw["gate2_quoted"] is False
    assert raw["ethology_rerun"] is False
    assert raw["planes_head_untouched"] is True
    assert raw["encoder_frozen"] is True
    assert [r["mix_plies"] for r in raw["rows"]] == [0, 1, 3]
    t0 = raw["rows"][0]["families"]["teacher"]["factored"]["real_acc"]
    t1 = raw["rows"][1]["families"]["teacher"]["factored"]["real_acc"]
    assert t0 >= 0.5
    assert t1 < t0
    assert "occupancy register" in raw["pass_fail"]["verdict"]
    eth = json.loads((REPO / "logs" / "ethology_gate.json").read_text(encoding="utf-8"))
    assert eth["real"]["score"] == 0.4875
    pointer = json.loads((REPO / "logs" / "planes_head.json").read_text(encoding="utf-8"))
    assert pointer["n_eval"] == 10
    assert pointer["real_mean_target_rank"] == 3.9
    planes = json.loads((REPO / "logs" / "planes_gate.json").read_text(encoding="utf-8"))
    assert planes["n_games"] == 40
