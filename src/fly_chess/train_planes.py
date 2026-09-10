# Copyright (c) 2026 Martial Systems LLC
"""Train the linear head on a locked FEN split. Graph stays frozen."""

from __future__ import annotations

import json

import chess
import numpy as np

from fly_chess.head import LinearHead
from fly_chess.lif import HZ_NOTE
from fly_chess.match import load_gates
from fly_chess.paths import LOGS
from fly_chess.planes import currents as plane_currents
from fly_chess.planes import load_planes_cfg, readout_vector
from fly_chess.puzzles import split_positions
from fly_chess.session import Session, mix_rates, open_session

HEAD_PATH = LOGS / "planes_head.npz"
TABLE_PATH = LOGS / "planes_head.json"


def _feat(session: Session, board: chess.Board, *, mix_plies: int) -> np.ndarray:
    i_ext = plane_currents(board, session.graph, session.resolved)
    hz = mix_rates(session, i_ext, n_plies=mix_plies)
    return readout_vector(hz, session.resolved)


def train_head(
    session: Session,
    *,
    epochs: int,
    lr: float,
    mix_plies: int,
    seed: int = 0,
) -> LinearHead:
    train = split_positions(arm="train")
    feat0 = _feat(session, train[0][0], mix_plies=mix_plies)
    rng = np.random.default_rng(seed)
    head = LinearHead.zeros(len(feat0))
    order = list(range(len(train)))
    for _ in range(epochs):
        rng.shuffle(order)
        for i in order:
            board, target, _kind = train[i]
            feat = _feat(session, board.copy(), mix_plies=mix_plies)
            head.train_step(feat, target, board, lr=lr)
    return head


def eval_head(
    session: Session,
    head: LinearHead,
    *,
    mix_plies: int,
    arm: str = "eval",
) -> dict:
    rows = split_positions(arm=arm)
    correct = 0
    ranks: list[int] = []
    for board, target, _kind in rows:
        feat = _feat(session, board.copy(), mix_plies=mix_plies)
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


def run_train(*, epochs: int | None = None, lr: float = 0.08, seed: int = 0) -> dict:
    cfg = load_planes_cfg()
    mix_plies = int(cfg["mix_plies"])
    gates = load_gates()
    if epochs is None:
        n_train = len(split_positions(arm="train"))
        epochs = max(8, int(gates["gate1"]["n_train"]) // max(n_train, 1))
    real_session = open_session(source="fixture", shuffled=False)
    shuf_session = open_session(source="fixture", shuffled=True, seed=int(gates["shuffle_seed"]))
    real_head = train_head(real_session, epochs=epochs, lr=lr, mix_plies=mix_plies, seed=seed)
    shuf_head = train_head(shuf_session, epochs=epochs, lr=lr, mix_plies=mix_plies, seed=seed)
    real_eval = eval_head(real_session, real_head, mix_plies=mix_plies, arm="eval")
    shuf_eval = eval_head(shuf_session, shuf_head, mix_plies=mix_plies, arm="eval")
    delta = float(real_eval["accuracy"]) - float(shuf_eval["accuracy"])
    LOGS.mkdir(parents=True, exist_ok=True)
    real_head.save(HEAD_PATH)
    payload = {
        "experiment": "planes",
        "graph": "fixture, not MaleCNS v1.0",
        "encoding": cfg["encoding"],
        "mix_plies": mix_plies,
        "epochs": epochs,
        "lr": lr,
        "n_train": len(split_positions(arm="train")),
        "n_eval": real_eval["n"],
        "real_acc": real_eval["accuracy"],
        "shuffle_acc": shuf_eval["accuracy"],
        "delta": delta,
        "real_mean_target_rank": real_eval["mean_target_rank"],
        "shuffle_mean_target_rank": shuf_eval["mean_target_rank"],
        "real_correct": real_eval["correct"],
        "shuffle_correct": shuf_eval["correct"],
        "head": "logs/planes_head.npz",
        "games": 0,
        "elo": None,
        "gate2_quoted": False,
        "hz_note": HZ_NOTE,
        "note": (
            "Gate 1 figure is real_acc minus shuffle_acc on held-out FENs. "
            "Same head, same split, degree-and-sign shuffle of the same graph."
        ),
    }
    TABLE_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def write_train() -> dict:
    return run_train()
