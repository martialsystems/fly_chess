# Copyright (c) 2026 Martial Systems LLC
"""Experiment 2: twelve reserved piece-plane pools plus STM, castling, EP."""

from __future__ import annotations

import json
from pathlib import Path

import chess
import numpy as np

from fly_chess.graph import Graph
from fly_chess.paths import CONFIG, PLANES_MAP
from fly_chess.resolve import Resolved

PIECE_TO_PLANE = {
    (chess.WHITE, chess.PAWN): 0,
    (chess.WHITE, chess.KNIGHT): 1,
    (chess.WHITE, chess.BISHOP): 2,
    (chess.WHITE, chess.ROOK): 3,
    (chess.WHITE, chess.QUEEN): 4,
    (chess.WHITE, chess.KING): 5,
    (chess.BLACK, chess.PAWN): 6,
    (chess.BLACK, chess.KNIGHT): 7,
    (chess.BLACK, chess.BISHOP): 8,
    (chess.BLACK, chess.ROOK): 9,
    (chess.BLACK, chess.QUEEN): 10,
    (chess.BLACK, chess.KING): 11,
}
CASTLE_BITS = (
    ("CASTLE_H1", chess.BB_H1),
    ("CASTLE_A1", chess.BB_A1),
    ("CASTLE_H8", chess.BB_H8),
    ("CASTLE_A8", chess.BB_A8),
)


def load_planes_cfg() -> dict:
    return json.loads((CONFIG / "planes.json").read_text(encoding="utf-8"))


def plane_types(cfg: dict | None = None) -> list[str]:
    cfg = cfg or load_planes_cfg()
    return list(cfg["plane_types"])


def dump_planes_map(graph: Graph, resolved: Resolved, path: Path | None = None) -> dict:
    cfg = load_planes_cfg()
    types = plane_types(cfg)
    pools = []
    for typ in types:
        cells = [
            {"square": int(n.square), "neuron_id": n.id, "type": n.type}
            for n in graph.neurons
            if n.type == typ and n.square is not None
        ]
        cells.sort(key=lambda r: r["square"])
        pools.append({"type": typ, "n": len(cells), "cells": cells})
    payload = {
        "encoding": cfg["encoding"],
        "piece_order": cfg["piece_order"],
        "mix_plies": cfg["mix_plies"],
        "pools": pools,
        "photoreceptors": "off",
        "squares": sum((p["cells"] for p in pools), []),
    }
    dest = path or PLANES_MAP
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def _index_by_type_square(graph: Graph) -> dict[tuple[str, int | None], int]:
    out: dict[tuple[str, int | None], int] = {}
    for n in graph.neurons:
        out[(n.type, n.square)] = n.id
    return out


def currents(
    board: chess.Board,
    graph: Graph,
    resolved: Resolved,
    cfg: dict | None = None,
) -> np.ndarray:
    cfg = cfg or load_planes_cfg()
    types = plane_types(cfg)
    index = _index_by_type_square(graph)
    i_ext = np.zeros(graph.n, dtype=np.float64)
    occ = cfg["occupancy_current"]
    for sq, piece in board.piece_map().items():
        plane = PIECE_TO_PLANE[(piece.color, piece.piece_type)]
        nid = index.get((types[plane], int(sq)))
        if nid is not None:
            i_ext[nid] += occ
    stm = index.get(("STM", None))
    if stm is not None and board.turn == chess.WHITE:
        i_ext[stm] += cfg["side_to_move_current"]
    rights = board.castling_rights
    for typ, bit in CASTLE_BITS:
        nid = index.get((typ, None))
        if nid is not None and rights & bit:
            i_ext[nid] += cfg["castling_current"]
    if board.ep_square is not None:
        nid = index.get(("EP_FILE", chess.square_file(board.ep_square)))
        if nid is not None:
            i_ext[nid] += cfg["en_passant_current"]
    return i_ext


def readout_vector(hz: np.ndarray, resolved: Resolved) -> np.ndarray:
    ids = resolved.roles.get("readout_pool") or resolved.roles.get("reserved_input_pool")
    if not ids:
        return hz.copy()
    return hz[np.array(ids, dtype=np.int32)]


def plane_cell_rates(
    hz: np.ndarray,
    graph: Graph,
    cfg: dict | None = None,
) -> np.ndarray:
    """12 × 64 rates on the reserved plane pools. Used to test type identity."""
    cfg = cfg or load_planes_cfg()
    types = plane_types(cfg)
    out = np.zeros((12, 64), dtype=np.float64)
    for n in graph.neurons:
        if n.square is None:
            continue
        if n.type in types:
            out[types.index(n.type), int(n.square)] = hz[n.id]
    return out
