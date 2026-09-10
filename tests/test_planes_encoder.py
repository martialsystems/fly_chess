# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import chess
import numpy as np

from fly_chess.fixture import PLANE_TYPES
from fly_chess.planes import currents, load_planes_cfg, plane_cell_rates, plane_types
from fly_chess.puzzles import load_split
from fly_chess.session import mix_rates, open_session


def test_typed_pools_are_twelve_by_sixty_four() -> None:
    session = open_session(source="fixture")
    types = plane_types()
    assert types == list(PLANE_TYPES)
    counts = {typ: 0 for typ in types}
    for n in session.graph.neurons:
        if n.type in counts:
            counts[n.type] += 1
    assert all(v == 64 for v in counts.values())
    assert any(n.type == "STM" for n in session.graph.neurons)


def test_piece_type_is_recoverable_from_plane_cells() -> None:
    session = open_session(source="fixture")
    board = chess.Board("4k3/8/8/3n4/8/8/8/3QK3 w - - 0 1")
    cfg = load_planes_cfg()
    i_ext = currents(board, session.graph, session.resolved, cfg)
    hz = mix_rates(session, i_ext, n_plies=int(cfg["mix_plies"]))
    rates = plane_cell_rates(hz, session.graph, cfg)
    from fly_chess.planes import PIECE_TO_PLANE

    for sq, piece in board.piece_map().items():
        plane = PIECE_TO_PLANE[(piece.color, piece.piece_type)]
        assert int(np.argmax(rates[:, int(sq)])) == plane


def test_split_file_has_no_overlap() -> None:
    split = load_split()
    assert set(split["train"]).isdisjoint(split["eval"])
    assert len(split["eval"]) >= 8


def test_head_table_is_shuffle_controlled() -> None:
    from pathlib import Path
    import json

    path = Path(__file__).resolve().parents[1] / "logs" / "planes_head.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["games"] == 0
    assert raw["elo"] is None
    assert raw["gate2_quoted"] is False
    assert raw["n_eval"] == 10
    assert raw["n_train"] == 30
    assert raw["real_acc"] == 0.5
    assert raw["shuffle_acc"] == 0.7
    assert abs(raw["delta"] - (raw["real_acc"] - raw["shuffle_acc"])) < 1e-12
    assert raw["delta"] < 0


def test_diagnose_logs_cosine_and_plane_identity() -> None:
    from pathlib import Path
    import json

    path = Path(__file__).resolve().parents[1] / "logs" / "planes_diagnose.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["real"]["plane_identity_acc"] == 1.0
    assert raw["shuffled"]["plane_identity_acc"] == 1.0
    assert raw["real"]["cosine_empty_vs_knight"] == 0.0
    assert raw["shuffled"]["cosine_empty_vs_knight"] > 0.5
    assert raw["games"] == 0
    assert raw["gate2_quoted"] is False
