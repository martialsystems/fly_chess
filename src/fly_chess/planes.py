# Copyright (c) 2026 Martial Systems LLC
"""Experiment 2: frozen piece-plane currents into reserved square cells."""

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


def load_planes_cfg() -> dict:
    return json.loads((CONFIG / "planes.json").read_text(encoding="utf-8"))


def dump_planes_map(graph: Graph, resolved: Resolved, path: Path | None = None) -> dict:
    cfg = load_planes_cfg()
    cells = []
    for i in resolved.roles["reserved_input_pool"]:
        n = graph.neurons[i]
        if n.type == "PLANE_SQ" and n.square is not None:
            cells.append(
                {
                    "square": int(n.square),
                    "neuron_id": i,
                    "piece": "12-dim occupancy current",
                    "current": cfg["occupancy_current"],
                }
            )
    cells.sort(key=lambda r: r["square"])
    payload = {
        "encoding": "one reserved cell per square; current is occupancy_current * plane_index_weight",
        "piece_order": cfg["piece_order"],
        "squares": cells,
        "photoreceptors": "off",
    }
    dest = path or PLANES_MAP
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def currents(
    board: chess.Board,
    graph: Graph,
    resolved: Resolved,
    cfg: dict | None = None,
) -> np.ndarray:
    cfg = cfg or load_planes_cfg()
    i_ext = np.zeros(graph.n, dtype=np.float64)
    by_sq = {}
    for i in resolved.roles["reserved_input_pool"]:
        n = graph.neurons[i]
        if n.type == "PLANE_SQ" and n.square is not None:
            by_sq[int(n.square)] = i
    occ = cfg["occupancy_current"]
    for sq, piece in board.piece_map().items():
        plane = PIECE_TO_PLANE[(piece.color, piece.piece_type)]
        nid = by_sq.get(sq)
        if nid is not None:
            i_ext[nid] += occ * (1.0 + 0.15 * plane)
    stm = by_sq.get(0)
    if stm is not None and board.turn == chess.WHITE:
        i_ext[stm] += cfg["side_to_move_current"]
    rights = board.castling_rights
    if rights & chess.BB_H1 and 1 in by_sq:
        i_ext[by_sq[1]] += cfg["castling_current"]
    if rights & chess.BB_A1 and 2 in by_sq:
        i_ext[by_sq[2]] += cfg["castling_current"]
    if rights & chess.BB_H8 and 61 in by_sq:
        i_ext[by_sq[61]] += cfg["castling_current"]
    if rights & chess.BB_A8 and 62 in by_sq:
        i_ext[by_sq[62]] += cfg["castling_current"]
    if board.ep_square is not None and board.ep_square in by_sq:
        i_ext[by_sq[board.ep_square]] += cfg["en_passant_current"]
    return i_ext


def readout_vector(hz: np.ndarray, resolved: Resolved) -> np.ndarray:
    ids = resolved.roles.get("readout_pool") or resolved.roles.get("reserved_input_pool")
    if not ids:
        return hz.copy()
    return hz[np.array(ids, dtype=np.int32)]
