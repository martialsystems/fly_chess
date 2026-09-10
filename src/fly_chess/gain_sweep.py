# Copyright (c) 2026 Martial Systems LLC
"""mV/contact × paint pulse on the 475-cell slice. Not a firing-rate table."""

from __future__ import annotations

import json

import numpy as np

from fly_chess.fetch import malecns_present
from fly_chess.lif import GAIN_PICK_NOTE, HZ_NOTE, LifConfig, LifNet, near_rest
from fly_chess.paint import circuit_gains, load_paint_cfg
from fly_chess.paths import LOGS
from fly_chess.rates import mean_hz
from fly_chess.session import ply_rates, session_from_graph

MV_GRID = (0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0)
PULSE_GRID = (18.0, 26.0)


def _role_hz(session, hz: np.ndarray) -> dict[str, float]:
    roles = session.resolved.roles
    return {
        "feed_mn": mean_hz(hz, roles["feed_mn"]),
        "gf_escape": mean_hz(hz, roles["gf_escape"]),
        "sugar_grn": mean_hz(hz, roles["sugar_grn"]),
        "loom_vpn": mean_hz(hz, roles["loom_vpn"]),
    }


def _drive(session, channel: str, pulse: float) -> np.ndarray:
    cfg = load_paint_cfg()
    if channel == "rest":
        return np.zeros(session.graph.n, dtype=np.float64)
    if channel == "sugar":
        i_ext = np.zeros(session.graph.n, dtype=np.float64)
        for i in session.resolved.roles["sugar_grn"]:
            i_ext[i] = pulse
        return i_ext
    if channel == "loom":
        i_ext = np.zeros(session.graph.n, dtype=np.float64)
        for i in session.resolved.roles["loom_vpn"]:
            i_ext[i] = pulse
        return i_ext
    return circuit_gains(session.graph, session.resolved, channel, cfg)


def evaluate_cell(session, *, mV_per_contact: float, pulse: float) -> dict:
    cfg = LifConfig.for_source("malecns")
    cfg.mV_per_contact = float(mV_per_contact)
    session.net = LifNet(session.graph, cfg)
    rest_hz = ply_rates(session, _drive(session, "rest", pulse))
    sugar_hz = ply_rates(session, _drive(session, "sugar", pulse))
    loom_hz = ply_rates(session, _drive(session, "loom", pulse))
    rest = _role_hz(session, rest_hz)
    sugar = _role_hz(session, sugar_hz)
    loom = _role_hz(session, loom_hz)
    split_ok = (
        sugar["feed_mn"] > rest["feed_mn"]
        and sugar["feed_mn"] > 1.0
        and near_rest(sugar["gf_escape"], rest["gf_escape"])
        and loom["gf_escape"] > rest["gf_escape"]
        and loom["gf_escape"] > 1.0
        and near_rest(loom["feed_mn"], rest["feed_mn"])
    )
    stacked = np.concatenate([rest_hz, sugar_hz, loom_hz])
    ceiling = cfg.saturate_hz
    saturate_frac = float(np.mean(stacked >= ceiling))
    max_hz = float(np.max(stacked)) if stacked.size else 0.0
    return {
        "mV_per_contact": mV_per_contact,
        "pulse": pulse,
        "split_ok": bool(split_ok),
        "saturate_frac": saturate_frac,
        "max_hz": max_hz,
        "rest": rest,
        "sugar": sugar,
        "loom": loom,
        "hz_note": HZ_NOTE,
    }


def run_gain_sweep(*, shuffle_seed: int = 1) -> dict:
    if not malecns_present():
        raise FileNotFoundError("MaleCNS files missing; run python -m fly_chess fetch")
    from fly_chess.import_malecns import load_identity_graph

    graph = load_identity_graph()
    session = session_from_graph(graph, shuffled=False, require="identity", source="malecns")
    cells = [
        evaluate_cell(session, mV_per_contact=mv, pulse=pulse)
        for mv in MV_GRID
        for pulse in PULSE_GRID
    ]
    ceiling = session.net.cfg.saturate_hz
    winners = [
        c
        for c in cells
        if c["split_ok"] and c["max_hz"] < ceiling and c["saturate_frac"] < 0.25
    ]
    # Smallest mV that works at every pulse in the grid.
    by_mv: dict[float, list[dict]] = {}
    for cell in cells:
        by_mv.setdefault(cell["mV_per_contact"], []).append(cell)
    picked = None
    for mv in MV_GRID:
        group = by_mv[mv]
        if all(
            c["split_ok"] and c["max_hz"] < ceiling and c["saturate_frac"] < 0.25
            for c in group
        ):
            picked = mv
            break
    return {
        "source": "malecns",
        "n_neurons": graph.n,
        "default_circuit_graph": "475_identity_slice",
        "mv_grid": list(MV_GRID),
        "pulse_grid": list(PULSE_GRID),
        "saturate_hz": ceiling,
        "cells": cells,
        "n_winners": len(winners),
        "picked_mV_per_contact": picked,
        "split_held": picked is not None,
        "hz_note": HZ_NOTE,
        "games": 0,
        "elo": None,
        "gate2_quoted": False,
        "note": (
            "Winning Hz is the injected pulse on an intact path, "
            "not a biological firing rate. " + GAIN_PICK_NOTE
        ),
        "readout_notes": [GAIN_PICK_NOTE],
    }


def write_gain_sweep() -> dict:
    payload = run_gain_sweep()
    LOGS.mkdir(parents=True, exist_ok=True)
    dest = LOGS / "malecns_gain_sweep.json"
    dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload
