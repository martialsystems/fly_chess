# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import json
from pathlib import Path

import chess
import pytest

from fly_chess.cli import main
from fly_chess.distill_value import play_ava_positions, run_distill
from fly_chess.hand_eval import hand_eval
from fly_chess.search import search_white
from fly_chess.session import open_session
from fly_chess.value_feats import graph_fingerprint

REPO = Path(__file__).resolve().parents[1]
HANGING_Q = "4k3/8/8/3q4/8/8/8/3QK3 w - - 0 1"


def test_search_takes_mate_in_one() -> None:
    from fly_chess.child_value import pick_child
    from fly_chess.hand_eval import MATE

    board = chess.Board("6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 1")
    assert search_white(board, depth=0) == hand_eval(board)
    assert search_white(board, depth=1) == MATE
    move = pick_child(board, lambda b: search_white(b, depth=0))
    assert move.uci() == "e1e8"


def test_ava_generator_plays_a_after_opening() -> None:
    src = (REPO / "src" / "fly_chess" / "distill_value.py").read_text(encoding="utf-8")
    assert "backup_white" not in src
    assert "play_labeled_game" not in src
    assert "pick_child(board, hand_eval)" in src
    rows = play_ava_positions(n_games=3, opening_plies=2, max_ply=8, seed=0)
    assert len({gid for gid, _ in rows}) == 3
    assert len(rows) >= 3


def test_cli_refuses_closed_chess_on_wiring_trainers() -> None:
    for stage in ("selfplay", "distill", "mix1-distill", "followup", "A", "all"):
        with pytest.raises(SystemExit) as err:
            main(["value", "--stage", stage])
        assert "closed" in str(err.value).lower()


def test_tiny_distill_labels_children_and_freezes_graph() -> None:
    session = open_session(source="fixture")
    fp = graph_fingerprint(session)
    payload = run_distill(tiny=True, n_play=0)
    assert payload["generator"] == "A_vs_A_after_random_opening"
    assert payload["child_label"] == "hand_eval"
    assert payload["not_truncated_return"] is True
    assert payload["held_out"]["n_children"] >= payload["held_out"]["n_parents"]
    assert payload["graph_frozen"] is True
    assert payload["synapses_used"] is False
    assert payload["wiring_helped"] is False
    assert payload["fingerprint"] == fp
    eth = json.loads((REPO / "logs" / "ethology_gate.json").read_text(encoding="utf-8"))
    assert eth["real"]["score"] == 0.4875
    sp = json.loads((REPO / "logs" / "value_selfplay.json").read_text(encoding="utf-8"))
    assert sp["selfplay_vs_random"]["score"] == 0.6075
    hang = chess.Board(HANGING_Q)
    assert search_white(hang, depth=0) == hand_eval(hang)
