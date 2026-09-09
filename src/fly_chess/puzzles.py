# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import chess

HANGING = [
    ("4k3/8/8/3n4/8/8/8/3QK3 w - - 0 1", "d1d5"),
    ("4k3/8/8/8/3r4/8/8/3RK3 w - - 0 1", "d1d4"),
    ("4k3/8/8/2b5/8/8/8/2Q1K3 w - - 0 1", "c1c5"),
    ("4k3/8/8/8/4q3/8/8/4QK2 w - - 0 1", "e1e4"),
    ("4k3/8/8/5n2/8/8/8/5QK1 w - - 0 1", "f1f5"),
    ("4k3/8/8/6b1/8/8/8/6QK w - - 0 1", "g1g5"),
    ("k7/8/8/n7/8/8/8/Q3K3 w - - 0 1", "a1a5"),
    ("4k3/8/8/1n6/8/8/8/1Q2K3 w - - 0 1", "b1b5"),
    ("4k3/8/3n4/8/8/8/8/3QK3 w - - 0 1", "d1d6"),
    ("4k3/8/8/8/8/3n4/8/3QK3 w - - 0 1", "d1d3"),
    ("4k3/8/8/8/2q5/8/8/2Q1K3 w - - 0 1", "c1c4"),
    ("4k3/8/8/8/5r2/8/8/5RK1 w - - 0 1", "f1f4"),
    ("4k3/8/8/4b3/8/8/8/4QK2 w - - 0 1", "e1e5"),
    ("k7/8/8/8/n7/8/8/Q3K3 w - - 0 1", "a1a4"),
    ("4k3/8/8/8/6n1/8/8/6QK w - - 0 1", "g1g4"),
    ("4k3/8/1n6/8/8/8/8/1Q2K3 w - - 0 1", "b1b6"),
]

MATE_IN_ONE = [
    ("6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 1", "e1e8"),
    ("6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1", "a1a8"),
    ("5k2/4Q3/5K2/8/8/8/8/8 w - - 0 1", "e7f7"),
    ("7k/5Q2/6K1/8/8/8/8/8 w - - 0 1", "f7g7"),
    ("7k/6Q1/6K1/8/8/8/8/8 w - - 0 1", "g7h7"),
    ("6k1/5Q2/6K1/8/8/8/8/8 w - - 0 1", "f7g7"),
    ("6k1/4Qppp/8/8/8/8/8/4K3 w - - 0 1", "e7e8"),
    ("6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1", "d1d8"),
    ("6k1/5ppp/8/8/8/8/5PPP/2R3K1 w - - 0 1", "c1c8"),
    ("6k1/5ppp/8/8/8/8/5PPP/1R4K1 w - - 0 1", "b1b8"),
    ("7k/4Q1pp/8/8/8/8/8/4K3 w - - 0 1", "e7e8"),
    ("6k1/5ppp/8/8/8/8/6PP/4R2K w - - 0 1", "e1e8"),
    ("7k/5ppp/8/8/8/8/5PPP/R6K w - - 0 1", "a1a8"),
    ("6k1/4Q1pp/8/8/8/8/8/4K3 w - - 0 1", "e7e8"),
    ("6k1/4Qppp/8/8/8/8/8/6K1 w - - 0 1", "e7e8"),
    ("7k/5Q2/6K1/8/8/8/8/8 w - - 0 1", "f7f8"),
]


def labeled_positions() -> list[tuple[chess.Board, chess.Move, str]]:
    out: list[tuple[chess.Board, chess.Move, str]] = []
    for fen, uci in HANGING + MATE_IN_ONE:
        board = chess.Board(fen)
        move = chess.Move.from_uci(uci)
        if move not in board.legal_moves:
            raise ValueError(f"bad puzzle {fen} {uci}")
        kind = "mate" if (fen, uci) in MATE_IN_ONE else "hanging"
        if kind == "mate":
            b2 = board.copy()
            b2.push(move)
            if not b2.is_checkmate():
                raise ValueError(f"not mate {fen} {uci}")
        else:
            if not board.is_capture(move):
                raise ValueError(f"hanging puzzle is not a capture {fen} {uci}")
        out.append((board, move, kind))
    return out


def check_escape_position() -> chess.Board:
    """Us to move, in check, a legal escape exists."""
    return chess.Board("4k3/8/8/8/8/8/4r3/4K3 w - - 0 1")
