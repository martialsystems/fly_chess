# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import chess


def hanging_enemy_squares(board: chess.Board, us: chess.Color) -> list[int]:
    out: list[int] = []
    for sq, piece in board.piece_map().items():
        if piece.color == us:
            continue
        attackers = board.attackers(us, sq)
        defenders = board.attackers(not us, sq)
        if attackers and not defenders:
            out.append(sq)
    return out


def hanging_own_squares(board: chess.Board, us: chess.Color) -> list[int]:
    out: list[int] = []
    for sq, piece in board.piece_map().items():
        if piece.color != us:
            continue
        attackers = board.attackers(not us, sq)
        defenders = board.attackers(us, sq)
        if attackers and not defenders:
            out.append(sq)
    return out


def king_square(board: chess.Board, us: chess.Color) -> int:
    sq = board.king(us)
    if sq is None:
        raise ValueError("king missing")
    return sq


def open_files_to_king(board: chess.Board, us: chess.Color) -> list[int]:
    king = king_square(board, us)
    kfile = chess.square_file(king)
    own_pawns = [
        sq
        for sq, p in board.piece_map().items()
        if p.color == us and p.piece_type == chess.PAWN and chess.square_file(sq) == kfile
    ]
    if own_pawns:
        return []
    return [chess.square(kfile, r) for r in range(8)]


def passed_pawns(board: chess.Board, us: chess.Color) -> list[int]:
    out: list[int] = []
    them = not us
    for sq, piece in board.piece_map().items():
        if piece.color != us or piece.piece_type != chess.PAWN:
            continue
        f = chess.square_file(sq)
        r = chess.square_rank(sq)
        blocked = False
        ranks = range(r + 1, 8) if us == chess.WHITE else range(r - 1, -1, -1)
        for rr in ranks:
            for ff in (f - 1, f, f + 1):
                if 0 <= ff <= 7:
                    p = board.piece_at(chess.square(ff, rr))
                    if p and p.color == them and p.piece_type == chess.PAWN:
                        blocked = True
        if not blocked:
            out.append(sq)
    return out


def poisoned_captures(board: chess.Board, us: chess.Color) -> list[int]:
    """Recapture bait: we can capture, they recapture with a cheaper or equal piece still attacking."""
    out: list[int] = []
    for move in board.legal_moves:
        if not board.is_capture(move):
            continue
        dest = move.to_square
        if board.attackers(not us, dest):
            out.append(dest)
    return sorted(set(out))
