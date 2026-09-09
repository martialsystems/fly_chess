# Copyright (c) 2026 Martial Systems LLC
"""Experiment 1: board as food/loom fields on synthetic loci plus global gains."""

from __future__ import annotations

import json
from pathlib import Path

import chess
import numpy as np

from fly_chess.board_feats import (
    hanging_enemy_squares,
    hanging_own_squares,
    open_files_to_king,
    passed_pawns,
    poisoned_captures,
)
from fly_chess.graph import Graph
from fly_chess.paths import CONFIG, ETHOLOGY_MAP
from fly_chess.resolve import Resolved


def load_paint_cfg() -> dict:
    return json.loads((CONFIG / "ethology_paint.json").read_text(encoding="utf-8"))


def dump_ethology_map(graph: Graph, resolved: Resolved, path: Path | None = None) -> dict:
    """Square identity is on reserved loci, not on LB3c geometry."""
    app = _locus_table(graph, resolved, "APP_LOCUS")
    av = _locus_table(graph, resolved, "AV_LOCUS")
    payload = {
        "spatial_identity": "synthetic_loci",
        "sugar_geometry": "global_gain_only",
        "loom_geometry": "global_gain_plus_weak_LPLC2_columns",
        "appetitive_loci": app,
        "aversive_loci": av,
        "sugar_grn": resolved.roles.get("sugar_grn") or [],
        "loom_vpn": resolved.roles.get("loom_vpn") or [],
        "aversive_grn": resolved.roles.get("aversive_grn") or [],
        "note": (
            "Labellar GRNs are not an 8x8 retina. Hottest square is argmax of "
            "reserved locus rates. Real GRNs/LPLC2 get a global gain."
        ),
    }
    dest = path or ETHOLOGY_MAP
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def _locus_table(graph: Graph, resolved: Resolved, type_name: str) -> list[dict]:
    rows = []
    for i in resolved.roles["reserved_input_pool"]:
        n = graph.neurons[i]
        if n.type != type_name or n.square is None:
            continue
        rows.append({"square": int(n.square), "neuron_id": i, "type": n.type, "current": None})
    rows.sort(key=lambda r: r["square"])
    return rows


def currents(
    board: chess.Board,
    graph: Graph,
    resolved: Resolved,
    cfg: dict | None = None,
) -> np.ndarray:
    cfg = cfg or load_paint_cfg()
    i_ext = np.zeros(graph.n, dtype=np.float64)
    us = board.turn
    app_by_sq = _by_square(graph, resolved, "APP_LOCUS")
    av_by_sq = _by_square(graph, resolved, "AV_LOCUS")

    hanging_e = hanging_enemy_squares(board, us)
    hanging_o = hanging_own_squares(board, us)
    if hanging_e:
        _add_ids(i_ext, resolved.roles["sugar_grn"], cfg["sugar_global_gain"])
        for sq in hanging_e:
            if sq in app_by_sq:
                i_ext[app_by_sq[sq]] += cfg["appetitive_locus_current"]
    for sq in passed_pawns(board, us):
        if sq in app_by_sq:
            i_ext[app_by_sq[sq]] += cfg["appetitive_locus_current"] * cfg["passed_pawn_scale"]

    threat = hanging_o or board.is_check()
    if threat or open_files_to_king(board, us):
        _add_ids(i_ext, resolved.roles["loom_vpn"], cfg["loom_global_gain"])
        if board.is_check():
            king = board.king(us)
            if king is not None and king in av_by_sq:
                i_ext[av_by_sq[king]] += cfg["aversive_locus_current"]
        for sq in hanging_o:
            if sq in av_by_sq:
                i_ext[av_by_sq[sq]] += cfg["aversive_locus_current"]
        for sq in open_files_to_king(board, us):
            if sq in av_by_sq:
                i_ext[av_by_sq[sq]] += 0.4 * cfg["aversive_locus_current"]

    poisoned = poisoned_captures(board, us)
    if poisoned:
        _add_ids(i_ext, resolved.roles["aversive_grn"], cfg["aversive_global_gain"])
        for sq in poisoned:
            if sq in av_by_sq:
                i_ext[av_by_sq[sq]] += 0.5 * cfg["aversive_locus_current"]

    _add_ids(i_ext, resolved.roles.get("arousal") or [], cfg["arousal_current"])
    return i_ext


def _by_square(graph: Graph, resolved: Resolved, type_name: str) -> dict[int, int]:
    out: dict[int, int] = {}
    for i in resolved.roles["reserved_input_pool"]:
        n = graph.neurons[i]
        if n.type == type_name and n.square is not None:
            out[int(n.square)] = i
    return out


def _add_ids(i_ext: np.ndarray, ids: list[int], value: float) -> None:
    for i in ids:
        i_ext[i] += value


def locus_rates(graph: Graph, resolved: Resolved, hz: np.ndarray, type_name: str) -> np.ndarray:
    rates = np.zeros(64, dtype=np.float64)
    for i in resolved.roles["reserved_input_pool"]:
        n = graph.neurons[i]
        if n.type == type_name and n.square is not None:
            rates[int(n.square)] = hz[i]
    return rates
