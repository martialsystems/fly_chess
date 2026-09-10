# Copyright (c) 2026 Martial Systems LLC
"""475-cell Experiment 1 circuit check: paint sugar/loom gains, no games."""

from __future__ import annotations

import json

from fly_chess.fetch import malecns_present
from fly_chess.lif import GAIN_PICK_NOTE, HZ_NOTE, MN9_MEAN_NOTE, near_rest
from fly_chess.paint import circuit_gains, load_paint_cfg
from fly_chess.paths import LOGS
from fly_chess.rates import mean_hz
from fly_chess.session import open_session, ply_rates, session_from_graph


def _rates(session, channel: str) -> dict[str, float]:
    cfg = load_paint_cfg()
    i_ext = circuit_gains(session.graph, session.resolved, channel, cfg)
    hz = ply_rates(session, i_ext)
    return {
        "feed_mn": mean_hz(hz, session.resolved.roles["feed_mn"]),
        "gf_escape": mean_hz(hz, session.resolved.roles["gf_escape"]),
        "sugar_grn": mean_hz(hz, session.resolved.roles["sugar_grn"]),
        "loom_vpn": mean_hz(hz, session.resolved.roles["loom_vpn"]),
    }


def run_circuit(*, source: str, shuffle_seed: int = 1) -> dict:
    if source == "malecns" and not malecns_present():
        raise FileNotFoundError("MaleCNS files missing; run python -m fly_chess fetch")
    require = "identity" if source == "malecns" else "all"
    if source == "malecns":
        from fly_chess.import_malecns import load_identity_graph

        graph = load_identity_graph()
        real = session_from_graph(
            graph, shuffled=False, require=require, source="malecns"
        )
        shuffled = session_from_graph(
            graph, shuffled=True, seed=shuffle_seed, require=require, source="malecns"
        )
    else:
        real = open_session(source=source, shuffled=False, require=require)
        shuffled = open_session(
            source=source, shuffled=True, seed=shuffle_seed, require=require
        )
    cfg = load_paint_cfg()
    out = {
        "source": source,
        "n_neurons": real.graph.n,
        "shuffle_seed": shuffle_seed,
        "paint": {
            "sugar_global_gain": cfg["sugar_global_gain"],
            "loom_global_gain": cfg["loom_global_gain"],
            "appetitive_locus_current": cfg["appetitive_locus_current"],
            "aversive_locus_current": cfg["aversive_locus_current"],
            "loci": False,
            "games": False,
        },
        "real": {
            "rest": _rates(real, "rest"),
            "sugar": _rates(real, "sugar"),
            "loom": _rates(real, "loom"),
        },
        "shuffled": {
            "rest": _rates(shuffled, "rest"),
            "sugar": _rates(shuffled, "sugar"),
            "loom": _rates(shuffled, "loom"),
        },
        "gate2_quoted": False,
        "elo": None,
        "games": 0,
        "hz_note": HZ_NOTE,
        "readout_notes": (
            [MN9_MEAN_NOTE, GAIN_PICK_NOTE] if source == "malecns" else []
        ),
        "kernel": real.net.cfg.payload(),
    }
    rs, ss = out["real"], out["shuffled"]
    sugar_sep = rs["sugar"]["feed_mn"] > rs["rest"]["feed_mn"] and near_rest(
        rs["sugar"]["gf_escape"], rs["rest"]["gf_escape"]
    )
    loom_sep = rs["loom"]["gf_escape"] > rs["rest"]["gf_escape"] and near_rest(
        rs["loom"]["feed_mn"], rs["rest"]["feed_mn"]
    )
    out["passed"] = {
        "mn9_vs_dnp01_separate": bool(sugar_sep and loom_sep),
        "sugar_mn9_real": rs["sugar"]["feed_mn"] > rs["rest"]["feed_mn"],
        "loom_gf_real": rs["loom"]["gf_escape"] > rs["rest"]["gf_escape"],
        "shuffle_crosstalk": (
            ss["sugar"]["gf_escape"] > ss["rest"]["gf_escape"] + 1.0
            or ss["loom"]["feed_mn"] > ss["rest"]["feed_mn"] + 1.0
        ),
    }
    return out


def write_circuit(source: str = "malecns") -> dict:
    payload = run_circuit(source=source)
    LOGS.mkdir(parents=True, exist_ok=True)
    dest = LOGS / f"{source}_circuit.json"
    dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload
