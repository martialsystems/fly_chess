# Copyright (c) 2026 Martial Systems LLC
"""Sugar → MN9 and LPLC2 → DNp01 on a graph and on its degree-and-sign shuffle."""

from __future__ import annotations

import json

from fly_chess.fetch import malecns_present
from fly_chess.match import identity_stim
from fly_chess.paths import LOGS
from fly_chess.session import open_session


def run_identity(*, source: str, shuffle_seed: int = 1) -> dict:
    if source == "malecns" and not malecns_present():
        raise FileNotFoundError("MaleCNS files missing; run python -m fly_chess fetch")
    real = open_session(source=source, shuffled=False)
    shuffled = open_session(source=source, shuffled=True, seed=shuffle_seed)
    out = {
        "source": source,
        "n_neurons_real": real.graph.n,
        "n_neurons_shuffled": shuffled.graph.n,
        "shuffle_seed": shuffle_seed,
        "real": {
            "sugar_rest": identity_stim(real, "sugar_grn", current=0.0),
            "sugar_on": identity_stim(real, "sugar_grn", current=18.0),
            "loom_rest": identity_stim(real, "loom_vpn", current=0.0),
            "loom_on": identity_stim(real, "loom_vpn", current=18.0),
        },
        "shuffled": {
            "sugar_rest": identity_stim(shuffled, "sugar_grn", current=0.0),
            "sugar_on": identity_stim(shuffled, "sugar_grn", current=18.0),
            "loom_rest": identity_stim(shuffled, "loom_vpn", current=0.0),
            "loom_on": identity_stim(shuffled, "loom_vpn", current=18.0),
        },
        "gate2_quoted": False,
    }
    rs, ss = out["real"], out["shuffled"]
    out["passed"] = {
        "sugar_mn9_real": ss_up(rs["sugar_on"]["feed_mn"], rs["sugar_rest"]["feed_mn"]),
        "loom_gf_real": ss_up(rs["loom_on"]["gf_escape"], rs["loom_rest"]["gf_escape"]),
        "sugar_mn9_shuffled": ss_up(
            ss["sugar_on"]["feed_mn"], ss["sugar_rest"]["feed_mn"]
        ),
        "loom_gf_shuffled": ss_up(
            ss["loom_on"]["gf_escape"], ss["loom_rest"]["gf_escape"]
        ),
    }
    out["passed"]["identity"] = bool(
        out["passed"]["sugar_mn9_real"] and out["passed"]["loom_gf_real"]
    )
    return out


def ss_up(on: float, rest: float) -> bool:
    return float(on) > float(rest) and float(on) > 1.0


def write_identity(source: str = "malecns") -> dict:
    payload = run_identity(source=source)
    LOGS.mkdir(parents=True, exist_ok=True)
    dest = LOGS / f"{source}_identity.json"
    dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload
