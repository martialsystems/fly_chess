# Copyright (c) 2026 Martial Systems LLC
"""Load a graph. Default is the fixture. Full MaleCNS is a local fetch."""

from __future__ import annotations

import json
from pathlib import Path

from fly_chess.fetch import fetch_malecns
from fly_chess.fixture import build_fixture
from fly_chess.graph import Graph
from fly_chess.paths import FIXTURE, PROVENANCE


def write_fixture(path: Path | None = None) -> Graph:
    graph = build_fixture()
    dest = path or FIXTURE
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(graph.to_dict()) + "\n", encoding="utf-8")
    return graph


def load_graph(path: Path | None = None, *, source: str = "fixture") -> Graph:
    if source == "malecns":
        from fly_chess.import_malecns import load_malecns_graph

        return load_malecns_graph()
    if source == "fixture" and path is None:
        if FIXTURE.is_file():
            raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
            return Graph.from_dict(raw)
        return write_fixture()
    if path is None:
        raise FileNotFoundError("no graph path; use source=fixture")
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return Graph.from_dict(raw)


def malecns_lock_path() -> Path:
    return PROVENANCE / "malecns_v1" / "source.lock.json"


__all__ = ["write_fixture", "load_graph", "fetch_malecns", "malecns_lock_path"]
