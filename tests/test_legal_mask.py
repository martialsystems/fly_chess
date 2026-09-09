# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import chess

from fly_chess.head import LinearHead
from fly_chess.mask import legal_moves
from fly_chess.match import ethology_move, planes_move, play_ethology, play_planes_gate0
from fly_chess.planes import readout_vector
from fly_chess.session import open_session


def test_ethology_never_emits_illegal() -> None:
    report = play_ethology(n=4, opponent="random", seed=0)
    assert report["illegal"] == 0
    assert report["n_games"] == 4
    assert "Approach/avoid controller" in report["claim"]


def test_random_policy_legal_on_start() -> None:
    board = chess.Board()
    assert all(m in board.legal_moves for m in legal_moves(board))


def test_gate0_illegal_rate_zero() -> None:
    report = play_planes_gate0(n=16, seed=0)
    assert report["illegal"] == 0
    assert report["illegal_rate"] == 0.0
    assert "Piece-plane encoding" in report["claim"]


def test_head_mask_on_start_position() -> None:
    session = open_session()
    feat = readout_vector(__import__("numpy").zeros(session.graph.n), session.resolved)
    head = LinearHead.zeros(len(feat))
    board = chess.Board()
    move = planes_move(session, board, head)
    assert move in board.legal_moves
    move2, verb = ethology_move(session, board)
    assert move2 in board.legal_moves
    assert verb in {"flee", "capture", "reject", "retreat", "advance", "quiet"}
