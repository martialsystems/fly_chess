# Copyright (c) 2026 Martial Systems LLC
"""Linear legal-move head. Graph stays frozen. Only this matrix trains."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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

    def rank(self, board: chess.Board, feat: np.ndarray, target: chess.Move) -> int:
        legal = legal_moves(board)
        log = self.logits(feat)
        scored = sorted(legal, key=lambda m: float(log[move_index(m)]), reverse=True)
        try:
            return scored.index(target) + 1
        except ValueError:
            return len(scored) + 1

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez(path, w=self.w, b=self.b)

    @classmethod
    def load(cls, path: Path) -> "LinearHead":
        blob = np.load(path)
        return cls(w=np.asarray(blob["w"], dtype=np.float64), b=np.asarray(blob["b"], dtype=np.float64))


@dataclass
class FactoredHead:
    """64 from-logits plus 64 to-logits. Legal mask on the pair. Not a bigger W."""

    w_from: np.ndarray
    w_to: np.ndarray
    b_from: np.ndarray
    b_to: np.ndarray

    @classmethod
    def zeros(cls, n_feat: int) -> "FactoredHead":
        rng = np.random.default_rng(0)
        return cls(
            w_from=rng.normal(0.0, 0.01, size=(64, n_feat)),
            w_to=rng.normal(0.0, 0.01, size=(64, n_feat)),
            b_from=np.zeros(64, dtype=np.float64),
            b_to=np.zeros(64, dtype=np.float64),
        )

    def score(self, feat: np.ndarray, move: chess.Move) -> float:
        lf = self.w_from @ feat + self.b_from
        lt = self.w_to @ feat + self.b_to
        return float(lf[move.from_square] + lt[move.to_square])

    def pick(self, board: chess.Board, feat: np.ndarray) -> chess.Move:
        legal = legal_moves(board)
        scored = [(self.score(feat, m), m) for m in legal]
        return never_null(max(scored, key=lambda t: t[0])[1], legal)

    def train_step(
        self,
        feat: np.ndarray,
        target: chess.Move,
        board: chess.Board,
        *,
        lr: float = 0.05,
    ) -> None:
        legal = legal_moves(board)
        scores = np.array([self.score(feat, m) for m in legal], dtype=np.float64)
        scores = scores - np.max(scores)
        p = np.exp(scores)
        p = p / np.sum(p)
        g_from = np.zeros(64, dtype=np.float64)
        g_to = np.zeros(64, dtype=np.float64)
        for prob, m in zip(p.tolist(), legal):
            g_from[m.from_square] += prob
            g_to[m.to_square] += prob
        g_from[target.from_square] -= 1.0
        g_to[target.to_square] -= 1.0
        self.w_from -= lr * np.outer(g_from, feat)
        self.w_to -= lr * np.outer(g_to, feat)
        self.b_from -= lr * g_from
        self.b_to -= lr * g_to

    def rank(self, board: chess.Board, feat: np.ndarray, target: chess.Move) -> int:
        legal = legal_moves(board)
        scored = sorted(legal, key=lambda m: self.score(feat, m), reverse=True)
        try:
            return scored.index(target) + 1
        except ValueError:
            return len(scored) + 1
