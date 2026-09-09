# Copyright (c) 2026 Martial Systems LLC
"""Hop budget from LPLC2 and MN9. Counts only. Default circuit graph stays 475."""

from __future__ import annotations

import json

import numpy as np

from fly_chess.fetch import malecns_present
from fly_chess.lif import HZ_NOTE, LifConfig
from fly_chess.paths import LOGS

N_CAP = 8000
EDGE_CENSUS_CAP = 4000


def run_neighborhood(*, hops: int = 3, n_cap: int = N_CAP) -> dict:
    if not malecns_present():
        raise FileNotFoundError("MaleCNS files missing; run python -m fly_chess fetch")
    from fly_chess.import_malecns import _edges_reader, count_internal_edges, role_body_ids

    seeds, _meta = role_body_ids(("loom_vpn", "feed_mn"))
    cfg = LifConfig.for_mode("fixture_voltage_jump")
    jump_thresh = cfg.v_thresh_mV - cfg.v_rest_mV
    names = ("LPLC2", "MN9")
    keep = {
        "LPLC2": {int(x) for x in seeds["loom_vpn"]},
        "MN9": {int(x) for x in seeds["feed_mn"]},
    }
    frontier = {name: set(keep[name]) for name in names}
    keep_by_hop = {name: [set(keep[name])] for name in names}
    capped = {name: False for name in names}
    for _hop in range(hops):
        if all(capped[name] or not frontier[name] for name in names):
            break
        nxt = {name: set() for name in names}
        reader, _root = _edges_reader()
        arrs = {
            name: np.array(sorted(frontier[name]), dtype=np.int64)
            for name in names
            if frontier[name] and not capped[name]
        }
        for i in range(reader.num_record_batches):
            batch = reader.get_batch(i)
            pre = batch.column("body_pre").to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
            post = batch.column("body_post").to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
            for name, arr in arrs.items():
                hits = post[np.isin(pre, arr)]
                if hits.size:
                    nxt[name].update(int(x) for x in np.unique(hits).tolist())
                if len(keep[name]) + len(nxt[name] - keep[name]) >= n_cap:
                    capped[name] = True
        for name in names:
            extra = nxt[name] - keep[name]
            if capped[name]:
                room = max(0, n_cap - len(keep[name]))
                extra = set(sorted(extra)[:room])
            keep[name].update(extra)
            keep_by_hop[name].append(set(keep[name]))
            frontier[name] = extra
    for name in names:
        while len(keep_by_hop[name]) <= hops:
            keep_by_hop[name].append(set(keep[name]))
            capped[name] = True
    arms = []
    for name in names:
        for h in range(1, hops + 1):
            if h >= len(keep_by_hop[name]):
                break
            cells = keep_by_hop[name][h]
            n_cells = len(cells)
            hit_cap = bool(capped[name] and n_cells >= n_cap)
            if n_cells <= EDGE_CENSUS_CAP:
                n_edges, sum_abs, max_in = count_internal_edges(cells)
                seize = bool(max_in > jump_thresh)
                census = "full"
            else:
                n_edges, sum_abs, max_in = None, None, None
                seize = True
                census = "skipped_gt_4000"
            arms.append(
                {
                    "seed": name,
                    "hops": h,
                    "n_neurons": n_cells,
                    "n_cap": n_cap,
                    "capped": hit_cap,
                    "n_edges": n_edges,
                    "sum_abs_weight": sum_abs,
                    "max_incoming_abs_weight": max_in,
                    "would_seize_under_old_jump": seize,
                    "edge_census": census,
                    "default_circuit_graph": False,
                }
            )
    return {
        "source": "malecns",
        "hops": hops,
        "n_cap": n_cap,
        "jump_thresh_mV": jump_thresh,
        "default_circuit_graph": "475_identity_slice",
        "arms": arms,
        "games": 0,
        "elo": None,
        "gate2_quoted": False,
        "hz_note": HZ_NOTE,
        "note": (
            "Outgoing BFS from LPLC2 and MN9. n_cap stops the count; "
            "hop 2 from LPLC2 is already most of the map. No play."
        ),
    }


def write_neighborhood() -> dict:
    payload = run_neighborhood()
    LOGS.mkdir(parents=True, exist_ok=True)
    dest = LOGS / "malecns_neighborhood.json"
    dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload
