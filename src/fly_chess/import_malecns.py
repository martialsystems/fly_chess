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


def _ann_columns(ann) -> tuple[str, str, str, str]:
    body = "bodyId" if "bodyId" in ann.columns else "body"
    typ = "type" if "type" in ann.columns else "cell_type"
    side = "side" if "side" in ann.columns else None
    status = "status" if "status" in ann.columns else None
    return body, typ, side or "", status or ""


def load_identity_graph(*, hops: int = 1):
    """Identity cells plus disynaptic bridges: sugar→X→MN9 and LPLC2→DNp01.

    A 2-hop neighborhood of LPLC2 is almost the whole brain. Do not use that.
    """
    from fly_chess.aliases import load_alias_table, role_specs
    from fly_chess.fetch import malecns_dir, malecns_present
    from fly_chess.resolve import IDENTITY_ROLES, _match

    if not malecns_present():
        raise FileNotFoundError("MaleCNS files missing; run python -m fly_chess fetch")
    import pandas as pd
    import pyarrow as pa
    import pyarrow.ipc as ipc

    root = malecns_dir()
    ann = pd.read_feather(root / "annotations.feather")
    nt = pd.read_feather(root / "neurotransmitters.feather")
    specs = {s.name: s for s in role_specs(load_alias_table())}
    seeds: dict[str, list[int]] = {r: [] for r in IDENTITY_ROLES}
    meta: dict[int, dict] = {}
    for typ, bid, status, sc, side in zip(
        ann["type"].tolist(),
        ann["bodyId"].tolist(),
        ann["status"].tolist(),
        ann["superclass"].tolist(),
        (ann["somaSide"] if "somaSide" in ann.columns else ann["type"]).tolist(),
    ):
        if status == "Glia" or sc is None or str(sc).strip() in ("", "nan"):
            continue
        typ_s = "" if typ is None else str(typ)
        bid_i = int(bid)
        meta[bid_i] = {
            "bodyId": bid_i,
            "type": typ_s,
            "side": "" if side is None else str(side),
            "superclass": sc,
            "status": status,
        }
        for role in IDENTITY_ROLES:
            if _match(typ_s, specs[role]):
                seeds[role].append(bid_i)
    missing = [r for r, ids in seeds.items() if not ids]
    if missing:
        raise RuntimeError(f"identity roles empty: {missing}")

    sugar = np.array(seeds["sugar_grn"], dtype=np.int64)
    mn9 = np.array(seeds["feed_mn"], dtype=np.int64)
    loom = np.array(seeds["loom_vpn"], dtype=np.int64)
    gf = np.array(seeds["gf_escape"], dtype=np.int64)
    sugar_posts: list[np.ndarray] = []
    mn9_pres: list[np.ndarray] = []
    reader = ipc.open_file(pa.memory_map(str(root / "edges.feather"), "r"))
    for i in range(reader.num_record_batches):
        batch = reader.get_batch(i)
        pre = batch.column("body_pre").to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
        post = batch.column("body_post").to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
        sugar_posts.append(post[np.isin(pre, sugar)])
        mn9_pres.append(pre[np.isin(post, mn9)])
    bridges = np.intersect1d(
        np.unique(np.concatenate(sugar_posts)) if sugar_posts else np.array([], dtype=np.int64),
        np.unique(np.concatenate(mn9_pres)) if mn9_pres else np.array([], dtype=np.int64),
    )
    keep = set(int(x) for x in sugar.tolist())
    keep.update(int(x) for x in mn9.tolist())
    keep.update(int(x) for x in loom.tolist())
    keep.update(int(x) for x in gf.tolist())
    keep.update(int(x) for x in bridges.tolist())
    keep_arr = np.array(sorted(keep), dtype=np.int64)

    edges: list[tuple[int, int, float]] = []
    reader = ipc.open_file(pa.memory_map(str(root / "edges.feather"), "r"))
    for i in range(reader.num_record_batches):
        batch = reader.get_batch(i)
        pre = batch.column("body_pre").to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
        post = batch.column("body_post").to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
        w = batch.column("weight").to_numpy(zero_copy_only=False)
        mask = np.isin(pre, keep_arr) & np.isin(post, keep_arr)
        for a, bpost, wt in zip(pre[mask].tolist(), post[mask].tolist(), w[mask].tolist()):
            edges.append((int(a), int(bpost), float(wt)))
    nt_map: dict[int, object] = {}
    if nt is not None and len(nt):
        bcol = "body" if "body" in nt.columns else "bodyId"
        ncol = "consensus_nt" if "consensus_nt" in nt.columns else "neurotransmitter"
        for body, pred in zip(nt[bcol].tolist(), nt[ncol].tolist()):
            nt_map[int(body)] = pred
    bodies = [meta[i] for i in sorted(keep) if i in meta]
    graph = graph_from_records(bodies, edges, nt_map)
    graph.source = (
        f"malecns_v1_identity seeds={ {k: len(v) for k, v in seeds.items()} } "
        f"bridges={int(bridges.size)} n={graph.n}"
    )
    return graph


def _edges_reader():
    import pyarrow as pa
    import pyarrow.ipc as ipc

    from fly_chess.fetch import malecns_dir, malecns_present

    if not malecns_present():
        raise FileNotFoundError("MaleCNS files missing; run python -m fly_chess fetch")
    root = malecns_dir()
    return ipc.open_file(pa.memory_map(str(root / "edges.feather"), "r")), root


def role_body_ids(roles: tuple[str, ...]) -> tuple[dict[str, list[int]], dict[int, dict]]:
    """Map requested roles to retained bodyIds. Used by identity and hop budgets."""
    from fly_chess.aliases import load_alias_table, role_specs
    from fly_chess.fetch import malecns_dir, malecns_present
    from fly_chess.resolve import _match

    if not malecns_present():
        raise FileNotFoundError("MaleCNS files missing; run python -m fly_chess fetch")
    import pandas as pd

    ann = pd.read_feather(malecns_dir() / "annotations.feather")
    specs = {s.name: s for s in role_specs(load_alias_table())}
    seeds: dict[str, list[int]] = {r: [] for r in roles}
    meta: dict[int, dict] = {}
    side_col = ann["somaSide"] if "somaSide" in ann.columns else ann["type"]
    for typ, bid, status, sc, side in zip(
        ann["type"].tolist(),
        ann["bodyId"].tolist(),
        ann["status"].tolist(),
        ann["superclass"].tolist(),
        side_col.tolist(),
    ):
        if status == "Glia" or sc is None or str(sc).strip() in ("", "nan"):
            continue
        typ_s = "" if typ is None else str(typ)
        bid_i = int(bid)
        meta[bid_i] = {
            "bodyId": bid_i,
            "type": typ_s,
            "side": "" if side is None else str(side),
            "superclass": sc,
            "status": status,
        }
        for role in roles:
            if _match(typ_s, specs[role]):
                seeds[role].append(bid_i)
    missing = [r for r, ids in seeds.items() if not ids]
    if missing:
        raise RuntimeError(f"roles empty: {missing}")
    return seeds, meta


def outgoing_expand(
    seed_ids: list[int],
    *,
    hops: int,
    n_cap: int | None = None,
) -> dict:
    """Outgoing BFS from seeds. Caps the keep set; does not load the full brain."""
    reader, _root = _edges_reader()
    keep = {int(x) for x in seed_ids}
    frontier = set(keep)
    hop_sizes = [len(keep)]
    keep_by_hop = [set(keep)]
    capped = False
    for _hop in range(hops):
        if n_cap is not None and len(keep) >= n_cap:
            capped = True
            break
        nxt: set[int] = set()
        keep_arr = np.array(sorted(frontier), dtype=np.int64)
        for i in range(reader.num_record_batches):
            batch = reader.get_batch(i)
            pre = batch.column("body_pre").to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
            post = batch.column("body_post").to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
            hits = post[np.isin(pre, keep_arr)]
            if hits.size:
                nxt.update(int(x) for x in np.unique(hits).tolist())
            if n_cap is not None and len(keep) + len(nxt) >= n_cap:
                capped = True
                break
        if capped:
            room = n_cap - len(keep)
            extra = [x for x in sorted(nxt) if x not in keep][: max(0, room)]
            keep.update(extra)
            hop_sizes.append(len(keep))
            keep_by_hop.append(set(keep))
            break
        frontier = nxt - keep
        keep.update(nxt)
        hop_sizes.append(len(keep))
        keep_by_hop.append(set(keep))
        if not frontier:
            break
        reader, _root = _edges_reader()
    return {
        "n_neurons": len(keep),
        "hops_requested": hops,
        "hop_sizes": hop_sizes,
        "keep_by_hop": keep_by_hop,
        "capped": capped,
        "n_cap": n_cap,
        "keep": keep,
    }


def count_internal_edges(keep: set[int]) -> tuple[int, float, float]:
    """n_edges, sum |weight|, max incoming |weight| among keep."""
    reader, _root = _edges_reader()
    keep_arr = np.array(sorted(keep), dtype=np.int64)
    n_edges = 0
    sum_abs = 0.0
    incoming: dict[int, float] = {}
    for i in range(reader.num_record_batches):
        batch = reader.get_batch(i)
        pre = batch.column("body_pre").to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
        post = batch.column("body_post").to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
        w = batch.column("weight").to_numpy(zero_copy_only=False)
        mask = np.isin(pre, keep_arr) & np.isin(post, keep_arr)
        n_edges += int(mask.sum())
        ww = np.abs(w[mask].astype(np.float64, copy=False))
        sum_abs += float(ww.sum()) if ww.size else 0.0
        if ww.size:
            posts = post[mask]
            uniq, inv = np.unique(posts, return_inverse=True)
            acc = np.zeros(uniq.size, dtype=np.float64)
            np.add.at(acc, inv, ww)
            for body, val in zip(uniq.tolist(), acc.tolist()):
                incoming[int(body)] = incoming.get(int(body), 0.0) + float(val)
    max_in = max(incoming.values()) if incoming else 0.0
    return n_edges, sum_abs, float(max_in)


def load_outgoing_graph(seed_ids: list[int], *, hops: int, n_cap: int) -> tuple[Graph, dict]:
    """Capped outgoing neighborhood as a Graph. Never the default circuit graph."""
    import pandas as pd

    from fly_chess.fetch import malecns_dir

    stats = outgoing_expand(seed_ids, hops=hops, n_cap=n_cap)
    keep = stats["keep"]
    keep_arr = np.array(sorted(keep), dtype=np.int64)
    reader, root = _edges_reader()
    edges: list[tuple[int, int, float]] = []
    for i in range(reader.num_record_batches):
        batch = reader.get_batch(i)
        pre = batch.column("body_pre").to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
        post = batch.column("body_post").to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
        w = batch.column("weight").to_numpy(zero_copy_only=False)
        mask = np.isin(pre, keep_arr) & np.isin(post, keep_arr)
        for a, bpost, wt in zip(pre[mask].tolist(), post[mask].tolist(), w[mask].tolist()):
            edges.append((int(a), int(bpost), float(wt)))
    nt = pd.read_feather(root / "neurotransmitters.feather")
    _, meta = role_body_ids(("loom_vpn", "gf_escape", "sugar_grn", "feed_mn"))
    # meta only has role cells; fill the rest from annotations
    ann = pd.read_feather(root / "annotations.feather")
    for typ, bid, status, sc, side in zip(
        ann["type"].tolist(),
        ann["bodyId"].tolist(),
        ann["status"].tolist(),
        ann["superclass"].tolist(),
        (ann["somaSide"] if "somaSide" in ann.columns else ann["type"]).tolist(),
    ):
        if int(bid) not in keep:
            continue
        if status == "Glia" or sc is None or str(sc).strip() in ("", "nan"):
            continue
        meta[int(bid)] = {
            "bodyId": int(bid),
            "type": "" if typ is None else str(typ),
            "side": "" if side is None else str(side),
            "superclass": sc,
            "status": status,
        }
    nt_map: dict[int, object] = {}
    if nt is not None and len(nt):
        bcol = "body" if "body" in nt.columns else "bodyId"
        ncol = "consensus_nt" if "consensus_nt" in nt.columns else "neurotransmitter"
        for body, pred in zip(nt[bcol].tolist(), nt[ncol].tolist()):
            nt_map[int(body)] = pred
    bodies = [meta[i] for i in sorted(keep) if i in meta]
    graph = graph_from_records(bodies, edges, nt_map)
    graph.source = f"malecns_v1_outgoing hops={hops} n_cap={n_cap} n={graph.n}"
    stats["n_edges"] = int(graph.pre.size)
    stats["graph_n"] = graph.n
    return graph, stats
