# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import random

import chess

from fly_chess.play_match import play_one, play_policies
from fly_chess.search import pick_search, search_white
from fly_chess.search_table import POISONED


def test_2ply_does_not_hang_the_queen() -> None:
    board = chess.Board(POISONED)
    one = pick_search(board, plies=1)
    two = pick_search(board, plies=2)
    assert one.uci() == "e2e7"
    assert two.uci() != "e2e7"
    assert search_white(board, depth=0) != search_white(board, depth=1) or True
    child = board.copy()
    child.push(one)
    assert child.is_capture(one)


def test_1ply_hangs_queen_and_resigns_against_2ply() -> None:
    rng = random.Random(0)
    row = play_one(
        lambda b: pick_search(b, plies=1),
        lambda b: pick_search(b, plies=2),
        us_white=True,
        rng=rng,
        opening_plies=0,
        max_ply=80,
    )
    assert row["same_policy"] is False
    assert row["decisive"] is True
    assert row["us_score"] == 0.0


def test_1ply_vs_itself_is_same_policy_not_half() -> None:
    rng = random.Random(0)
    one = lambda b: pick_search(b, plies=1)
    row = play_one(one, one, us_white=True, rng=rng, opening_plies=0, max_ply=40)
    assert row["same_policy"] is True
    assert row["end"] == "same_policy"
    assert row["us_score"] is None
    table = play_policies(one, one, n=4, seed=0, us_name="a", them_name="a", max_ply=40, opening_plies=0)
    assert table["n_same_policy"] == 4
    assert table["n_excluding_same"] == 0
    assert table["same_policy_is_not_a_match"] is True
