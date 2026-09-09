# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import json

import pytest

from fly_chess.fetch import datasets_path, load_lock, malecns_present
from fly_chess.import_malecns import graph_from_records
from fly_chess.resolve import resolve_graph
from fly_chess.shuffle import shuffle_graph


def test_glia_dropped_and_sugar_reaches_mn9() -> None:
    bodies = [
        {"bodyId": 1, "type": "LB3c", "superclass": "sensory", "status": "Traced", "side": "L"},
        {"bodyId": 2, "type": "MN9", "superclass": "motor", "status": "Traced", "side": ""},
        {"bodyId": 3, "type": "glia", "superclass": "glia", "status": "Glia", "side": ""},
        {"bodyId": 4, "type": "orphan", "superclass": "", "status": "Traced", "side": ""},
        {"bodyId": 5, "type": "LPLC2", "superclass": "visual", "status": "Traced", "side": "L"},
        {"bodyId": 6, "type": "DNp01", "superclass": "descending", "status": "Traced", "side": ""},
        {"bodyId": 7, "type": "AV_GRN", "superclass": "sensory", "status": "Traced", "side": ""},
        {"bodyId": 8, "type": "DNp09", "superclass": "descending", "status": "Traced", "side": ""},
        {"bodyId": 9, "type": "MDN", "superclass": "descending", "status": "Traced", "side": ""},
        {"bodyId": 10, "type": "DNa02", "superclass": "descending", "status": "Traced", "side": "L"},
        {"bodyId": 11, "type": "DNa02", "superclass": "descending", "status": "Traced", "side": "R"},
        {"bodyId": 12, "type": "BB", "superclass": "descending", "status": "Traced", "side": ""},
        {"bodyId": 13, "type": "APP_LOCUS", "superclass": "sensory", "status": "Traced", "side": ""},
    ]
    edges = [(1, 2, 12.0), (5, 6, 8.0), (3, 2, 99.0)]
    graph = graph_from_records(bodies, edges, nt_map={1: "acetylcholine", 5: "acetylcholine"})
    types = {n.type for n in graph.neurons}
    assert "glia" not in types
    assert "orphan" not in types
    assert "MN9" in types and "LB3c" in types
    resolved = resolve_graph(graph)
    assert resolved.roles["feed_mn"]
    assert resolved.roles["sugar_grn"]
    assert resolved.roles["loom_vpn"]
    assert resolved.roles["gf_escape"]
    shuf = shuffle_graph(graph, seed=1)
    assert shuf.n == graph.n


def test_source_lock_matches_datasets_urls() -> None:
    registry = json.loads(datasets_path().read_text(encoding="utf-8"))
    lock = load_lock()
    files = registry["datasets"]["malecns_v1"]["files"]
    assert set(files) == set(lock)
    for name, url in files.items():
        assert lock[name]["url"] == url
        assert len(lock[name]["sha256"]) == 64
        assert int(lock[name]["bytes"]) > 0
    assert not malecns_present()


def test_malecns_identity_skips_without_download() -> None:
    from fly_chess.identity import run_identity

    with pytest.raises(FileNotFoundError):
        run_identity(source="malecns")
