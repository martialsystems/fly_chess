# Copyright (c) 2026 Martial Systems LLC
"""Bounded 2-hop LPLC2 probe. Not the default circuit graph. Not a player."""

from __future__ import annotations

import json

import numpy as np

from fly_chess.fetch import malecns_present
from fly_chess.lif import HOP_BUDGET_NOTE, HZ_NOTE, LifConfig, LifNet
from fly_chess.paths import LOGS

N_CAP = 2000
HOPS = 2
SATURATE_FRAC_ABORT = 0.25


def run_hop_probe(*, hops: int = HOPS, n_cap: int = N_CAP) -> dict:
    if not malecns_present():
        raise FileNotFoundError("MaleCNS files missing; run python -m fly_chess fetch")
    from fly_chess.aliases import load_alias_table, role_specs
    from fly_chess.import_malecns import load_outgoing_graph, role_body_ids
    from fly_chess.resolve import _match

    seeds, _meta = role_body_ids(("loom_vpn",))
    graph, stats = load_outgoing_graph(seeds["loom_vpn"], hops=hops, n_cap=n_cap)
    cfg = LifConfig.for_source("malecns")
    net = LifNet(graph, cfg)
    specs = {s.name: s for s in role_specs(load_alias_table())}
    loom = [
        n.id
        for n in graph.neurons
        if _match(n.type, specs["loom_vpn"])
    ]
    i_ext = np.zeros(graph.n, dtype=np.float64)
    pulse = 26.0
    for i in loom:
        i_ext[i] = pulse
    net.reset()
    hz = net.run_ply(i_ext)
    ceiling = cfg.saturate_hz
    saturate_frac = float(np.mean(hz >= ceiling)) if hz.size else 0.0
    max_hz = float(np.max(hz)) if hz.size else 0.0
    aborted = bool(saturate_frac >= SATURATE_FRAC_ABORT)
    return {
        "source": "malecns",
        "probe": "outgoing_lplc2",
        "hops": hops,
        "n_cap": n_cap,
        "n_neurons": graph.n,
        "n_edges": int(graph.pre.size),
        "capped": bool(stats["capped"]),
        "hop_sizes": stats["hop_sizes"],
        "n_loom_in_graph": len(loom),
        "pulse": pulse,
        "saturate_hz": ceiling,
        "saturate_frac": saturate_frac,
        "max_hz": max_hz,
        "aborted": aborted,
        "default_circuit_graph": "475_identity_slice",
        "used_as_circuit_graph": False,
        "games": 0,
        "elo": None,
        "gate2_quoted": False,
        "hz_note": HZ_NOTE,
        "kernel": cfg.payload(),
        "note": (
            "Abort means a high fraction of cells hit the Hz cap. "
            "This graph is not the circuit graph and not a player. "
            + HOP_BUDGET_NOTE
        ),
        "readout_notes": [HOP_BUDGET_NOTE],
    }


def write_hop_probe() -> dict:
    payload = run_hop_probe()
    LOGS.mkdir(parents=True, exist_ok=True)
    dest = LOGS / "malecns_hop_probe.json"
    dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload
