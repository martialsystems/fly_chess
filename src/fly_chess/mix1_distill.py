# Copyright (c) 2026 Martial Systems LLC
"""Distill A's child hand-eval onto mix-1 hidden rates. Real vs shuffle."""

from __future__ import annotations

import json
import random

import chess
import numpy as np

from fly_chess.child_value import pick_child
from fly_chess.dense_catalog import load_value_cfg
from fly_chess.distill_value import _split_by_game, play_ava_positions
from fly_chess.hand_eval import hand_eval
from fly_chess.lif import HZ_NOTE
from fly_chess.mask import legal_moves
from fly_chess.match import random_move
from fly_chess.paths import LOGS
from fly_chess.play_match import play_policies
from fly_chess.search import pick_search
from fly_chess.session import Session, open_session
from fly_chess.train_value import SHUFFLE_SEEDS, _silent
from fly_chess.value_feats import graph_fingerprint, mix1_features
from fly_chess.value_head import LinearValue

TABLE_PATH = LOGS / "mix1_distill.json"


def _fit_mix1_children(
    session: Session,
    parents: list[str],
    *,
    l2: float,
    silent: bool | None = None,
) -> tuple[LinearValue, bool, float]:
    xs: list[np.ndarray] = []
    ys: list[float] = []
    probe = mix1_features(session, chess.Board(), n_plies=1)
    silent_now = silent
    for fen in parents:
        board = chess.Board(fen)
        for move in legal_moves(board):
            board.push(move)
            if silent_now:
                feat = np.zeros_like(probe)
            else:
                feat = mix1_features(session, board, n_plies=1)
            xs.append(feat)
            ys.append(hand_eval(board))
            board.pop()
            if len(xs) >= 256 and silent_now is None:
                stacked = np.stack(xs)
                silent_now = _silent(stacked)
                if silent_now:
                    xs = [np.zeros_like(probe) for _ in xs]
    if not xs:
        raise RuntimeError("no mix-1 children")
    X = np.stack(xs)
    if silent_now is None:
        silent_now = _silent(X)
    y = np.asarray(ys, dtype=np.float64)
    head = LinearValue.fit(X, y, l2=l2, zscore=not silent_now)
    return head, bool(silent_now), float(np.max(np.abs(X)))


def _mix1_pick(session: Session, head: LinearValue, *, silent: bool):
    n = 64

    def pick(board: chess.Board) -> chess.Move:
        def score(child: chess.Board) -> float:
            if silent:
                feat = np.zeros(n, dtype=np.float64)
            else:
                feat = mix1_features(session, child, n_plies=1)
            return head.predict(feat)

        return pick_child(board, score)

    return pick


def _mean_interval(xs: list[float]) -> tuple[float, float, float]:
    arr = np.asarray(xs, dtype=np.float64)
    mean = float(np.mean(arr))
    if arr.size <= 1:
        return mean, mean, mean
    se = float(np.std(arr, ddof=1) / np.sqrt(arr.size))
    return mean, mean - 1.96 * se, mean + 1.96 * se


def run_mix1_distill(*, tiny: bool = False, n_play: int | None = None) -> dict:
    cfg = load_value_cfg()
    dcfg = cfg.get("mix1_distill") or cfg.get("distill") or {}
    n_games = 4 if tiny else int(dcfg.get("n_games", 200))
    opening = 2 if tiny else int(dcfg.get("opening_plies", 6))
    max_ply_gen = 12 if tiny else int(dcfg.get("max_ply", 64))
    n_play = int((0 if tiny else dcfg.get("games_n", 200)) if n_play is None else n_play)
    match_ply = 40 if tiny else 400
    l2 = float(cfg["ridge_l2"])
    seed = int(dcfg.get("seed", 4))
    real = open_session(source="fixture", shuffled=False)
    fp0 = graph_fingerprint(real)
    rows = play_ava_positions(
        n_games=n_games, opening_plies=opening, max_ply=max_ply_gen, seed=seed
    )
    train_fens, eval_fens = _split_by_game(rows, holdout_frac=0.2, seed=seed + 1)
    head_r, silent_r, max_r = _fit_mix1_children(real, train_fens, l2=l2)
    if graph_fingerprint(real) != fp0:
        raise RuntimeError("mix-1 distill mutated the graph")
    # held-out: if silent, skip LIF on eval children
    def mix1_or_zero(session: Session, board: chess.Board) -> np.ndarray:
        if silent_r:
            return np.zeros(64, dtype=np.float64)
        return mix1_features(session, board, n_plies=1)

    preds = []
    targs = []
    for fen in eval_fens:
        board = chess.Board(fen)
        for move in legal_moves(board):
            board.push(move)
            preds.append(head_r.predict(mix1_or_zero(real, board)))
            targs.append(hand_eval(board))
            board.pop()
    p = np.asarray(preds)
    t = np.asarray(targs)
    if p.size < 2 or float(np.std(p)) < 1e-12 or float(np.std(t)) < 1e-12:
        pearson = 0.0
    else:
        pc = np.corrcoef(p, t)[0, 1]
        pearson = 0.0 if np.isnan(pc) else float(pc)
    held = {
        "n_parents": len(eval_fens),
        "n_children": int(p.size),
        "mse": float(np.mean((p - t) ** 2)) if p.size else None,
        "pearson": pearson,
    }
    pick_a = lambda b: pick_search(b, plies=1)
    pick_r = _mix1_pick(real, head_r, silent=silent_r)
    vs_a = play_policies(
        pick_r,
        pick_a,
        n=n_play,
        seed=int(cfg["game_seed"]),
        us_name="mix1_real",
        them_name="mix0_A",
        max_ply=match_ply,
    )
    rng_rand = random.Random(int(cfg["game_seed"]) + 9)
    vs_rand = play_policies(
        pick_r,
        lambda b: random_move(b, rng_rand),
        n=n_play,
        seed=int(cfg["game_seed"]),
        us_name="mix1_real",
        them_name="random",
        max_ply=match_ply,
    )
    shuf_rows = []
    shuf_pair = []
    shuf_games = []
    for sh_seed in SHUFFLE_SEEDS:
        sh = open_session(source="fixture", shuffled=True, seed=sh_seed)
        hs, silent_s, max_s = _fit_mix1_children(sh, train_fens, l2=l2)
        pred_s = []
        targ_s = []
        for fen in eval_fens:
            board = chess.Board(fen)
            for move in legal_moves(board):
                board.push(move)
                feat = (
                    np.zeros(64)
                    if silent_s
                    else mix1_features(sh, board, n_plies=1)
                )
                pred_s.append(hs.predict(feat))
                targ_s.append(hand_eval(board))
                board.pop()
        ps = np.asarray(pred_s)
        ts = np.asarray(targ_s)
        if ps.size < 2 or float(np.std(ps)) < 1e-12 or float(np.std(ts)) < 1e-12:
            pr = 0.0
        else:
            c = np.corrcoef(ps, ts)[0, 1]
            pr = 0.0 if np.isnan(c) else float(c)
        shuf_pair.append(pr)
        pick_s = _mix1_pick(sh, hs, silent=silent_s)
        gv = play_policies(
            pick_s,
            pick_a,
            n=n_play,
            seed=int(cfg["game_seed"]),
            us_name=f"mix1_shuffle_{sh_seed}",
            them_name="mix0_A",
            max_ply=match_ply,
        )
        shuf_games.append(gv)
        shuf_rows.append(
            {
                "shuffle_seed": sh_seed,
                "silent": silent_s,
                "train_rate_max": max_s,
                "pearson": pr,
                "vs_A": gv,
            }
        )
    pair_d = [held["pearson"] - x for x in shuf_pair]
    pmean, plo, phi = _mean_interval(pair_d)
    real_vs_a = vs_a.get("score_excluding_same")
    shuf_vs_a = [
        g.get("score_excluding_same") for g in shuf_games if g.get("score_excluding_same") is not None
    ]
    helped = False
    if real_vs_a is not None and shuf_vs_a and vs_a.get("n_decisive", 0) >= 1:
        helped = (
            float(real_vs_a) > float(np.mean(shuf_vs_a))
            and float(held["pearson"]) > float(np.mean(shuf_pair))
            and plo > 0.0
            and float(real_vs_a) > 0.5
        )
    if graph_fingerprint(real) != fp0:
        raise RuntimeError("mix-1 distill mutated the graph")
    payload = {
        "experiment": "mix1_child_distill",
        "child_label": "hand_eval",
        "features": "hidden_64_after_one_ply",
        "generator": "A_vs_A_after_random_opening",
        "n_games": n_games,
        "n_train_parents": len(train_fens),
        "n_eval_parents": len(eval_fens),
        "holdout": "game_id",
        "real": {
            "silent": silent_r,
            "train_rate_max": max_r,
            "held_out": held,
            "vs_A": vs_a,
            "vs_random": vs_rand,
        },
        "shuffle": {
            "seeds": list(SHUFFLE_SEEDS),
            "pearson_mean": float(np.mean(shuf_pair)),
            "delta_pearson_mean": pmean,
            "delta_pearson_lo": plo,
            "delta_pearson_hi": phi,
            "per_seed": shuf_rows,
        },
        "wiring_helped": helped,
        "unfreeze_allowed": False,
        "graph_frozen": True,
        "synapses_used": True,
        "elo": None,
        "gate2_quoted": False,
        "ethology_rerun": False,
        "hz_note": HZ_NOTE,
        "tiny": tiny,
        "claim": (
            "Mix-1 child-value distill of A's hand-eval, real vs five shuffles. "
            "Graph frozen. Distill mix-0 is A."
        ),
        "note": (
            "wiring_helped only if mix-1 real beats shuffle and mix-0 A "
            "on held-out child value and on games that are not same-policy."
        ),
        "fingerprint": fp0,
    }
    if not tiny:
        LOGS.mkdir(parents=True, exist_ok=True)
        TABLE_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def write_mix1_distill(*, tiny: bool = False, n_play: int | None = None) -> dict:
    return run_mix1_distill(tiny=tiny, n_play=n_play)
