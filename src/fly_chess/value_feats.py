# Copyright (c) 2026 Martial Systems LLC
"""Mix-0 occupancy vs mix-1 hidden rates. Graph frozen."""

from __future__ import annotations

import hashlib

import chess
import numpy as np

from fly_chess.planes import currents, hidden_ids, occupancy_vector
from fly_chess.session import Session, mix_rates


def graph_fingerprint(session: Session) -> str:
    g = session.graph
    h = hashlib.sha256()
    h.update(np.asarray(g.pre).tobytes())
    h.update(np.asarray(g.post).tobytes())
    h.update(np.asarray(g.weight).tobytes())
    return h.hexdigest()


def mix0_features(session: Session, board: chess.Board) -> np.ndarray:
    return occupancy_vector(board, session.graph, session.resolved)


def mix1_features(session: Session, board: chess.Board, *, n_plies: int = 1) -> np.ndarray:
    i_ext = currents(board, session.graph, session.resolved)
    hz = mix_rates(session, i_ext, n_plies=n_plies)
    return hz[hidden_ids(session.graph)]
