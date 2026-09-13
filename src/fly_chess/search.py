# Copyright (c) 2026 Martial Systems LLC
"""White-centric d-ply alpha-beta over hand_eval. Graph unused."""

from __future__ import annotations

import chess

from fly_chess.hand_eval import MATE, PIECE_PAWNS, hand_eval, is_drawish
from fly_chess.mask import legal_moves


def ordered_moves(board: chess.Board) -> list[chess.Move]:
    legal = legal_moves(board)
    caps: list[tuple[float, chess.Move]] = []
    quiet: list[chess.Move] = []
    for move in legal:
        vic = board.piece_at(move.to_square)
        if vic is not None or board.is_en_passant(move):
            val = PIECE_PAWNS.get(vic.piece_type, 1.0) if vic is not None else 1.0
            caps.append((-val, move))
        else:
            quiet.append(move)
    caps.sort(key=lambda t: (t[0], t[1].uci()))
    quiet.sort(key=lambda m: m.uci())
    return [m for _v, m in caps] + quiet


def search_white(
    board: chess.Board,
    *,
    depth: int,
    alpha: float = -1e9,
    beta: float = 1e9,
) -> float:
    """Pawn units, White positive. depth 0 is hand_eval."""
    if board.is_checkmate():
        return -MATE if board.turn == chess.WHITE else MATE
    if is_drawish(board):
        return 0.0
    if depth <= 0:
        return hand_eval(board)
    us = board.turn
    if us == chess.WHITE:
        best = -1e18
        for move in ordered_moves(board):
            board.push(move)
            v = search_white(board, depth=depth - 1, alpha=alpha, beta=beta)
            board.pop()
            if v > best:
                best = v
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return float(best)
    best = 1e18
    for move in ordered_moves(board):
        board.push(move)
        v = search_white(board, depth=depth - 1, alpha=alpha, beta=beta)
        board.pop()
        if v < best:
            best = v
        if best < beta:
            beta = best
        if alpha >= beta:
            break
    return float(best)


def pick_search(board: chess.Board, *, plies: int) -> chess.Move:
    """plies=1 is 1-ply hand-eval of the child. plies=2 searches one extra ply."""
    from fly_chess.child_value import pick_child

    extra = max(0, int(plies) - 1)

    def score(child: chess.Board) -> float:
        return search_white(child, depth=extra)

    return pick_child(board, score)
