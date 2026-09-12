# Copyright (c) 2026 Martial Systems LLC
"""Distill mix-0 occupancy from A-vs-A children. Not truncated-return self-play."""

from __future__ import annotations

import json
import random

import chess
import numpy as np

from fly_chess.child_value import pick_child
from fly_chess.dense_catalog import load_value_cfg
from fly_chess.hand_eval import hand_eval
from fly_chess.lif import HZ_NOTE
from fly_chess.mask import legal_moves
from fly_chess.match import mean_interval, random_move
from fly_chess.paths import LOGS
from fly_chess.search import search_white
from fly_chess.session import Session, open_session
from fly_chess.train_value import _score_fn, play_value_games
from fly_chess.value_feats import graph_fingerprint, mix0_features
from fly_chess.value_head import LinearValue, ridge_from_batches

TABLE_PATH = LOGS / "value_distill.json"
HEAD_D = LOGS / "value_mix0_distill.npz"
HEAD_OUT = LOGS / "value_mix0_distill_outcome.npz"
MATCH_PEARSON = 0.98


def play_ava_positions(
    *,
    n_games: int,
    opening_plies: int,
    max_ply: int,
    seed: int,
) -> list[tuple[int, str]]:
    """A vs A after a short random opening. Play is A, not random."""
    rng = random.Random(seed)
    rows: list[tuple[int, str]] = []
    for gid in range(n_games):
        board = chess.Board()
        n_open = int(rng.randint(max(0, opening_plies - 2), opening_plies + 2))
        for _ in range(n_open):
            if board.is_game_over() or not any(board.legal_moves):
                break
            board.push(random_move(board, rng))
        ply = 0
        while not board.is_game_over() and ply < max_ply:
            rows.append((gid, board.fen()))
            board.push(pick_child(board, hand_eval))
            ply += 1
    return rows


def _split_by_game(
    rows: list[tuple[int, str]], *, holdout_frac: float, seed: int
) -> tuple[list[str], list[str]]:
    ids = sorted({gid for gid, _fen in rows})
    rng = random.Random(seed)
    rng.shuffle(ids)
    n_hold = max(1, int(round(len(ids) * holdout_frac)))
    eval_ids = set(ids[:n_hold])
    train = [fen for gid, fen in rows if gid not in eval_ids]
    ev = [fen for gid, fen in rows if gid in eval_ids]
    if not train or not ev:
        raise RuntimeError("distill split emptied an arm")
    return train, ev


def _fit_children(
    session: Session,
    parents: list[str],
    *,
    label_fn,
    l2: float,
) -> LinearValue:
    batches: list[tuple[np.ndarray, np.ndarray]] = []
    buf_x: list[np.ndarray] = []
    buf_y: list[float] = []
    for fen in parents:
        board = chess.Board(fen)
        for move in legal_moves(board):
            board.push(move)
            buf_x.append(mix0_features(session, board))
            buf_y.append(float(label_fn(board)))
            board.pop()
            if len(buf_x) >= 1024:
                batches.append((np.stack(buf_x), np.asarray(buf_y, dtype=np.float64)))
                buf_x, buf_y = [], []
    if buf_x:
        batches.append((np.stack(buf_x), np.asarray(buf_y, dtype=np.float64)))
    if not batches:
        raise RuntimeError("no distilled children")
    w, b = ridge_from_batches(batches, l2=l2)
    return LinearValue(w=w, b=b)


def _child_stats(session: Session, head: LinearValue, parents: list[str], *, label_fn) -> dict:
    preds: list[float] = []
    targs: list[float] = []
    for fen in parents:
        board = chess.Board(fen)
        for move in legal_moves(board):
            board.push(move)
            preds.append(head.predict(mix0_features(session, board)))
            targs.append(float(label_fn(board)))
            board.pop()
    p = np.asarray(preds, dtype=np.float64)
    t = np.asarray(targs, dtype=np.float64)
    if p.size < 2 or float(np.std(p)) < 1e-12 or float(np.std(t)) < 1e-12:
        pearson = 0.0
    else:
        pc = np.corrcoef(p, t)[0, 1]
        pearson = 0.0 if np.isnan(pc) else float(pc)
    return {
        "n_parents": len(parents),
        "n_children": int(p.size),
        "mse": float(np.mean((p - t) ** 2)) if p.size else None,
        "pearson": pearson,
    }


def play_vs_search(
    session: Session,
    head: LinearValue,
    *,
    depth: int,
    n: int,
    seed: int,
) -> dict:
    if n <= 0:
        return {
            "n_games": 0,
            "score": None,
            "score_lo": None,
            "score_hi": None,
            "illegal": 0,
            "elo": None,
            "skipped": True,
            "opponent": "hand_eval_1ply" if depth <= 0 else f"search_depth_{depth}",
        }
    rng = random.Random(seed)
    us_fn = _score_fn(session, head, mix0_features)

    def them(board: chess.Board) -> float:
        return hand_eval(board) if depth <= 0 else search_white(board, depth=depth)

    score = 0.0
    illegal = 0
    ply = 0
    for g in range(n):
        board = chess.Board()
        us = chess.WHITE if g % 2 == 0 else chess.BLACK
        while not board.is_game_over() and board.ply() < 80:
            if board.turn == us:
                move = pick_child(board, us_fn)
            else:
                move = pick_child(board, them)
            if move not in board.legal_moves:
                illegal += 1
                move = random_move(board, rng)
            board.push(move)
            ply += 1
        if board.is_checkmate():
            winner = not board.turn
            score += 1.0 if winner == us else 0.0
        else:
            score += 0.5
    mean = score / max(n, 1)
    lo, hi = mean_interval(mean, n)
    return {
        "n_games": n,
        "score": mean,
        "score_lo": lo,
        "score_hi": hi,
        "illegal": illegal,
        "ply": ply,
        "opponent": "hand_eval_1ply" if depth <= 0 else f"search_depth_{depth}",
        "elo": None,
    }


def play_hand_vs_random(*, n: int, seed: int) -> dict:
    if n <= 0:
        return {
            "n_games": 0,
            "score": None,
            "score_lo": None,
            "score_hi": None,
            "illegal": 0,
            "elo": None,
            "skipped": True,
            "opponent": "random",
        }
    rng = random.Random(seed)
    score = 0.0
    ply = 0
    for g in range(n):
        board = chess.Board()
        us = chess.WHITE if g % 2 == 0 else chess.BLACK
        while not board.is_game_over() and board.ply() < 80:
            if board.turn == us:
                board.push(pick_child(board, hand_eval))
            else:
                board.push(random_move(board, rng))
            ply += 1
        if board.is_checkmate():
            winner = not board.turn
            score += 1.0 if winner == us else 0.0
        else:
            score += 0.5
    mean = score / max(n, 1)
    lo, hi = mean_interval(mean, n)
    return {
        "n_games": n,
        "score": mean,
        "score_lo": lo,
        "score_hi": hi,
        "illegal": 0,
        "ply": ply,
        "opponent": "random",
        "elo": None,
    }


def run_distill(*, tiny: bool = False, n_play: int | None = None) -> dict:
    cfg = load_value_cfg()
    dcfg = cfg.get("distill") or {}
    n_games = 4 if tiny else int(dcfg.get("n_games", 200))
    opening = 2 if tiny else int(dcfg.get("opening_plies", 6))
    max_ply = 12 if tiny else int(dcfg.get("max_ply", 64))
    n_play = int((0 if tiny else dcfg.get("games_n", cfg["games_n"])) if n_play is None else n_play)
    l2 = float(cfg["ridge_l2"])
    outcome_coef = float(dcfg.get("outcome_coef", 0.2))
    seed = int(dcfg.get("seed", 2))
    session = open_session(source="fixture", shuffled=False)
    fp0 = graph_fingerprint(session)
    rows = play_ava_positions(
        n_games=n_games, opening_plies=opening, max_ply=max_ply, seed=seed
    )
    train_fens, eval_fens = _split_by_game(rows, holdout_frac=0.2, seed=seed + 1)
    head_d = _fit_children(session, train_fens, label_fn=hand_eval, l2=l2)
    if graph_fingerprint(session) != fp0:
        raise RuntimeError("distill fit mutated the graph")
    stats = _child_stats(session, head_d, eval_fens, label_fn=hand_eval)
    games_d = play_value_games(
        session, head_d, mix0_features, n=n_play, seed=int(cfg["game_seed"])
    )
    vs_a = play_vs_search(session, head_d, depth=0, n=n_play, seed=int(cfg["game_seed"]) + 1)
    vs_search = play_vs_search(session, head_d, depth=1, n=n_play, seed=int(cfg["game_seed"]) + 2)
    a_vs_random = play_hand_vs_random(n=n_play, seed=int(cfg["game_seed"]))
    matches_a = float(stats["pearson"]) >= MATCH_PEARSON
    if games_d.get("score") is not None and a_vs_random.get("score") is not None:
        matches_a = matches_a and abs(float(games_d["score"]) - float(a_vs_random["score"])) <= 0.12
    outcome = None
    if matches_a:

        def blended(board: chess.Board) -> float:
            h = hand_eval(board)
            s = search_white(board, depth=1)
            return float(h + outcome_coef * (s - h))

        head_o = _fit_children(session, train_fens, label_fn=blended, l2=l2)
        if graph_fingerprint(session) != fp0:
            raise RuntimeError("outcome fit mutated the graph")
        if not tiny:
            head_o.save(HEAD_OUT)
        outcome = {
            "outcome_coef": outcome_coef,
            "teacher": "hand_eval plus residual toward 2-ply search",
            "held_out_vs_hand_eval": _child_stats(
                session, head_o, eval_fens, label_fn=hand_eval
            ),
            "vs_random": play_value_games(
                session, head_o, mix0_features, n=n_play, seed=int(cfg["game_seed"])
            ),
            "vs_A": play_vs_search(
                session, head_o, depth=0, n=n_play, seed=int(cfg["game_seed"]) + 1
            ),
            "vs_2ply_search": play_vs_search(
                session, head_o, depth=1, n=n_play, seed=int(cfg["game_seed"]) + 2
            ),
            "weights": "logs/value_mix0_distill_outcome.npz",
        }
    if graph_fingerprint(session) != fp0:
        raise RuntimeError("distill mutated the graph")
    LOGS.mkdir(parents=True, exist_ok=True)
    if not tiny:
        head_d.save(HEAD_D)
    payload = {
        "experiment": "mix0_distill",
        "generator": "A_vs_A_after_random_opening",
        "child_label": "hand_eval",
        "not_truncated_return": True,
        "n_games": n_games,
        "n_train_parents": len(train_fens),
        "n_eval_parents": len(eval_fens),
        "holdout": "game_id",
        "held_out": stats,
        "matches_A": matches_a,
        "match_pearson_min": MATCH_PEARSON,
        "distill_vs_random": games_d,
        "A_vs_random": a_vs_random,
        "distill_vs_A": vs_a,
        "distill_vs_2ply_search": vs_search,
        "outcome": outcome,
        "graph_frozen": True,
        "synapses_used": False,
        "unfreeze_allowed": False,
        "wiring_helped": False,
        "elo": None,
        "gate2_quoted": False,
        "ethology_rerun": False,
        "hz_note": HZ_NOTE,
        "tiny": tiny,
        "claim": (
            "Mix-0 distillation: A-vs-A children labeled with hand-eval. "
            "Graph frozen. Truncated-return self-play is closed."
        ),
        "note": (
            "Every legal child is labeled with A's hand-eval. "
            "A small 2-ply residual is added only after the distilled head matches A."
        ),
        "fingerprint": fp0,
    }
    if not tiny:
        TABLE_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def write_distill(*, tiny: bool = False, n_play: int | None = None) -> dict:
    return run_distill(tiny=tiny, n_play=n_play)
