# Copyright (c) 2026 Martial Systems LLC
"""Child-position value: mix-0 player, mix-1 shuffle probe, mix-1 MLP probe."""

from __future__ import annotations

import json
import random
from collections.abc import Callable

import chess
import numpy as np

from fly_chess.child_value import pick_child, pairwise_agree
from fly_chess.dense_catalog import PositionRow, build_catalog, load_value_cfg
from fly_chess.hand_eval import hand_eval
from fly_chess.lif import HZ_NOTE
from fly_chess.mask import legal_moves
from fly_chess.match import mean_interval, random_move
from fly_chess.paths import LOGS
from fly_chess.session import Session, open_session
from fly_chess.value_feats import graph_fingerprint, mix0_features, mix1_features
from fly_chess.value_head import LinearValue, MLPValue

TABLE_PATH = LOGS / "value_lock.json"
HEAD_A = LOGS / "value_mix0.npz"
HEAD_B = LOGS / "value_mix1_real.npz"
HEAD_C = LOGS / "value_mix1_mlp.npz"
SHUFFLE_SEEDS = (1, 2, 3, 4, 5)


def _cfg(tiny: bool) -> dict:
    cfg = load_value_cfg()
    if tiny:
        cfg = dict(cfg)
        cfg["catalog"] = {
            **cfg["catalog"],
            "n_games": 6,
            "positions_per_game": 3,
            "max_ply": 24,
        }
        cfg["games_n"] = 2
        cfg["mlp_epochs"] = 8
    return cfg


def _session(*, shuffled: bool = False, seed: int = 0) -> Session:
    return open_session(source="fixture", shuffled=shuffled, seed=seed)


def _stack_parents(session: Session, rows: list[PositionRow], feat_fn) -> tuple[np.ndarray, np.ndarray]:
    xs = [feat_fn(session, chess.Board(r.fen)) for r in rows]
    ys = [r.y_white for r in rows]
    return np.stack(xs), np.asarray(ys, dtype=np.float64)


def _silent(X: np.ndarray) -> bool:
    return float(np.max(np.abs(X))) < 1e-12


def _mix1_fn(*, silent: bool, n_feat: int):
    if silent:

        def zeros(_s: Session, _b: chess.Board) -> np.ndarray:
            return np.zeros(n_feat, dtype=np.float64)

        return zeros
    return lambda s, b: mix1_features(s, b, n_plies=1)


def _ridge_occupancy_children(session: Session, rows: list[PositionRow], *, l2: float) -> LinearValue:
    batches: list[tuple[np.ndarray, np.ndarray]] = []
    buf_x: list[np.ndarray] = []
    buf_y: list[float] = []
    for row in rows:
        board = chess.Board(row.fen)
        buf_x.append(mix0_features(session, board))
        buf_y.append(row.y_white)
        for move in legal_moves(board):
            board.push(move)
            buf_x.append(mix0_features(session, board))
            buf_y.append(hand_eval(board))
            board.pop()
            if len(buf_x) >= 1024:
                batches.append((np.stack(buf_x), np.asarray(buf_y, dtype=np.float64)))
                buf_x, buf_y = [], []
    if buf_x:
        batches.append((np.stack(buf_x), np.asarray(buf_y, dtype=np.float64)))
    from fly_chess.value_head import ridge_from_batches

    w, b = ridge_from_batches(batches, l2=l2)
    return LinearValue(w=w, b=b)


def _mse(pred: np.ndarray, y: np.ndarray) -> float:
    return float(np.mean((pred - y) ** 2))


def _pearson(pred: np.ndarray, y: np.ndarray) -> float:
    if pred.size < 2:
        return 0.0
    if float(np.std(pred)) < 1e-12 or float(np.std(y)) < 1e-12:
        return 0.0
    pc = np.corrcoef(pred, y)[0, 1]
    return 0.0 if np.isnan(pc) else float(pc)


def eval_value(
    session: Session,
    head: LinearValue | MLPValue,
    rows: list[PositionRow],
    feat_fn,
) -> dict:
    X, y = _stack_parents(session, rows, feat_fn)
    pred = head.predict_many(X)
    pair_vals: list[float] = []
    best_match = 0
    n_pos = 0
    for row in rows:
        board = chess.Board(row.fen)
        legal = legal_moves(board)
        if len(legal) < 2:
            continue
        n_pos += 1
        preds: list[float] = []
        targs: list[float] = []
        us = board.turn
        for move in legal:
            board.push(move)
            y_white = hand_eval(board)
            p_white = head.predict(feat_fn(session, board))
            board.pop()
            preds.append(p_white if us == chess.WHITE else -p_white)
            targs.append(y_white if us == chess.WHITE else -y_white)
        p = np.asarray(preds, dtype=np.float64)
        t = np.asarray(targs, dtype=np.float64)
        pair_vals.append(pairwise_agree(p, t))
        if int(np.argmax(p)) == int(np.argmax(t)):
            best_match += 1
    return {
        "n_positions": len(rows),
        "mse": _mse(pred, y),
        "pearson": _pearson(pred, y),
        "child_pairwise": float(np.mean(pair_vals)) if pair_vals else 1.0,
        "best_child_match": best_match / max(n_pos, 1),
        "n_ranked": n_pos,
    }


def _score_fn(session: Session, head: LinearValue | MLPValue, feat_fn) -> Callable[[chess.Board], float]:
    def score_white(board: chess.Board) -> float:
        return head.predict(feat_fn(session, board))

    return score_white


def play_value_games(
    session: Session,
    head: LinearValue | MLPValue,
    feat_fn,
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
            "ply": 0,
            "opponent": "random",
            "elo": None,
            "skipped": True,
        }
    rng = random.Random(seed)
    score_white = _score_fn(session, head, feat_fn)
    score = 0.0
    illegal = 0
    ply = 0
    for g in range(n):
        board = chess.Board()
        us_white = g % 2 == 0
        us = chess.WHITE if us_white else chess.BLACK
        while not board.is_game_over() and board.ply() < 80:
            if board.turn == us:
                move = pick_child(board, score_white)
                if move not in board.legal_moves:
                    illegal += 1
                    move = random_move(board, rng)
                board.push(move)
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
        "illegal": illegal,
        "ply": ply,
        "opponent": "random",
        "elo": None,
    }


def _mean_interval(xs: list[float]) -> tuple[float, float, float]:
    arr = np.asarray(xs, dtype=np.float64)
    mean = float(np.mean(arr))
    if arr.size <= 1:
        return mean, mean, mean
    se = float(np.std(arr, ddof=1) / np.sqrt(arr.size))
    return mean, mean - 1.96 * se, mean + 1.96 * se


def _beats_random(games: dict) -> bool:
    if games.get("skipped") or games.get("score") is None:
        return False
    return float(games["score_lo"]) > 0.5 and int(games["illegal"]) == 0


def _wiring_helped(a: dict, b_real: dict, b_shuf: dict) -> bool:
    value_ok = (
        float(b_real["held_out"]["child_pairwise"]) > float(a["held_out"]["child_pairwise"])
        and float(b_real["held_out"]["child_pairwise"]) > float(b_shuf["held_out"]["child_pairwise"])
        and float(b_real["held_out"]["mse"]) < float(a["held_out"]["mse"])
        and float(b_real["held_out"]["mse"]) < float(b_shuf["held_out"]["mse"])
    )
    if a["games"].get("skipped") or b_real["games"].get("skipped"):
        return False
    games_ok = (
        float(b_real["games"]["score"]) > float(a["games"]["score"])
        and float(b_real["games"]["score"]) > float(b_shuf["games"]["score"])
        and float(b_shuf["delta_games_lo"]) > 0.0
    )
    return bool(value_ok and games_ok)


def run_value(*, stage: str = "all", tiny: bool = False, n_play: int | None = None) -> dict:
    cfg = _cfg(tiny)
    cat_cfg = cfg["catalog"]
    split = build_catalog(
        n_games=int(cat_cfg["n_games"]),
        positions_per_game=int(cat_cfg["positions_per_game"]),
        max_ply=int(cat_cfg["max_ply"]),
        seed=int(cat_cfg["seed"]),
        holdout_frac=float(cat_cfg["holdout_frac"]),
    )
    train, ev = split["train"], split["eval"]
    n_play = int(cfg["games_n"] if n_play is None else n_play)
    real = _session(shuffled=False)
    fp0 = graph_fingerprint(real)
    want = stage.lower()
    out: dict = {
        "experiment": "child_value",
        "question": cfg["question"],
        "graph": "fixture, not MaleCNS v1.0",
        "player": cfg["player"],
        "science": cfg["science"],
        "target": cfg["target"],
        "shuffle_seeds": list(SHUFFLE_SEEDS),
        "n_train": len(train),
        "n_eval": len(ev),
        "games_n": n_play,
        "graph_frozen": True,
        "synapses_trainable": False,
        "elo": None,
        "gate2_quoted": False,
        "ethology_rerun": False,
        "hz_note": HZ_NOTE,
        "tiny": tiny,
    }
    out["catalog"] = {
        "source": "selfplay_games",
        "holdout": "game_id",
        "not_hanging_catalog": True,
        "n_train": len(train),
        "n_eval": len(ev),
        "n_train_games": len({r.game_id for r in train}),
        "n_eval_games": len({r.game_id for r in ev}),
        "train_phases": _phases(train),
        "eval_phases": _phases(ev),
        "policies": sorted({r.policy for r in train + ev}),
    }

    a = None
    if want in ("a", "all", "table"):
        head_a = _ridge_occupancy_children(real, train, l2=float(cfg["ridge_l2"]))
        if graph_fingerprint(real) != fp0:
            raise RuntimeError("mix-0 fit mutated the graph")
        held_a = eval_value(real, head_a, ev, mix0_features)
        games_a = play_value_games(real, head_a, mix0_features, n=n_play, seed=int(cfg["game_seed"]))
        LOGS.mkdir(parents=True, exist_ok=True)
        head_a.save(HEAD_A)
        a = {
            "arm": "A",
            "mix_plies": 0,
            "synapses_used": False,
            "head": "linear_value",
            "features": "occupancy_12x64_stm_castle_ep",
            "held_out": held_a,
            "games": games_a,
            "beats_random": _beats_random(games_a),
            "weights": "logs/value_mix0.npz",
        }
        out["A"] = a

    b_real = b_shuf = None
    if want in ("b", "all", "table"):
        if a is None and want == "table":
            raise RuntimeError("table needs A")
        Xtr, ytr = _stack_parents(real, train, lambda s, b: mix1_features(s, b, n_plies=1))
        silent_real = _silent(Xtr)
        feat_b = _mix1_fn(silent=silent_real, n_feat=Xtr.shape[1])
        head_b = LinearValue.fit(Xtr, ytr, l2=float(cfg["ridge_l2"]), zscore=True)
        if graph_fingerprint(real) != fp0:
            raise RuntimeError("mix-1 fit mutated the graph")
        held_b = eval_value(real, head_b, ev, feat_b)
        games_b = play_value_games(
            real, head_b, feat_b, n=n_play, seed=int(cfg["game_seed"])
        )
        head_b.save(HEAD_B)
        shuf_held = []
        shuf_games = []
        shuf_mse = []
        shuf_pair = []
        shuf_score = []
        shuf_silent = []
        for seed in SHUFFLE_SEEDS:
            sh = _session(shuffled=True, seed=seed)
            fp_s = graph_fingerprint(sh)
            Xs, ys = _stack_parents(sh, train, lambda s, b: mix1_features(s, b, n_plies=1))
            silent_s = _silent(Xs)
            shuf_silent.append(silent_s)
            feat_s = _mix1_fn(silent=silent_s, n_feat=Xs.shape[1])
            hs = LinearValue.fit(Xs, ys, l2=float(cfg["ridge_l2"]), zscore=True)
            if graph_fingerprint(sh) != fp_s:
                raise RuntimeError("shuffle mix-1 fit mutated the graph")
            hv = eval_value(sh, hs, ev, feat_s)
            gv = play_value_games(
                sh, hs, feat_s, n=n_play, seed=int(cfg["game_seed"])
            )
            shuf_held.append(hv)
            shuf_games.append(gv)
            shuf_mse.append(hv["mse"])
            shuf_pair.append(hv["child_pairwise"])
            if gv.get("score") is not None:
                shuf_score.append(gv["score"])
        pair_mean, pair_lo, pair_hi = _mean_interval(
            [held_b["child_pairwise"] - x for x in shuf_pair]
        )
        mse_mean, mse_lo, mse_hi = _mean_interval([x - held_b["mse"] for x in shuf_mse])
        if games_b.get("score") is None or not shuf_score:
            sc_mean = sc_lo = sc_hi = 0.0
        else:
            sc_mean, sc_lo, sc_hi = _mean_interval([games_b["score"] - x for x in shuf_score])
        b_real = {
            "arm": "B_real",
            "mix_plies": 1,
            "synapses_used": True,
            "head": "linear_value",
            "features": "hidden_64_after_one_ply",
            "hidden_rates_silent": silent_real,
            "train_rate_max": float(np.max(np.abs(Xtr))),
            "held_out": held_b,
            "games": games_b,
            "beats_random": _beats_random(games_b),
            "weights": "logs/value_mix1_real.npz",
        }
        b_shuf = {
            "arm": "B_shuffle",
            "mix_plies": 1,
            "synapses_used": True,
            "head": "linear_value",
            "features": "hidden_64_after_one_ply",
            "hidden_rates_silent_per_seed": shuf_silent,
            "shuffle_seeds": list(SHUFFLE_SEEDS),
            "held_out": {
                "mse": float(np.mean(shuf_mse)),
                "child_pairwise": float(np.mean(shuf_pair)),
                "pearson": float(np.mean([h["pearson"] for h in shuf_held])),
                "best_child_match": float(np.mean([h["best_child_match"] for h in shuf_held])),
                "n_positions": len(ev),
                "per_seed": shuf_held,
            },
            "games": {
                "n_games": n_play,
                "n_games_per_seed": n_play,
                "score": float(np.mean(shuf_score)) if shuf_score else None,
                "score_lo": (
                    float(np.min([g["score_lo"] for g in shuf_games if g.get("score_lo") is not None]))
                    if any(g.get("score_lo") is not None for g in shuf_games)
                    else None
                ),
                "score_hi": (
                    float(np.max([g["score_hi"] for g in shuf_games if g.get("score_hi") is not None]))
                    if any(g.get("score_hi") is not None for g in shuf_games)
                    else None
                ),
                "illegal": int(sum(g["illegal"] for g in shuf_games)),
                "elo": None,
                "opponent": "random",
                "skipped": n_play <= 0,
                "per_seed": shuf_games,
            },
            "delta_pairwise_mean": pair_mean,
            "delta_pairwise_lo": pair_lo,
            "delta_pairwise_hi": pair_hi,
            "delta_mse_mean": mse_mean,
            "delta_mse_lo": mse_lo,
            "delta_mse_hi": mse_hi,
            "delta_games_mean": sc_mean,
            "delta_games_lo": sc_lo,
            "delta_games_hi": sc_hi,
        }
        out["B_real"] = b_real
        out["B_shuffle"] = b_shuf

    if want in ("c", "all"):
        Xtr, ytr = _stack_parents(real, train, lambda s, b: mix1_features(s, b, n_plies=1))
        silent_c = _silent(Xtr)
        feat_c = _mix1_fn(silent=silent_c, n_feat=Xtr.shape[1])
        mlp = MLPValue.fit(
            Xtr,
            ytr,
            hidden=int(cfg["mlp_hidden"]),
            epochs=int(cfg["mlp_epochs"]),
            lr=float(cfg["mlp_lr"]),
            batch=int(cfg["mlp_batch"]),
            seed=0,
        )
        if graph_fingerprint(real) != fp0:
            raise RuntimeError("MLP fit mutated the graph")
        held_c = eval_value(real, mlp, ev, feat_c)
        shuf_c = []
        for seed in SHUFFLE_SEEDS:
            sh = _session(shuffled=True, seed=seed)
            Xs, ys = _stack_parents(sh, train, lambda s, b: mix1_features(s, b, n_plies=1))
            feat_s = _mix1_fn(silent=_silent(Xs), n_feat=Xs.shape[1])
            hs = MLPValue.fit(
                Xs,
                ys,
                hidden=int(cfg["mlp_hidden"]),
                epochs=int(cfg["mlp_epochs"]),
                lr=float(cfg["mlp_lr"]),
                batch=int(cfg["mlp_batch"]),
                seed=0,
            )
            shuf_c.append(eval_value(sh, hs, ev, feat_s))
        dpair = [held_c["child_pairwise"] - h["child_pairwise"] for h in shuf_c]
        dmse = [h["mse"] - held_c["mse"] for h in shuf_c]
        pmean, plo, phi = _mean_interval(dpair)
        mmean, mlo, mhi = _mean_interval(dmse)
        mlp.save(HEAD_C)
        out["C"] = {
            "arm": "C",
            "mix_plies": 1,
            "synapses_used": True,
            "head": "mlp_two_layer",
            "mlp_hidden": int(cfg["mlp_hidden"]),
            "features": "hidden_64_after_one_ply",
            "held_out": held_c,
            "shuffle_held_out": {
                "mse": float(np.mean([h["mse"] for h in shuf_c])),
                "child_pairwise": float(np.mean([h["child_pairwise"] for h in shuf_c])),
                "per_seed": shuf_c,
            },
            "delta_pairwise_mean": pmean,
            "delta_pairwise_lo": plo,
            "delta_pairwise_hi": phi,
            "delta_mse_mean": mmean,
            "delta_mse_lo": mlo,
            "delta_mse_hi": mhi,
            "delta_includes_zero": plo <= 0.0 <= phi,
            "weights": "logs/value_mix1_mlp.npz",
        }

    if a is not None and b_real is not None and b_shuf is not None:
        helped = _wiring_helped(a, b_real, b_shuf)
        out["table"] = {
            "A_games": a["games"]["score"],
            "B_real_games": b_real["games"]["score"],
            "B_shuffle_games": b_shuf["games"]["score"],
            "A_pairwise": a["held_out"]["child_pairwise"],
            "B_real_pairwise": b_real["held_out"]["child_pairwise"],
            "B_shuffle_pairwise": b_shuf["held_out"]["child_pairwise"],
            "A_mse": a["held_out"]["mse"],
            "B_real_mse": b_real["held_out"]["mse"],
            "B_shuffle_mse": b_shuf["held_out"]["mse"],
        }
        out["A_beats_random"] = a["beats_random"]
        out["wiring_helped"] = helped
        out["unfreeze_allowed"] = False
        out["claim"] = (
            "Child-position value ranker on mix-0 occupancy; "
            "mix-1 hidden-rate probes vs five shuffle seeds. Graph frozen."
        )
        if not a["beats_random"]:
            out["note"] = (
                "Mix-0 child scoring did not beat random-legal. "
                "Head or data are wrong; the fly is irrelevant."
            )
        elif helped:
            out["note"] = (
                "Mix-1 real wiring beat mix-0 and shuffle on held-out value and on games. "
                "That is a wiring effect on this value task."
            )
        else:
            out["note"] = (
                "Mix-0 occupancy ranker is the player. Mix-1 real did not beat both "
                "mix-0 and shuffle, so the synapses still are not playing."
            )

    out["fingerprint"] = fp0
    if graph_fingerprint(real) != fp0:
        raise RuntimeError("graph mutated by the value run")
    LOGS.mkdir(parents=True, exist_ok=True)
    if not tiny:
        TABLE_PATH.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    return out


def _phases(rows: list[PositionRow]) -> dict[str, int]:
    out = {"opening": 0, "middlegame": 0, "simple": 0}
    for r in rows:
        out[r.phase] = out.get(r.phase, 0) + 1
    return out


def write_value(*, stage: str = "all", tiny: bool = False, n_play: int | None = None) -> dict:
    return run_value(stage=stage, tiny=tiny, n_play=n_play)
