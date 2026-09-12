# Copyright (c) 2026 Martial Systems LLC
"""White-centric cheap eval. No engine. Target for the value heads."""

from __future__ import annotations

import chess

MATE = 100.0
PIECE_PAWNS = {
    chess.PAWN: 1.0,
    chess.KNIGHT: 3.0,
    chess.BISHOP: 3.0,
    chess.ROOK: 5.0,
    chess.QUEEN: 9.0,
    chess.KING: 0.0,
}

# White-view pawn-unit PST, indexed by square 0..63.
_PAWN = (
    0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00,
    0.05, 0.05, 0.05, 0.00, 0.00, 0.05, 0.05, 0.05,
    0.05, 0.00, 0.10, 0.15, 0.15, 0.10, 0.00, 0.05,
    0.00, 0.05, 0.15, 0.25, 0.25, 0.15, 0.05, 0.00,
    0.05, 0.10, 0.20, 0.30, 0.30, 0.20, 0.10, 0.05,
    0.10, 0.20, 0.25, 0.35, 0.35, 0.25, 0.20, 0.10,
    0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50,
    0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00,
)
_KNIGHT = (
    -0.40, -0.20, -0.10, -0.10, -0.10, -0.10, -0.20, -0.40,
    -0.20, 0.00, 0.05, 0.10, 0.10, 0.05, 0.00, -0.20,
    -0.10, 0.05, 0.15, 0.20, 0.20, 0.15, 0.05, -0.10,
    -0.10, 0.10, 0.20, 0.25, 0.25, 0.20, 0.10, -0.10,
    -0.10, 0.10, 0.20, 0.25, 0.25, 0.20, 0.10, -0.10,
    -0.10, 0.05, 0.15, 0.20, 0.20, 0.15, 0.05, -0.10,
    -0.20, 0.00, 0.05, 0.10, 0.10, 0.05, 0.00, -0.20,
    -0.40, -0.20, -0.10, -0.10, -0.10, -0.10, -0.20, -0.40,
)
_KING = (
    0.20, 0.30, 0.10, 0.00, 0.00, 0.10, 0.30, 0.20,
    0.20, 0.20, 0.00, 0.00, 0.00, 0.00, 0.20, 0.20,
    -0.10, -0.20, -0.20, -0.20, -0.20, -0.20, -0.20, -0.10,
    -0.20, -0.30, -0.30, -0.40, -0.40, -0.30, -0.30, -0.20,
    -0.30, -0.40, -0.40, -0.50, -0.50, -0.40, -0.40, -0.30,
    -0.30, -0.40, -0.40, -0.50, -0.50, -0.40, -0.40, -0.30,
    -0.30, -0.40, -0.40, -0.50, -0.50, -0.40, -0.40, -0.30,
    -0.30, -0.40, -0.40, -0.50, -0.50, -0.40, -0.40, -0.30,
)


def _pst(piece: chess.Piece, square: int) -> float:
    sq = square if piece.color == chess.WHITE else chess.square_mirror(square)
    if piece.piece_type == chess.PAWN:
        return _PAWN[sq]
    if piece.piece_type == chess.KNIGHT:
        return _KNIGHT[sq]
    if piece.piece_type == chess.KING:
        return _KING[sq]
    return 0.0


def is_drawish(board: chess.Board) -> bool:
    return bool(
        board.is_stalemate()
        or board.is_insufficient_material()
        or board.can_claim_draw()
    )


def hand_eval(board: chess.Board) -> float:
    """Pawn units, White positive. Mate is terminal for the side to move."""
    if board.is_checkmate():
        return -MATE if board.turn == chess.WHITE else MATE
    if is_drawish(board):
        return 0.0
    score = 0.0
    for sq, piece in board.piece_map().items():
        val = PIECE_PAWNS[piece.piece_type] + _pst(piece, sq)
        score += val if piece.color == chess.WHITE else -val
    return float(score)


def phase_name(board: chess.Board) -> str:
    n = len(board.piece_map())
    if board.fullmove_number <= 8:
        return "opening"
    if n >= 16:
        return "middlegame"
    return "simple"
