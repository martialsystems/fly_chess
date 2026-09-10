# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import json

from fly_chess.paths import ETHOLOGY_MAP, PLANES_MAP
from fly_chess.session import open_session


def test_ethology_and_planes_maps_dump() -> None:
    open_session()
    eth = json.loads(ETHOLOGY_MAP.read_text(encoding="utf-8"))
    planes = json.loads(PLANES_MAP.read_text(encoding="utf-8"))
    assert eth["spatial_identity"] == "synthetic_loci"
    assert eth["sugar_geometry"] == "global_gain_only"
    assert len(eth["appetitive_loci"]) == 64
    assert len(eth["aversive_loci"]) == 64
    assert planes["photoreceptors"] == "off"
    assert len(planes["pools"]) == 12
    assert all(p["n"] == 64 for p in planes["pools"])
