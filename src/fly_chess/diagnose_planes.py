# Copyright (c) 2026 Martial Systems LLC
"""Readout diagnostics on real vs shuffled fixture. Not a Gate 2 score."""

from __future__ import annotations

import json
from collections import Counter

import chess
import numpy as np


from fly_chess.lif import HZ_NOTE
from fly_chess.match import load_gates
from fly_chess.paths import LOGS
from fly_chess.planes import currents as plane_currents
from fly_chess.planes import load_planes_cfg, plane_cell_rates, readout_vector
from fly_chess.puzzles import split_positions
from fly_chess.session import Session, mix_rates, open_session
from fly_chess.train_planes import _feat, eval_head, train_head

DIAG_PATH = LOGS / "planes_diagnose.json"


def _entropy(counts: Counter) -> float:
    n = sum(counts.values())
    if n <= 0:
        return 0.0
    ent = 0.0
    for c in counts.values():
        p = c / n
        if p > 0:
            ent -= p * np.log2(p)
    return float(ent)


def mutual_information(xs: list[int], ys: list[int]) -> float:
    joint: Counter = Counter(zip(xs, ys))
    hx = _entropy(Counter(xs))
    hy = _entropy(Counter(ys))
    hxy = _entropy(joint)
    return hx + hy - hxy


def _hidden_vec(session: Session, board: chess.Board, mix_plies: int) -> np.ndarray:
    i_ext = plane_currents(board, session.graph, session.resolved)
    hz = mix_rates(session, i_ext, n_plies=mix_plies)
    ids = [n.id for n in session.graph.neurons if n.type == "HIDDEN"]
    return hz[np.array(ids, dtype=np.int32)]


def plane_identity_acc(session: Session, board: chess.Board, mix_plies: int) -> float:
    i_ext = plane_currents(board, session.graph, session.resolved)
    hz = mix_rates(session, i_ext, n_plies=mix_plies)
    rates = plane_cell_rates(hz, session.graph)
    hits = 0
    n = 0
    from fly_chess.planes import PIECE_TO_PLANE

    for sq, piece in board.piece_map().items():
        plane = PIECE_TO_PLANE[(piece.color, piece.piece_type)]
        pred = int(np.argmax(rates[:, int(sq)]))
        hits += int(pred == plane)
        n += 1
    return hits / max(n, 1)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def arm_report(session: Session, *, mix_plies: int, epochs: int, seed: int) -> dict:
    head = train_head(session, epochs=epochs, lr=0.08, mix_plies=mix_plies, seed=seed)
    ev = eval_head(session, head, mix_plies=mix_plies, arm="eval")
    train = split_positions(arm="train")
    empty = chess.Board("4k3/8/8/8/8/8/8/4K3 w - - 0 1")
    knight = empty.copy()
    knight.set_piece_at(chess.D4, chess.Piece.from_symbol("N"))
    bishop = empty.copy()
    bishop.set_piece_at(chess.D4, chess.Piece.from_symbol("B"))
    h_empty = _hidden_vec(session, empty, mix_plies)
    h_knight = _hidden_vec(session, knight, mix_plies)
    h_bishop = _hidden_vec(session, bishop, mix_plies)
    start = chess.Board()
    froms: list[int] = []
    tos: list[int] = []
    pieces: list[int] = []
    caps: list[int] = []
    hottest: list[int] = []
    ident = []
    for board, target, _kind in train:
        feat = _feat(session, board.copy(), mix_plies=mix_plies)
        hidden = _hidden_vec(session, board.copy(), mix_plies)
        ident.append(plane_identity_acc(session, board, mix_plies))
        froms.append(int(target.from_square))
        tos.append(int(target.to_square))
        piece = board.piece_at(target.from_square)
        pieces.append(int(piece.piece_type) if piece else 0)
        caps.append(int(board.is_capture(target)))
        hottest.append(int(np.argmax(hidden)) if hidden.size else 0)
        _ = feat
        _ = head
    return {
        "accuracy": ev["accuracy"],
        "mean_target_rank": ev["mean_target_rank"],
        "plane_identity_acc": float(np.mean(ident)) if ident else 0.0,
        "cosine_empty_vs_knight": cosine(h_empty, h_knight),
        "cosine_knight_vs_bishop": cosine(h_knight, h_bishop),
        "mi_hottest_from": mutual_information(hottest, froms),
        "mi_hottest_to": mutual_information(hottest, tos),
        "mi_hottest_piece": mutual_information(hottest, pieces),
        "mi_hottest_capture": mutual_information(hottest, caps),
        "n_train": len(train),
        "n_eval": ev["n"],
    }


def run_diagnose(*, epochs: int = 8, seed: int = 0) -> dict:
    cfg = load_planes_cfg()
    mix_plies = int(cfg["mix_plies"])
    gates = load_gates()
    real = open_session(source="fixture", shuffled=False)
    shuf = open_session(source="fixture", shuffled=True, seed=int(gates["shuffle_seed"]))
    real_rep = arm_report(real, mix_plies=mix_plies, epochs=epochs, seed=seed)
    shuf_rep = arm_report(shuf, mix_plies=mix_plies, epochs=epochs, seed=seed)
    payload = {
        "experiment": "planes_diagnose",
        "graph": "fixture, not MaleCNS v1.0",
        "encoding": cfg["encoding"],
        "mix_plies": mix_plies,
        "real": real_rep,
        "shuffled": shuf_rep,
        "delta_acc": float(real_rep["accuracy"]) - float(shuf_rep["accuracy"]),
        "plane_identity_real_gt_shuffled": (
            real_rep["plane_identity_acc"] > shuf_rep["plane_identity_acc"]
        ),
        "games": 0,
        "elo": None,
        "gate2_quoted": False,
        "hz_note": HZ_NOTE,
        "note": (
            "If shuffled rates are as linearly separable as real rates, "
            "more gradient steps will not help. Fix the encoder first."
        ),
    }
    LOGS.mkdir(parents=True, exist_ok=True)
    DIAG_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def write_diagnose() -> dict:
    return run_diagnose()
