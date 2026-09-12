# Copyright (c) 2026 Martial Systems LLC
"""1-ply child scoring. Enumerate legal moves, score the child, pick the max."""

from __future__ import annotations

from collections.abc import Callable

import chess
import numpy as np

from fly_chess.hand_eval import MATE, hand_eval, is_drawish
from fly_chess.mask import legal_moves, never_null

ScoreFn = Callable[[chess.Board], float]


def score_after_move(board: chess.Board, move: chess.Move, score_white: ScoreFn) -> float:
    """Mover-perspective score of the child. Positive is good for the side about to move."""
    us = board.turn
    board.push(move)
    if board.is_checkmate():
        s_white = -MATE if board.turn == chess.WHITE else MATE
    elif is_drawish(board):
        s_white = 0.0
    else:
        s_white = float(score_white(board))
    board.pop()
    return s_white if us == chess.WHITE else -s_white


def pick_child(board: chess.Board, score_white: ScoreFn) -> chess.Move:
    legal = legal_moves(board)
    best_m = legal[0]
    best_s = -1e18
    best_uci = best_m.uci()
    for move in legal:
        s = score_after_move(board, move, score_white)
        uci = move.uci()
        if s > best_s or (s == best_s and uci < best_uci):
            best_s = s
            best_m = move
            best_uci = uci
    return never_null(best_m, legal)


def child_table(board: chess.Board, score_white: ScoreFn) -> list[tuple[chess.Move, float, float]]:
    """(move, mover_score, white_eval_of_child) for every legal child."""
    rows: list[tuple[chess.Move, float, float]] = []
    us = board.turn
    for move in legal_moves(board):
        board.push(move)
        y_white = hand_eval(board)
        board.pop()
        s = y_white if us == chess.WHITE else -y_white
        pred = score_after_move(board, move, score_white)
        rows.append((move, pred, s))
    return rows


def pairwise_agree(pred: np.ndarray, target: np.ndarray) -> float:
    """Fraction of child pairs whose ranking sign matches the target."""
    n = pred.size
    if n < 2:
        return 1.0
    hits = 0
    tot = 0
    for i in range(n):
        for j in range(i + 1, n):
            dp = pred[i] - pred[j]
            dt = target[i] - target[j]
            if abs(dt) < 1e-12:
                continue
            tot += 1
            if dp * dt > 0:
                hits += 1
    return hits / tot if tot else 1.0
