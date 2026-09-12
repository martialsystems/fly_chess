# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import json
from pathlib import Path

import chess

from fly_chess.hand_eval import MATE
from fly_chess.selfplay_value import backup_white, run_selfplay, terminal_white
import numpy as np

from fly_chess.value_feats import graph_fingerprint
from fly_chess.value_head import LinearValue
from fly_chess.session import open_session

REPO = Path(__file__).resolve().parents[1]


def test_terminal_return_is_white_centric() -> None:
    mate = chess.Board("6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 1")
    mate.push(chess.Move.from_uci("e1e8"))
    assert mate.is_checkmate()
    assert terminal_white(mate) == 1.0
    assert backup_white(mate) == 1.0
    board = chess.Board()
    y = backup_white(board)
    assert abs(y) < 0.05
    assert MATE == 100.0


def test_linear_value_save_load_roundtrip(tmp_path: Path) -> None:
    rng = np.random.default_rng(0)
    X = rng.normal(size=(32, 8))
    y = X[:, 0] - 0.3 * X[:, 1]
    head = LinearValue.fit(X, y, l2=0.01)
    path = tmp_path / "v.npz"
    head.save(path)
    loaded = LinearValue.load(path)
    assert np.allclose(head.w, loaded.w)
    assert abs(head.b - loaded.b) < 1e-12
    x = X[0]
    assert abs(head.predict(x) - loaded.predict(x)) < 1e-12


def test_selfplay_source_stays_mix0() -> None:
    src = (REPO / "src" / "fly_chess" / "selfplay_value.py").read_text(encoding="utf-8")
    assert "LinearHead" not in src
    assert "FactoredHead" not in src
    assert "labeled_positions" not in src
    assert "mix1_features" not in src
    assert "dopamine" not in src.lower()


def test_tiny_selfplay_freezes_graph_and_does_not_claim_wiring() -> None:
    session = open_session(source="fixture")
    fp = graph_fingerprint(session)
    payload = run_selfplay(tiny=True, n_play=0)
    assert payload["graph_frozen"] is True
    assert payload["synapses_used"] is False
    assert payload["wiring_helped"] is False
    assert payload["unfreeze_allowed"] is False
    assert payload["elo"] is None
    assert payload["mix_plies"] == 0
    assert payload["n_train_positions"] >= 1
    assert payload["n_eval_positions"] >= 1
    assert payload["holdout"] == "game_id"
    assert payload["fingerprint"] == fp
    eth = json.loads((REPO / "logs" / "ethology_gate.json").read_text(encoding="utf-8"))
    assert eth["real"]["score"] == 0.4875
    val = json.loads((REPO / "logs" / "value_lock.json").read_text(encoding="utf-8"))
    assert val["A"]["games"]["score"] == 0.91
    assert val["wiring_helped"] is False
