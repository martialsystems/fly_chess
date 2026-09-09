# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import chess


def legal_moves(board: chess.Board) -> list[chess.Move]:
    return list(board.legal_moves)


def apply_legal(board: chess.Board, move: chess.Move) -> chess.Move:
    if move not in board.legal_moves:
        raise ValueError(f"illegal move {move.uci()}")
    return move


def leaves_in_check(board: chess.Board, move: chess.Move) -> bool:
    board.push(move)
    check = board.is_check()
    board.pop()
    return check


def escapes_check(board: chess.Board, move: chess.Move) -> bool:
    if not board.is_check():
        return False
    board.push(move)
    still = board.is_check()
    board.pop()
    return not still


def never_null(move: chess.Move | None, legal: list[chess.Move]) -> chess.Move:
    if move is None or move not in legal:
        if not legal:
            raise ValueError("no legal moves")
        return legal[0]
    return move
