# Copyright (c) 2026 Martial Systems LLC
"""Mix-depth × shuffle-seed table. LinearHead unchanged. Not Gate 2."""

from __future__ import annotations

import json

import chess
import numpy as np

from fly_chess.head import FactoredHead, LinearHead
from fly_chess.lif import HZ_NOTE
from fly_chess.paths import LOGS
from fly_chess.planes import currents as plane_currents
from fly_chess.planes import hidden_ids, load_planes_cfg, occupancy_vector, readout_vector
from fly_chess.puzzles import split_positions
from fly_chess.session import Session, mix_rates, open_session

MIX_DEPTHS = (0, 1, 3)
SHUFFLE_SEEDS = (1, 2, 3, 4, 5)
EPOCHS = 8
LR = 0.08
TABLE_PATH = LOGS / "planes_mix.json"
CAPTION = (
    "Wiring changes the hidden geometry; it has not made the labeled move "
    "the top linear class."
)


def feat_for_depth(session: Session, board: chess.Board, *, mix_plies: int) -> np.ndarray:
    if mix_plies <= 0:
        return occupancy_vector(board, session.graph, session.resolved)
    i_ext = plane_currents(board, session.graph, session.resolved)
    hz = mix_rates(session, i_ext, n_plies=mix_plies)
    return readout_vector(hz, session.resolved)


def hidden_vec(session: Session, board: chess.Board, *, mix_plies: int) -> np.ndarray:
    if mix_plies <= 0:
        return feat_for_depth(session, board, mix_plies=0)
    i_ext = plane_currents(board, session.graph, session.resolved)
    hz = mix_rates(session, i_ext, n_plies=mix_plies)
    return hz[hidden_ids(session.graph)]


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def knight_empty_cosine(session: Session, *, mix_plies: int) -> float:
    empty = chess.Board("4k3/8/8/8/8/8/8/4K3 w - - 0 1")
    knight = empty.copy()
    knight.set_piece_at(chess.D4, chess.Piece.from_symbol("N"))
    return cosine(
        hidden_vec(session, empty, mix_plies=mix_plies),
        hidden_vec(session, knight, mix_plies=mix_plies),
    )


def _cache(session: Session, rows, *, mix_plies: int) -> list[np.ndarray]:
    return [feat_for_depth(session, board.copy(), mix_plies=mix_plies) for board, _t, _k in rows]


def _train(head, feats, rows, *, epochs: int, lr: float, seed: int) -> None:
    rng = np.random.default_rng(seed)
    order = list(range(len(rows)))
    for _ in range(epochs):
        rng.shuffle(order)
        for i in order:
            board, target, _k = rows[i]
            head.train_step(feats[i], target, board, lr=lr)


def _eval(head, feats, rows) -> dict:
    correct = 0
    ranks: list[int] = []
    for feat, (board, target, _k) in zip(feats, rows):
        move = head.pick(board.copy(), feat)
        ranks.append(head.rank(board.copy(), feat, target))
        if move == target:
            correct += 1
    n = max(len(rows), 1)
    return {
        "n": len(rows),
        "correct": correct,
        "accuracy": correct / n,
        "mean_target_rank": float(np.mean(ranks)) if ranks else None,
    }


def _mean_interval(xs: list[float]) -> tuple[float, float, float]:
    arr = np.array(xs, dtype=np.float64)
    mean = float(np.mean(arr))
    if arr.size <= 1:
        return mean, mean, mean
    se = float(np.std(arr, ddof=1) / np.sqrt(arr.size))
    return mean, mean - 1.96 * se, mean + 1.96 * se


def run_mix_sweep(*, epochs: int = EPOCHS, lr: float = LR, seed: int = 0) -> dict:
    train_rows = split_positions(arm="train")
    eval_rows = split_positions(arm="eval")
    if len(train_rows) < 80 or len(eval_rows) < 40:
        raise RuntimeError("split too small for mix sweep")
    real = open_session(source="fixture", shuffled=False)
    depths = []
    for mix in MIX_DEPTHS:
        real_train = _cache(real, train_rows, mix_plies=mix)
        real_eval = _cache(real, eval_rows, mix_plies=mix)
        lin = LinearHead.zeros(len(real_train[0]))
        _train(lin, real_train, train_rows, epochs=epochs, lr=lr, seed=seed)
        real_lin = _eval(lin, real_eval, eval_rows)
        fac = FactoredHead.zeros(len(real_train[0]))
        _train(fac, real_train, train_rows, epochs=epochs, lr=lr, seed=seed)
        real_fac = _eval(fac, real_eval, eval_rows)
        real_cos = knight_empty_cosine(real, mix_plies=mix)
        shuf_lin = []
        shuf_fac = []
        shuf_cos = []
        for shuf_seed in SHUFFLE_SEEDS:
            shuf = open_session(source="fixture", shuffled=True, seed=shuf_seed)
            st = _cache(shuf, train_rows, mix_plies=mix)
            se = _cache(shuf, eval_rows, mix_plies=mix)
            h = LinearHead.zeros(len(st[0]))
            _train(h, st, train_rows, epochs=epochs, lr=lr, seed=seed)
            ev = _eval(h, se, eval_rows)
            fh = FactoredHead.zeros(len(st[0]))
            _train(fh, st, train_rows, epochs=epochs, lr=lr, seed=seed)
            fev = _eval(fh, se, eval_rows)
            shuf_lin.append(ev)
            shuf_fac.append(fev)
            shuf_cos.append(knight_empty_cosine(shuf, mix_plies=mix))
        lin_deltas = [real_lin["accuracy"] - row["accuracy"] for row in shuf_lin]
        fac_deltas = [real_fac["accuracy"] - row["accuracy"] for row in shuf_fac]
        dmean, dlo, dhi = _mean_interval(lin_deltas)
        fmean, flo, fhi = _mean_interval(fac_deltas)
        rmean, rlo, rhi = _mean_interval(
            [real_lin["mean_target_rank"] - row["mean_target_rank"] for row in shuf_lin]
        )
        depths.append(
            {
                "mix_plies": mix,
                "readout": "reserved_pools" if mix == 0 else "hidden_mix",
                "synapses_used": mix > 0,
                "real_acc": real_lin["accuracy"],
                "real_mean_target_rank": real_lin["mean_target_rank"],
                "shuffle_acc_mean": float(np.mean([r["accuracy"] for r in shuf_lin])),
                "shuffle_mean_target_rank_mean": float(
                    np.mean([r["mean_target_rank"] for r in shuf_lin])
                ),
                "delta_acc_mean": dmean,
                "delta_acc_lo": dlo,
                "delta_acc_hi": dhi,
                "delta_rank_mean": rmean,
                "shuffle_seeds": list(SHUFFLE_SEEDS),
                "shuffle_acc": [r["accuracy"] for r in shuf_lin],
                "shuffle_mean_target_rank": [r["mean_target_rank"] for r in shuf_lin],
                "cosine_knight_vs_empty_real": real_cos,
                "cosine_knight_vs_empty_shuffle_mean": float(np.mean(shuf_cos)),
                "factored": {
                    "real_acc": real_fac["accuracy"],
                    "real_mean_target_rank": real_fac["mean_target_rank"],
                    "shuffle_acc_mean": float(np.mean([r["accuracy"] for r in shuf_fac])),
                    "shuffle_mean_target_rank_mean": float(
                        np.mean([r["mean_target_rank"] for r in shuf_fac])
                    ),
                    "delta_acc_mean": fmean,
                    "delta_acc_lo": flo,
                    "delta_acc_hi": fhi,
                },
            }
        )
    payload = {
        "experiment": "planes_mix",
        "graph": "fixture, not MaleCNS v1.0",
        "encoding": load_planes_cfg()["encoding"],
        "n_train": len(train_rows),
        "n_eval": len(eval_rows),
        "epochs": epochs,
        "lr": lr,
        "linear_head": "4096-way from-to, train_step unchanged",
        "factored_head": "64 from-logits + 64 to-logits, legal mask on the pair",
        "mix_depths": list(MIX_DEPTHS),
        "shuffle_seeds": list(SHUFFLE_SEEDS),
        "rows": depths,
        "caption": CAPTION,
        "pre_register": {
            "delta_near_zero_at_0_ply": "connectome unused; occupancy code only",
            "delta_negative_as_mix_increases": "connectome destroys the linear occupancy code",
            "delta_flat": "curriculum is the bottleneck",
            "delta_positive_at_1_dies_at_3": "mix depth is the knob, not pool count",
        },
        "games": 0,
        "elo": None,
        "gate2_quoted": False,
        "ethology_rerun": False,
        "hz_note": HZ_NOTE,
        "note": CAPTION,
    }
    LOGS.mkdir(parents=True, exist_ok=True)
    TABLE_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def write_mix_sweep() -> dict:
    return run_mix_sweep()
