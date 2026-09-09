# Copyright (c) 2026 Martial Systems LLC
"""Linear legal-move head. Graph stays frozen. Only this matrix trains."""

from __future__ import annotations

from dataclasses import dataclass

import chess
import numpy as np

from fly_chess.mask import legal_moves, never_null

N_MOVES = 64 * 64


def move_index(move: chess.Move) -> int:
    return move.from_square * 64 + move.to_square


def index_move(idx: int, board: chess.Board) -> chess.Move | None:
    frm, to = divmod(int(idx), 64)
    promo = None
    piece = board.piece_at(frm)
    if piece and piece.piece_type == chess.PAWN:
        to_rank = chess.square_rank(to)
        if to_rank in (0, 7):
            promo = chess.QUEEN
    move = chess.Move(frm, to, promotion=promo)
    if move in board.legal_moves:
        return move
    return None


@dataclass
class LinearHead:
    w: np.ndarray
    b: np.ndarray

    @classmethod
    def zeros(cls, n_feat: int) -> "LinearHead":
        rng = np.random.default_rng(0)
        w = rng.normal(0.0, 0.01, size=(N_MOVES, n_feat))
        b = np.zeros(N_MOVES, dtype=np.float64)
        return cls(w=w, b=b)

    def logits(self, feat: np.ndarray) -> np.ndarray:
        return self.w @ feat + self.b

    def pick(self, board: chess.Board, feat: np.ndarray) -> chess.Move:
        legal = legal_moves(board)
        log = self.logits(feat)
        mask = np.full(N_MOVES, -1e9, dtype=np.float64)
        for m in legal:
            mask[move_index(m)] = log[move_index(m)]
        idx = int(np.argmax(mask))
        move = index_move(idx, board)
        return never_null(move, legal)

    def train_step(
        self,
        feat: np.ndarray,
        target: chess.Move,
        board: chess.Board,
        *,
        lr: float = 0.05,
    ) -> None:
        log = self.logits(feat)
        legal_idx = np.array([move_index(m) for m in board.legal_moves], dtype=np.int32)
        sub = log[legal_idx]
        sub = sub - np.max(sub)
        p = np.exp(sub)
        p = p / np.sum(p)
        grad = np.zeros_like(log)
        grad[legal_idx] = p
        grad[move_index(target)] -= 1.0
        self.w -= lr * np.outer(grad, feat)
        self.b -= lr * grad
