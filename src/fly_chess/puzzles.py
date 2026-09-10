# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import json

import chess

from fly_chess.paths import CONFIG

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

RECAPTURE = [
    ("4k3/8/8/3n4/4P3/8/8/4K3 w - - 0 1", "e4d5"),
    ("4k3/8/8/4p3/3P4/8/8/4K3 w - - 0 1", "d4e5"),
    ("4k3/8/8/8/3n4/8/8/3RK3 w - - 0 1", "d1d4"),
]

CHECK_ESCAPE = [
    ("4k3/8/8/8/8/8/4r3/4K3 w - - 0 1", "e1e2"),
    ("4k3/8/8/8/8/4q3/8/4K3 w - - 0 1", "e1d1"),
    ("4k3/8/8/8/8/8/3b4/4K3 w - - 0 1", "e1d2"),
]

FORK = [
    ("8/8/1q3k2/3N4/8/8/8/4K3 w - - 0 1", "d5b6"),
    ("4k3/8/3q4/5N2/8/8/8/4K3 w - - 0 1", "f5d6"),
]

DONT_HANG_QUEEN = [
    ("4k3/8/2n5/3n4/8/8/8/3QK3 w - - 0 1", "d1d5"),
]


def _all_raw() -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for fen, uci in HANGING:
        rows.append((fen, uci, "hanging"))
    for fen, uci in MATE_IN_ONE:
        rows.append((fen, uci, "mate"))
    for fen, uci in RECAPTURE:
        rows.append((fen, uci, "recapture"))
    for fen, uci in CHECK_ESCAPE:
        rows.append((fen, uci, "check_escape"))
    for fen, uci in FORK:
        rows.append((fen, uci, "fork"))
    for fen, uci in DONT_HANG_QUEEN:
        rows.append((fen, uci, "hanging"))
    return rows


def labeled_positions() -> list[tuple[chess.Board, chess.Move, str]]:
    out: list[tuple[chess.Board, chess.Move, str]] = []
    for fen, uci, kind in _all_raw():
        board = chess.Board(fen)
        move = chess.Move.from_uci(uci)
        if move not in board.legal_moves:
            raise ValueError(f"bad puzzle {fen} {uci}")
        if kind == "mate":
            b2 = board.copy()
            b2.push(move)
            if not b2.is_checkmate():
                raise ValueError(f"not mate {fen} {uci}")
        elif kind == "check_escape":
            if not board.is_check():
                raise ValueError(f"not in check {fen}")
            b2 = board.copy()
            b2.push(move)
            if b2.is_check():
                raise ValueError(f"escape still in check {fen} {uci}")
        elif kind in ("hanging", "recapture", "fork"):
            if not board.is_capture(move):
                raise ValueError(f"{kind} is not a capture {fen} {uci}")
        out.append((board, move, kind))
    return out


def load_split() -> dict:
    return json.loads((CONFIG / "planes_split.json").read_text(encoding="utf-8"))


def _by_fen() -> dict[str, tuple[chess.Board, chess.Move, str]]:
    out: dict[str, tuple[chess.Board, chess.Move, str]] = {}
    for board, move, kind in labeled_positions():
        fen = board.fen()
        if fen not in out:
            out[fen] = (board, move, kind)
    return out


def split_positions(*, arm: str) -> list[tuple[chess.Board, chess.Move, str]]:
    split = load_split()
    fens = split[arm]
    catalog = _by_fen()
    missing = [fen for fen in fens if fen not in catalog]
    if missing:
        raise ValueError(f"split {arm} FENs missing from catalog: {missing[:3]}")
    overlap = set(split["train"]) & set(split["eval"])
    if overlap:
        raise ValueError(f"train/eval FEN overlap: {sorted(overlap)[:3]}")
    return [catalog[fen] for fen in fens]


def check_escape_position() -> chess.Board:
    return chess.Board("4k3/8/8/8/8/8/4r3/4K3 w - - 0 1")
