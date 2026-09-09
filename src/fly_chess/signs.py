# Copyright (c) 2026 Martial Systems LLC
"""Transmitter audit on the 475-cell slice. Do not flip unclear/monoamine."""

from __future__ import annotations

import json

import numpy as np

from fly_chess.fetch import malecns_present
from fly_chess.import_malecns import load_nt_signs, nt_sign
from fly_chess.lif import HZ_NOTE
from fly_chess.paths import LOGS
from fly_chess.resolve import IDENTITY_ROLES, resolve_graph


def _is_missing(name: object) -> bool:
    if name is None:
        return True
    if isinstance(name, float) and np.isnan(name):
        return True
    return str(name).strip() == ""


def _is_unknown(name: object) -> bool:
    return not _is_missing(name) and str(name).strip().casefold() == "unknown"


def _is_monoamine(name: object) -> bool:
    if _is_missing(name):
        return False
    key = str(name).strip().casefold()
    return key in {"monoamine", "dopamine", "serotonin", "octopamine"}


def run_signs() -> dict:
    if not malecns_present():
        raise FileNotFoundError("MaleCNS files missing; run python -m fly_chess fetch")
    import pandas as pd

    from fly_chess.fetch import malecns_dir
    from fly_chess.import_malecns import load_identity_graph

    graph = load_identity_graph()
    resolved = resolve_graph(graph, require="identity")
    nt = pd.read_feather(malecns_dir() / "neurotransmitters.feather")
    bcol = "body" if "body" in nt.columns else "bodyId"
    ncol = "consensus_nt" if "consensus_nt" in nt.columns else "neurotransmitter"
    nt_map: dict[int, object] = {}
    for body, pred in zip(nt[bcol].tolist(), nt[ncol].tolist()):
        nt_map[int(body)] = pred
    signs = load_nt_signs()
    fallback = 1
    required_ids = set()
    for role in IDENTITY_ROLES:
        required_ids.update(resolved.roles[role])
    n_edges = int(graph.pre.size)
    n_required_role_edges = 0
    n_unknown = 0
    n_missing = 0
    n_monoamine = 0
    n_plus = 0
    n_minus = 0
    for pre_i, w in zip(graph.pre.tolist(), graph.weight.tolist()):
        if pre_i not in required_ids:
            continue
        n_required_role_edges += 1
        body = graph.neurons[pre_i].body_id
        pred = nt_map.get(int(body)) if body is not None else None
        if _is_missing(pred):
            n_missing += 1
        if _is_unknown(pred):
            n_unknown += 1
        if _is_monoamine(pred):
            n_monoamine += 1
        signed = nt_sign(pred, signs, fallback=fallback)
        if signed > 0:
            n_plus += 1
        else:
            n_minus += 1
    return {
        "source": "malecns",
        "n_neurons": graph.n,
        "n_edges": n_edges,
        "required_roles": list(IDENTITY_ROLES),
        "n_required_role_edges": n_required_role_edges,
        "n_pre_nt_missing": n_missing,
        "n_pre_nt_unknown": n_unknown,
        "n_pre_monoamine": n_monoamine,
        "n_required_role_edges_plus": n_plus,
        "n_required_role_edges_minus": n_minus,
        "fallback_sign": fallback,
        "unclear_and_monoamine": "fallback +1, not flipped per synapse",
        "games": 0,
        "elo": None,
        "gate2_quoted": False,
        "hz_note": HZ_NOTE,
    }


def write_signs() -> dict:
    payload = run_signs()
    LOGS.mkdir(parents=True, exist_ok=True)
    dest = LOGS / "malecns_signs.json"
    dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload
