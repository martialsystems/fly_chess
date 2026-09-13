# Copyright (c) 2026 Martial Systems LLC
"""Policy matches that do not call identical 80-ply greedy a 0.50 result."""

from __future__ import annotations

import random
from collections.abc import Callable

import chess

from fly_chess.hand_eval import hand_eval
from fly_chess.mask import legal_moves
from fly_chess.match import mean_interval, random_move

MAX_PLY = 400
RESIGN_PAWNS = 8.0
PickFn = Callable[[chess.Board], chess.Move]


def should_resign(board: chess.Board, us: chess.Color, *, thresh: float = RESIGN_PAWNS) -> bool:
    ev = hand_eval(board)
    if us == chess.WHITE:
        return ev <= -thresh
    return ev >= thresh


def play_one(
    pick_us: PickFn,
    pick_them: PickFn,
    *,
    us_white: bool,
    rng: random.Random,
    opening_plies: int = 0,
    max_ply: int = MAX_PLY,
    resign_pawns: float = RESIGN_PAWNS,
) -> dict:
    board = chess.Board()
    for _ in range(opening_plies):
        if board.is_game_over() or not any(board.legal_moves):
            break
        board.push(random_move(board, rng))
    us = chess.WHITE if us_white else chess.BLACK
    same = True
    ply = 0
    end = "cap"
    resign_score: float | None = None
    start_ev = hand_eval(board)

    def lost_material(side: chess.Color) -> bool:
        ev = hand_eval(board)
        if side == chess.WHITE:
            return ev <= start_ev - resign_pawns
        return ev >= start_ev + resign_pawns

    while not board.is_game_over() and ply < max_ply:
        if ply > 0 and lost_material(us):
            end = "resign"
            resign_score = 0.0
            break
        if ply > 0 and lost_material(not us):
            end = "resign"
            resign_score = 1.0
            break
        ours = pick_us(board)
        theirs = pick_them(board)
        if ours != theirs:
            same = False
        move = ours if board.turn == us else theirs
        if move not in board.legal_moves:
            move = legal_moves(board)[0]
        board.push(move)
        ply += 1
    if board.is_checkmate():
        end = "mate"
        winner = not board.turn
        us_score = 1.0 if winner == us else 0.0
    elif end == "resign":
        us_score = float(resign_score if resign_score is not None else 0.0)
    elif board.is_game_over():
        end = "draw"
        us_score = 0.5
    else:
        end = "cap"
        us_score = 0.5
    if same:
        return {
            "end": "same_policy",
            "same_policy": True,
            "ply": ply,
            "us_score": None,
            "decisive": False,
        }
    return {
        "end": end,
        "same_policy": same,
        "ply": ply,
        "us_score": us_score,
        "decisive": end in ("mate", "resign"),
    }


def play_policies(
    pick_us: PickFn,
    pick_them: PickFn,
    *,
    n: int,
    seed: int,
    opening_plies: int = 4,
    max_ply: int = MAX_PLY,
    resign_pawns: float = RESIGN_PAWNS,
    us_name: str,
    them_name: str,
) -> dict:
    if n <= 0:
        return {
            "n_games": 0,
            "n_decisive": 0,
            "n_same_policy": 0,
            "n_cap": 0,
            "score_decisive": None,
            "score_excluding_same": None,
            "same_policy_is_not_a_match": True,
            "us": us_name,
            "them": them_name,
            "max_ply": max_ply,
            "skipped": True,
            "elo": None,
        }
    rng = random.Random(seed)
    decisive_pts = 0.0
    n_dec = 0
    n_same = 0
    n_cap = 0
    n_draw = 0
    excl_pts = 0.0
    n_excl = 0
    ply_sum = 0
    for g in range(n):
        row = play_one(
            pick_us,
            pick_them,
            us_white=g % 2 == 0,
            rng=rng,
            opening_plies=int(rng.randint(0, max(0, opening_plies))),
            max_ply=max_ply,
            resign_pawns=resign_pawns,
        )
        ply_sum += int(row["ply"])
        if row["same_policy"] and row["end"] in ("same_policy", "cap", "draw"):
            n_same += 1
            continue
        n_excl += 1
        excl_pts += float(row["us_score"])
        if row["decisive"]:
            n_dec += 1
            decisive_pts += float(row["us_score"])
        elif row["end"] == "cap":
            n_cap += 1
        else:
            n_draw += 1
    def _mean(pts: float, k: int) -> float | None:
        return pts / k if k else None

    sc_ex = _mean(excl_pts, n_excl)
    lo, hi = mean_interval(sc_ex or 0.0, n_excl) if n_excl else (None, None)
    sc_dec = _mean(decisive_pts, n_dec)
    return {
        "n_games": n,
        "n_decisive": n_dec,
        "n_same_policy": n_same,
        "n_cap": n_cap,
        "n_draw": n_draw,
        "n_excluding_same": n_excl,
        "score_decisive": sc_dec,
        "score_excluding_same": sc_ex,
        "score_lo": lo,
        "score_hi": hi,
        "mean_ply": ply_sum / max(n, 1),
        "same_policy_is_not_a_match": True,
        "us": us_name,
        "them": them_name,
        "max_ply": max_ply,
        "resign_pawns": resign_pawns,
        "opening_plies": opening_plies,
        "elo": None,
    }
