# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fly_chess.connectome import load_graph, write_fixture
from fly_chess.graph import Graph
from fly_chess.lif import LifConfig, LifNet
from fly_chess.paint import dump_ethology_map
from fly_chess.planes import dump_planes_map
from fly_chess.resolve import Resolved, ResolveError, resolve_graph, write_resolved
from fly_chess.shuffle import shuffle_graph


@dataclass
class Session:
    graph: Graph
    resolved: Resolved
    net: LifNet
    shuffled: bool
    shuffle_seed: int | None


def open_session(
    *,
    shuffled: bool = False,
    seed: int = 0,
    source: str = "fixture",
    require: str = "all",
) -> Session:
    if source == "fixture":
        write_fixture()
        graph = load_graph(source="fixture")
    elif source == "malecns":
        from fly_chess.import_malecns import load_identity_graph

        graph = load_identity_graph()
    else:
        graph = load_graph(source=source)
    if shuffled:
        graph = shuffle_graph(graph, seed=seed)
    resolved = resolve_graph(graph, require=require)
    write_resolved(resolved)
    if require == "all":
        dump_ethology_map(graph, resolved)
        dump_planes_map(graph, resolved)
    net = LifNet(graph, LifConfig.load())
    return Session(
        graph=graph,
        resolved=resolved,
        net=net,
        shuffled=shuffled,
        shuffle_seed=seed if shuffled else None,
    )


def session_from_graph(
    graph: Graph,
    *,
    shuffled: bool = False,
    seed: int = 0,
    require: str = "all",
) -> Session:
    if shuffled:
        graph = shuffle_graph(graph, seed=seed)
    resolved = resolve_graph(graph, require=require)
    net = LifNet(graph, LifConfig.load())
    return Session(
        graph=graph,
        resolved=resolved,
        net=net,
        shuffled=shuffled,
        shuffle_seed=seed if shuffled else None,
    )


def require_ethology(session: Session) -> None:
    if not session.resolved.roles.get("feed_mn"):
        raise ResolveError("MN9 missing: Experiment 1 does not start")


def ply_rates(session: Session, i_ext: np.ndarray) -> np.ndarray:
    session.net.reset()
    return session.net.run_ply(i_ext)
