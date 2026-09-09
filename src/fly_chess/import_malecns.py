# Copyright (c) 2026 Martial Systems LLC
"""MaleCNS v1.0 tables → Graph. Pytest uses a tiny in-memory frame, not the 1 GB file."""

from __future__ import annotations

import json

import numpy as np

from fly_chess.graph import Graph, Neuron
from fly_chess.paths import CONFIG


def load_nt_signs() -> dict[str, int]:
    raw = json.loads((CONFIG / "nt_signs.json").read_text(encoding="utf-8"))
    out: dict[str, int] = {}
    for name in raw["excitatory"]:
        out[name.casefold()] = 1
    for name in raw["inhibitory"]:
        out[name.casefold()] = -1
    return out


def nt_sign(name: object, table: dict[str, int], fallback: int = 1) -> int:
    if name is None or (isinstance(name, float) and np.isnan(name)):
        return fallback
    key = str(name).strip().casefold()
    return table.get(key, fallback)


def graph_from_records(
    bodies: list[dict],
    edges: list[tuple[int, int, float]],
    nt_map: dict[int, object] | None = None,
    *,
    nt_signs: dict[str, int] | None = None,
) -> Graph:
    """bodies: bodyId, type, superclass, status, side. Glia and empty superclass drop."""
    signs = nt_signs or load_nt_signs()
    nt_map = nt_map or {}
    kept: list[dict] = []
    for row in bodies:
        status = str(row.get("status") or "")
        superclass = row.get("superclass")
        has_super = superclass is not None and str(superclass).strip() not in ("", "nan")
        if status == "Glia" or not has_super:
            continue
        kept.append(row)
    if not kept:
        raise ValueError("no retained neurons")
    body_ids = [int(r["bodyId"]) for r in kept]
    index = {b: i for i, b in enumerate(body_ids)}
    neurons = [
        Neuron(
            id=i,
            type=str(kept[i].get("type") or ""),
            side=str(kept[i].get("side") or ""),
            sign=nt_sign(nt_map.get(body_ids[i]), signs),
            body_id=body_ids[i],
        )
        for i in range(len(kept))
    ]
    pre: list[int] = []
    post: list[int] = []
    wgt: list[float] = []
    for a, b, w in edges:
        if a not in index or b not in index:
            continue
        ia, ib = index[int(a)], index[int(b)]
        pre.append(ia)
        post.append(ib)
        wgt.append(float(w) * neurons[ia].sign)
    return Graph(
        neurons=neurons,
        pre=pre,
        post=post,
        weight=wgt,
        source="malecns_v1",
    )


def graph_from_frames(ann, nt, edges, *, nt_signs: dict[str, int] | None = None) -> Graph:
    """Build a Graph from pandas frames."""
    nt_map: dict[int, object] = {}
    if nt is not None and len(nt):
        body_col = "body" if "body" in nt.columns else "bodyId"
        nt_col = "consensus_nt" if "consensus_nt" in nt.columns else "neurotransmitter"
        for body, pred in zip(nt[body_col].tolist(), nt[nt_col].tolist()):
            nt_map[int(body)] = pred
    bodies = [ann.iloc[i].to_dict() for i in range(len(ann))]
    pre_col = "body_pre" if "body_pre" in edges.columns else "pre"
    post_col = "body_post" if "body_post" in edges.columns else "post"
    w_col = "weight" if "weight" in edges.columns else "synapse_count"
    edge_rows = list(
        zip(
            [int(x) for x in edges[pre_col].tolist()],
            [int(x) for x in edges[post_col].tolist()],
            [float(x) for x in edges[w_col].tolist()],
        )
    )
    return graph_from_records(bodies, edge_rows, nt_map, nt_signs=nt_signs)


def load_malecns_graph():
    from fly_chess.fetch import malecns_dir, malecns_present

    if not malecns_present():
        raise FileNotFoundError("MaleCNS files missing; run python -m fly_chess fetch")
    import pandas as pd

    root = malecns_dir()
    ann = pd.read_feather(root / "annotations.feather")
    nt = pd.read_feather(root / "neurotransmitters.feather")
    edges = pd.read_feather(root / "edges.feather")
    return graph_from_frames(ann, nt, edges)
