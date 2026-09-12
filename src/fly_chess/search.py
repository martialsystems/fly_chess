# Copyright (c) 2026 Martial Systems LLC
"""White-centric d-ply search over hand_eval. Graph unused."""

from __future__ import annotations

import chess

from fly_chess.hand_eval import MATE, hand_eval, is_drawish
from fly_chess.mask import legal_moves


def search_white(board: chess.Board, *, depth: int) -> float:
    """Pawn units, White positive. depth 0 is hand_eval. depth 1 is one extra ply."""
    if board.is_checkmate():
        return -MATE if board.turn == chess.WHITE else MATE
    if is_drawish(board):
        return 0.0
    if depth <= 0:
        return hand_eval(board)
    us = board.turn
    best = -1e18 if us == chess.WHITE else 1e18
    for move in legal_moves(board):
        board.push(move)
        v = search_white(board, depth=depth - 1)
        board.pop()
        if us == chess.WHITE:
            if v > best:
                best = v
        elif v < best:
            best = v
    return float(best)
