# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

from pathlib import Path

import chess
import numpy as np

from fly_chess.child_value import pick_child
from fly_chess.dense_catalog import build_catalog
from fly_chess.hand_eval import MATE, hand_eval
from fly_chess.planes import occupancy_vector
from fly_chess.puzzles import labeled_positions
from fly_chess.session import open_session
from fly_chess.value_feats import graph_fingerprint, mix0_features, mix1_features
from fly_chess.value_head import LinearValue, MLPValue

REPO = Path(__file__).resolve().parents[1]
HANGING_Q = "4k3/8/8/3q4/8/8/8/3QK3 w - - 0 1"


def test_hand_eval_is_white_centric_material() -> None:
    board = chess.Board(HANGING_Q)
    assert hand_eval(board) == 0.0
    board.push(chess.Move.from_uci("d1d5"))
    assert hand_eval(board) == 9.0
    mate = chess.Board("6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 1")
    mate.push(chess.Move.from_uci("e1e8"))
    assert mate.is_checkmate()
    assert hand_eval(mate) == MATE


def test_child_scoring_takes_hanging_queen() -> None:
    board = chess.Board(HANGING_Q)
    move = pick_child(board, hand_eval)
    assert move.uci() == "d1d5"
    legal = list(board.legal_moves)
    assert move in legal
    assert len(legal) > 1


def test_occupancy_is_781_and_skips_lif() -> None:
    session = open_session(source="fixture")
    board = chess.Board()
    feat = occupancy_vector(board, session.graph, session.resolved)
    assert feat.shape == (781,)
    src = (REPO / "src" / "fly_chess" / "value_feats.py").read_text(encoding="utf-8")
    mix0_block = src.split("def mix0_features")[1].split("def mix1_features")[0]
    assert "mix_rates" not in mix0_block
    assert mix0_features(session, board).shape == (781,)


def _material_board(white: str, black: str | None, wsq: int, bsq: int) -> chess.Board:
    board = chess.Board()
    board.clear()
    board.set_piece_at(chess.E1, chess.Piece.from_symbol("K"))
    board.set_piece_at(chess.E8, chess.Piece.from_symbol("k"))
    board.set_piece_at(wsq, chess.Piece.from_symbol(white))
    if black is not None:
        board.set_piece_at(bsq, chess.Piece.from_symbol(black))
    board.turn = chess.WHITE
    return board


def test_mix0_ridge_recovers_hanging_capture() -> None:
    session = open_session(source="fixture")
    xs = []
    ys = []
    pieces = ("Q", "R", "B", "N", "P")
    for i, w in enumerate(pieces):
        for j, b in enumerate(pieces):
            board = _material_board(w, b.lower(), chess.A1 + i, chess.A8 - j)
            xs.append(mix0_features(session, board))
            ys.append(hand_eval(board))
            for mv in board.legal_moves:
                if not board.is_capture(mv):
                    continue
                board.push(mv)
                xs.append(mix0_features(session, board))
                ys.append(hand_eval(board))
                board.pop()
    hang = chess.Board(HANGING_Q)
    xs.append(mix0_features(session, hang))
    ys.append(hand_eval(hang))
    for mv in hang.legal_moves:
        hang.push(mv)
        xs.append(mix0_features(session, hang))
        ys.append(hand_eval(hang))
        hang.pop()
    head = LinearValue.fit(np.stack(xs), np.asarray(ys), l2=0.01, zscore=False)
    board = chess.Board(HANGING_Q)
    move = pick_child(board, lambda b: head.predict(mix0_features(session, b)))
    assert move.uci() == "d1d5"
    fp = graph_fingerprint(session)
    _ = head.predict(mix0_features(session, board))
    assert graph_fingerprint(session) == fp


def test_catalog_holds_out_by_game_not_hanging_puzzles() -> None:
    split = build_catalog(
        n_games=12, positions_per_game=4, max_ply=32, seed=0, holdout_frac=0.25
    )
    train_ids = {r.game_id for r in split["train"]}
    eval_ids = {r.game_id for r in split["eval"]}
    assert train_ids.isdisjoint(eval_ids)
    assert split["train"] and split["eval"]
    phases = {r.phase for r in split["train"] + split["eval"]}
    assert "opening" in phases
    hanging_fens = {b.fen() for b, _m, k in labeled_positions() if k == "hanging"}
    catalog_fens = {r.fen for r in split["train"] + split["eval"]}
    assert not catalog_fens <= hanging_fens
    assert len(catalog_fens & hanging_fens) <= 2


def test_mlp_is_two_layer() -> None:
    rng = np.random.default_rng(0)
    X = rng.normal(size=(64, 16))
    y = X[:, 0] - 0.5 * X[:, 1]
    mlp = MLPValue.fit(X, y, hidden=8, epochs=20, lr=0.05, batch=16, seed=0)
    assert mlp.w1.shape == (8, 16)
    assert mlp.w2.shape == (8,)
    pred = mlp.predict_many(X)
    assert pred.shape == (64,)
    assert float(np.corrcoef(pred, y)[0, 1]) > 0.5


def test_mix1_hidden_is_64_and_uses_synapses() -> None:
    session = open_session(source="fixture")
    board = chess.Board()
    feat = mix1_features(session, board, n_plies=1)
    assert feat.shape == (64,)
    assert float(np.max(np.abs(feat))) == 0.0
    shuf = open_session(source="fixture", shuffled=True, seed=1)
    feat_s = mix1_features(shuf, board, n_plies=1)
    assert feat_s.shape == (64,)
    assert float(np.max(np.abs(feat_s))) > 0.0
