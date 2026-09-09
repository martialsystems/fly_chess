# Copyright (c) 2026 Martial Systems LLC
"""Frozen verb dictionary: named DN/MN rates to a legal chess move."""

from __future__ import annotations

import json

import chess
import numpy as np

from fly_chess.board_feats import hanging_enemy_squares, hanging_own_squares
from fly_chess.graph import Graph
from fly_chess.mask import escapes_check, legal_moves, never_null
from fly_chess.paint import load_paint_cfg, locus_rates
from fly_chess.paths import CONFIG
from fly_chess.rates import mean_hz
from fly_chess.resolve import Resolved


def load_verbs_cfg() -> dict:
    return json.loads((CONFIG / "verbs.json").read_text(encoding="utf-8"))


def cluster_rates(hz: np.ndarray, resolved: Resolved) -> dict[str, float]:
    return {
        "feed_mn": mean_hz(hz, resolved.roles.get("feed_mn") or []),
        "gf_escape": mean_hz(hz, resolved.roles.get("gf_escape") or []),
        "aversive_grn": mean_hz(hz, resolved.roles.get("aversive_grn") or []),
        "walk_back": mean_hz(hz, resolved.roles.get("walk_back") or []),
        "walk_fwd": mean_hz(hz, resolved.roles.get("walk_fwd") or []),
        "halt": mean_hz(hz, resolved.roles.get("halt") or []),
        "steer_l": mean_hz(hz, resolved.roles.get("steer_l") or []),
        "steer_r": mean_hz(hz, resolved.roles.get("steer_r") or []),
    }


def choose_move(
    board: chess.Board,
    graph: Graph,
    resolved: Resolved,
    hz: np.ndarray,
    *,
    paint_cfg: dict | None = None,
) -> tuple[chess.Move, str]:
    paint_cfg = paint_cfg or load_paint_cfg()
    legal = legal_moves(board)
    if not legal:
        raise ValueError("no legal moves")
    clusters = cluster_rates(hz, resolved)
    app = locus_rates(graph, resolved, hz, "APP_LOCUS")
    av = locus_rates(graph, resolved, hz, "AV_LOCUS")
    us = board.turn

    verb = _arbitrate(board, clusters, paint_cfg)
    candidates = _class_moves(board, legal, verb, us)
    if not candidates:
        verb = "quiet"
        candidates = _class_moves(board, legal, "quiet", us)
    if not candidates:
        candidates = legal
    chosen = _steer_or_peak(board, candidates, verb, clusters, app, av, paint_cfg)
    return never_null(chosen, legal), verb


def _arbitrate(board: chess.Board, clusters: dict[str, float], cfg: dict) -> str:
    in_check = board.is_check()
    if in_check and clusters["gf_escape"] >= cfg["flee_threshold_hz"]:
        return "flee"
    if clusters["feed_mn"] >= cfg["capture_threshold_hz"]:
        if clusters["aversive_grn"] >= cfg["reject_threshold_hz"]:
            return "reject"
        return "capture"
    if clusters["walk_back"] >= cfg["retreat_threshold_hz"] and hanging_own_squares(board, board.turn):
        return "retreat"
    if clusters["walk_fwd"] >= cfg["advance_threshold_hz"]:
        return "advance"
    return "quiet"


def _class_moves(
    board: chess.Board,
    legal: list[chess.Move],
    verb: str,
    us: chess.Color,
) -> list[chess.Move]:
    if verb == "flee":
        esc = [m for m in legal if escapes_check(board, m)]
        return esc or legal
    if verb == "capture":
        hanging = set(hanging_enemy_squares(board, us))
        caps = [m for m in legal if board.is_capture(m) and m.to_square in hanging]
        if caps:
            return caps
        return [m for m in legal if board.is_capture(m)]
    if verb == "reject":
        poisoned = {m.to_square for m in legal if board.is_capture(m) and board.attackers(not us, m.to_square)}
        caps = [m for m in legal if board.is_capture(m) and m.to_square not in poisoned]
        return caps or [m for m in legal if not board.is_capture(m)]
    if verb == "retreat":
        hanging = set(hanging_own_squares(board, us))
        ret = [m for m in legal if m.from_square in hanging]
        return ret
    if verb == "advance":
        return [
            m
            for m in legal
            if board.piece_at(m.from_square)
            and board.piece_at(m.from_square).piece_type == chess.PAWN
            and not board.is_capture(m)
        ]
    quiet = [m for m in legal if not board.is_capture(m) and not _gives_check(board, m)]
    return quiet or legal


def _gives_check(board: chess.Board, move: chess.Move) -> bool:
    board.push(move)
    chk = board.is_check()
    board.pop()
    return chk


def _steer_or_peak(
    board: chess.Board,
    candidates: list[chess.Move],
    verb: str,
    clusters: dict[str, float],
    app: np.ndarray,
    av: np.ndarray,
    cfg: dict,
) -> chess.Move:
    if verb in ("capture", "advance"):
        scores = [float(app[m.to_square]) for m in candidates]
        best = max(scores) if scores else 0.0
        top = [m for m, s in zip(candidates, scores) if s == best]
        return _steer(top, clusters, cfg)
    if verb == "flee":
        scores = []
        for m in candidates:
            src = float(av[m.from_square])
            dst = float(av[m.to_square])
            scores.append(src - dst)
        best = max(scores) if scores else 0.0
        top = [m for m, s in zip(candidates, scores) if s == best]
        return _steer(top, clusters, cfg)
    if verb == "retreat":
        scores = [float(av[m.from_square]) for m in candidates]
        best = max(scores) if scores else 0.0
        top = [m for m, s in zip(candidates, scores) if s == best]
        return _steer(top, clusters, cfg)
    return _steer(candidates, clusters, cfg)


def _steer(moves: list[chess.Move], clusters: dict[str, float], cfg: dict) -> chess.Move:
    if len(moves) == 1:
        return moves[0]
    diff = clusters["steer_r"] - clusters["steer_l"]
    if abs(diff) < cfg["steer_diff_hz"]:
        return moves[0]
    prefer_right = diff > 0
    sided = [
        m
        for m in moves
        if (chess.square_file(m.to_square) >= 4) == prefer_right
    ]
    return sided[0] if sided else moves[0]
