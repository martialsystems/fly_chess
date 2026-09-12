# Copyright (c) 2026 Martial Systems LLC
"""Mix-0 self-play value. Graph frozen. Mix-1 line stays closed."""

from __future__ import annotations

import json
import random
from collections.abc import Callable

import chess
import numpy as np

from fly_chess.child_value import pick_child
from fly_chess.dense_catalog import build_catalog, load_value_cfg
from fly_chess.hand_eval import hand_eval, is_drawish
from fly_chess.lif import HZ_NOTE
from fly_chess.match import mean_interval, random_move
from fly_chess.paths import LOGS
from fly_chess.session import Session, open_session
from fly_chess.train_value import (
    HEAD_A,
    _ridge_occupancy_children,
    _score_fn,
    play_value_games,
)
from fly_chess.value_feats import graph_fingerprint, mix0_features
from fly_chess.value_head import LinearValue

TABLE_PATH = LOGS / "value_selfplay.json"
HEAD_SP = LOGS / "value_mix0_selfplay.npz"
MATERIAL_COEF = 0.05
MAX_PLY = 80


def terminal_white(board: chess.Board) -> float | None:
    """White-centric game return. Mate is ±1. Draw is 0."""
    if board.is_checkmate():
        return -1.0 if board.turn == chess.WHITE else 1.0
    if is_drawish(board):
        return 0.0
    return None


def backup_white(board: chess.Board, *, material_coef: float = MATERIAL_COEF) -> float:
    term = terminal_white(board)
    if term is not None:
        return term
    return float(material_coef * np.tanh(hand_eval(board) / 10.0))


def _pick(board: chess.Board, score_white: Callable[[chess.Board], float], rng: random.Random) -> chess.Move:
    move = pick_child(board, score_white)
    if move not in board.legal_moves:
        return random_move(board, rng)
    return move


def play_labeled_game(
    *,
    score_us: Callable[[chess.Board], float],
    opponent: str,
    score_them: Callable[[chess.Board], float] | None,
    us_white: bool,
    rng: random.Random,
    max_ply: int = MAX_PLY,
    material_coef: float = MATERIAL_COEF,
) -> tuple[list[str], float, int]:
    board = chess.Board()
    us = chess.WHITE if us_white else chess.BLACK
    fens: list[str] = []
    ply = 0
    while not board.is_game_over() and ply < max_ply:
        fens.append(board.fen())
        if board.turn == us:
            board.push(_pick(board, score_us, rng))
        elif opponent == "self" and score_them is not None:
            board.push(_pick(board, score_them, rng))
        else:
            board.push(random_move(board, rng))
        ply += 1
    return fens, backup_white(board, material_coef=material_coef), ply


def play_two_heads(
    session: Session,
    head_us: LinearValue,
    head_them: LinearValue,
    *,
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
            "opponent": "mix0_hand_eval",
        }
    rng = random.Random(seed)
    us_fn = _score_fn(session, head_us, mix0_features)
    them_fn = _score_fn(session, head_them, mix0_features)
    score = 0.0
    illegal = 0
    ply = 0
    for g in range(n):
        board = chess.Board()
        us_white = g % 2 == 0
        us = chess.WHITE if us_white else chess.BLACK
        while not board.is_game_over() and board.ply() < MAX_PLY:
            fn = us_fn if board.turn == us else them_fn
            move = pick_child(board, fn)
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
        "opponent": "mix0_hand_eval",
        "elo": None,
    }


def _load_or_fit_a(session: Session, *, tiny: bool) -> LinearValue:
    """Always refit from the catalog. Do not trust a leftover npz."""
    cfg = load_value_cfg()
    cat = cfg["catalog"]
    n_games = 6 if tiny else int(cat["n_games"])
    per = 3 if tiny else int(cat["positions_per_game"])
    split = build_catalog(
        n_games=n_games,
        positions_per_game=per,
        max_ply=24 if tiny else int(cat["max_ply"]),
        seed=int(cat["seed"]),
        holdout_frac=float(cat["holdout_frac"]),
    )
    head = _ridge_occupancy_children(session, split["train"], l2=float(cfg["ridge_l2"]))
    if not tiny:
        head.save(HEAD_A)
    return head


def run_selfplay(*, tiny: bool = False, n_play: int | None = None) -> dict:
    cfg = load_value_cfg()
    sp = cfg.get("selfplay") or {}
    n_games = 4 if tiny else int(sp.get("n_games", 400))
    n_play = int((0 if tiny else sp.get("games_n", cfg["games_n"])) if n_play is None else n_play)
    vs_random_frac = float(sp.get("vs_random_frac", 0.5))
    material_coef = float(sp.get("material_coef", MATERIAL_COEF))
    max_ply = 16 if tiny else int(sp.get("max_ply", MAX_PLY))
    seed = int(sp.get("seed", 1))
    rng = random.Random(seed)
    session = open_session(source="fixture", shuffled=False)
    fp0 = graph_fingerprint(session)
    head_a = _load_or_fit_a(session, tiny=tiny)
    if graph_fingerprint(session) != fp0:
        raise RuntimeError("loading A mutated the graph")
    score_a = _score_fn(session, head_a, mix0_features)
    games: list[tuple[list[str], float]] = []
    terminals = {"mate": 0, "draw": 0, "trunc": 0}
    for gid in range(n_games):
        us_white = gid % 2 == 0
        opponent = "random" if rng.random() < vs_random_frac else "self"
        fens, y, _ply = play_labeled_game(
            score_us=score_a,
            opponent=opponent,
            score_them=score_a,
            us_white=us_white,
            rng=rng,
            max_ply=max_ply,
            material_coef=material_coef,
        )
        if abs(y) >= 1.0 - 1e-9:
            terminals["mate"] += 1
        elif abs(y) < 1e-12:
            terminals["draw"] += 1
        else:
            terminals["trunc"] += 1
        games.append((fens, y))
    order = list(range(n_games))
    rng.shuffle(order)
    n_hold = max(1, int(round(n_games * 0.2)))
    eval_ids = set(order[:n_hold])
    train_fens: list[str] = []
    train_y: list[float] = []
    eval_fens: list[str] = []
    eval_y: list[float] = []
    for gid, (fens, y) in enumerate(games):
        arm_f, arm_y = (eval_fens, eval_y) if gid in eval_ids else (train_fens, train_y)
        arm_f.extend(fens)
        arm_y.extend([y] * len(fens))
    if not train_fens or not eval_fens:
        raise RuntimeError("self-play split emptied an arm")
    xs = [mix0_features(session, chess.Board(fen)) for fen in train_fens]
    head_sp = LinearValue.fit(np.stack(xs), np.asarray(train_y, dtype=np.float64), l2=float(cfg["ridge_l2"]))
    if graph_fingerprint(session) != fp0:
        raise RuntimeError("self-play fit mutated the graph")
    ev_x = np.stack([mix0_features(session, chess.Board(fen)) for fen in eval_fens])
    ev_y = np.asarray(eval_y, dtype=np.float64)
    pred = head_sp.predict_many(ev_x)
    mse = float(np.mean((pred - ev_y) ** 2))
    if float(np.std(pred)) < 1e-12 or float(np.std(ev_y)) < 1e-12:
        pearson = 0.0
    else:
        pc = np.corrcoef(pred, ev_y)[0, 1]
        pearson = 0.0 if np.isnan(pc) else float(pc)
    games_sp = play_value_games(
        session, head_sp, mix0_features, n=n_play, seed=int(cfg["game_seed"])
    )
    games_a = play_value_games(
        session, head_a, mix0_features, n=n_play, seed=int(cfg["game_seed"])
    )
    vs_a = play_two_heads(session, head_sp, head_a, n=n_play, seed=int(cfg["game_seed"]) + 1)
    LOGS.mkdir(parents=True, exist_ok=True)
    if not tiny:
        head_sp.save(HEAD_SP)
    beats_a_random = bool(
        games_a.get("score") is not None and float(games_a["score_lo"]) > 0.5
    )
    beats_random = bool(
        games_sp.get("score") is not None
        and float(games_sp["score_lo"]) > 0.5
        and int(games_sp["illegal"]) == 0
    )
    beats_a = bool(
        vs_a.get("score") is not None
        and games_sp.get("score") is not None
        and games_a.get("score") is not None
        and float(games_sp["score"]) > float(games_a["score"])
        and float(vs_a["score_lo"] or 0) > 0.5
    )
    if graph_fingerprint(session) != fp0:
        raise RuntimeError("self-play play mutated the graph")
    payload = {
        "experiment": "mix0_selfplay_value",
        "player": "mix0_child_ranker_selfplay",
        "graph": "fixture, not MaleCNS v1.0",
        "graph_frozen": True,
        "synapses_trainable": False,
        "synapses_used": False,
        "mix_plies": 0,
        "target": "white_centric_outcome_plus_material_truncation",
        "material_coef": material_coef,
        "n_games_generated": n_games,
        "n_train_positions": len(train_fens),
        "n_eval_positions": len(eval_fens),
        "holdout": "game_id",
        "terminals": terminals,
        "held_out": {"mse": mse, "pearson": pearson, "n_positions": len(eval_fens)},
        "selfplay_vs_random": games_sp,
        "hand_eval_A_vs_random": games_a,
        "selfplay_vs_A": vs_a,
        "beats_random": beats_random,
        "A_beats_random": beats_a_random,
        "beats_A": beats_a,
        "wiring_helped": False,
        "unfreeze_allowed": False,
        "elo": None,
        "gate2_quoted": False,
        "ethology_rerun": False,
        "hz_note": HZ_NOTE,
        "tiny": tiny,
        "claim": (
            "Mix-0 self-play value on occupancy child scoring. "
            "Graph frozen. Mix-1 line closed."
        ),
        "note": (
            "Targets are +1 checkmate, 0 draw, -1 loss for White, plus a small "
            "material term on truncation. Report vs random-legal and vs the "
            "frozen hand-eval mix-0 ranker."
        ),
        "fingerprint": fp0,
    }
    if not tiny:
        TABLE_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def write_selfplay(*, tiny: bool = False, n_play: int | None = None) -> dict:
    return run_selfplay(tiny=tiny, n_play=n_play)
