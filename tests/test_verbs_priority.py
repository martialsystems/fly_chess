# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import chess
import numpy as np

from fly_chess.puzzles import check_escape_position
from fly_chess.verbs import choose_move, cluster_rates
from fly_chess.session import open_session, ply_rates
from fly_chess.paint import currents as paint_currents


def test_check_prefers_flee_when_escape_cluster_is_high() -> None:
    session = open_session()
    board = check_escape_position()
    assert board.is_check()
    i_ext = paint_currents(board, session.graph, session.resolved)
    hz = ply_rates(session, i_ext)
    clusters = cluster_rates(hz, session.resolved)
    move, verb = choose_move(board, session.graph, session.resolved, hz)
    assert move in board.legal_moves
    board.push(move)
    if clusters["gf_escape"] >= 5.0:
        assert verb == "flee"
        assert not board.is_check()


def test_hanging_capture_uses_reserved_locus_not_grn_geometry() -> None:
    session = open_session()
    board = chess.Board("4k3/8/8/3n4/8/8/8/3QK3 w - - 0 1")
    i_ext = paint_currents(board, session.graph, session.resolved)
    d5 = [
        n
        for n in session.graph.neurons
        if n.type == "APP_LOCUS" and n.square == chess.D5
    ]
    assert d5
    assert i_ext[d5[0].id] > 0
    sugar = session.resolved.roles["sugar_grn"]
    assert np.allclose(i_ext[sugar], i_ext[sugar][0])
