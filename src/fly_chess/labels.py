# Copyright (c) 2026 Martial Systems LLC
"""Label families from injected board facts. No engine. Encoder frozen."""

from __future__ import annotations

import json

import chess

from fly_chess.board_feats import hanging_enemy_squares
from fly_chess.paths import CONFIG
from fly_chess.puzzles import labeled_positions

PIECE_VALUE = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0,
}


def hanging_capture_move(board: chess.Board) -> chess.Move | None:
    us = board.turn
    hanging = hanging_enemy_squares(board, us)
    best: chess.Move | None = None
    best_val = -1
    best_uci = ""
    for sq in hanging:
        piece = board.piece_at(sq)
        if piece is None:
            continue
        val = PIECE_VALUE[piece.piece_type]
        for mv in board.legal_moves:
            if mv.to_square != sq or not board.is_capture(mv):
                continue
            uci = mv.uci()
            if val > best_val or (val == best_val and (best is None or uci < best_uci)):
                best = mv
                best_val = val
                best_uci = uci
    return best


def check_escape_move(board: chess.Board) -> chess.Move | None:
    if not board.is_check():
        return None
    escapes: list[chess.Move] = []
    for mv in board.legal_moves:
        b2 = board.copy()
        b2.push(mv)
        if not b2.is_check():
            escapes.append(mv)
    if not escapes:
        return None
    return sorted(escapes, key=lambda m: m.uci())[0]


def teacher_move(board: chess.Board) -> chess.Move | None:
    """Highest-value hanging capture, else any legal check-escape, else exclude."""
    hanging = hanging_capture_move(board)
    if hanging is not None:
        return hanging
    return check_escape_move(board)


def escapes_check(board: chess.Board, move: chess.Move) -> bool:
    if move not in board.legal_moves:
        return False
    b2 = board.copy()
    b2.push(move)
    return not b2.is_check()


def hanging_family() -> list[tuple[chess.Board, chess.Move, str]]:
    """Current hanging catalog only. No new hanging twins."""
    out: list[tuple[chess.Board, chess.Move, str]] = []
    seen: set[str] = set()
    for board, move, kind in labeled_positions():
        if kind != "hanging":
            continue
        fen = board.fen()
        if fen in seen:
            continue
        if hanging_capture_move(board) is None:
            continue
        seen.add(fen)
        out.append((board, move, "hanging"))
    return out


def _gen_check_escapes() -> list[tuple[chess.Board, chess.Move, str]]:
    """Us to move in check, a legal escape exists. Not hanging twins."""
    rows: list[tuple[chess.Board, chess.Move, str]] = []
    seen: set[str] = set()

    def add(board: chess.Board) -> None:
        if not board.is_check():
            return
        target = check_escape_move(board)
        if target is None:
            return
        fen = board.fen()
        if fen in seen:
            return
        seen.add(fen)
        rows.append((board, target, "check_escape"))

    for kind, symbol in ((chess.ROOK, "r"), (chess.QUEEN, "q"), (chess.BISHOP, "b")):
        for sq in range(64):
            if sq in (chess.E1, chess.E8):
                continue
            board = chess.Board()
            board.clear()
            board.set_piece_at(chess.E1, chess.Piece.from_symbol("K"))
            board.set_piece_at(chess.E8, chess.Piece.from_symbol("k"))
            board.set_piece_at(sq, chess.Piece(kind, chess.BLACK))
            board.turn = chess.WHITE
            add(board)
    for wk in (chess.D1, chess.F1, chess.E2, chess.D2, chess.F2):
        for sq in range(64):
            if sq in (wk, chess.E8):
                continue
            board = chess.Board()
            board.clear()
            board.set_piece_at(wk, chess.Piece.from_symbol("K"))
            board.set_piece_at(chess.E8, chess.Piece.from_symbol("k"))
            board.set_piece_at(sq, chess.Piece.from_symbol("r"))
            board.turn = chess.WHITE
            add(board)
    return rows


def check_escape_family() -> list[tuple[chess.Board, chess.Move, str]]:
    out: list[tuple[chess.Board, chess.Move, str]] = []
    seen: set[str] = set()
    for board, move, kind in labeled_positions():
        if kind != "check_escape":
            continue
        fen = board.fen()
        if fen in seen:
            continue
        target = check_escape_move(board)
        if target is None:
            continue
        seen.add(fen)
        out.append((board, target, "check_escape"))
    for board, move, kind in _gen_check_escapes():
        fen = board.fen()
        if fen in seen:
            continue
        seen.add(fen)
        out.append((board, move, kind))
    return out


def teacher_family(
    hanging: list[tuple[chess.Board, chess.Move, str]],
    escapes: list[tuple[chess.Board, chess.Move, str]],
) -> list[tuple[chess.Board, chess.Move, str]]:
    out: list[tuple[chess.Board, chess.Move, str]] = []
    seen: set[str] = set()
    for board, _old, _k in hanging + escapes:
        fen = board.fen()
        if fen in seen:
            continue
        target = teacher_move(board)
        if target is None:
            continue
        seen.add(fen)
        out.append((board.copy(), target, "teacher"))
    return out


def load_labels_split() -> dict:
    return json.loads((CONFIG / "planes_labels_split.json").read_text(encoding="utf-8"))


def family_split(
    rows: list[tuple[chess.Board, chess.Move, str]],
    *,
    arm: str,
) -> list[tuple[chess.Board, chess.Move, str]]:
    split = load_labels_split()
    want = set(split[arm])
    return [(b, m, k) for b, m, k in rows if b.fen() in want]
