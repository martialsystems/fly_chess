# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import pytest

from fly_chess.aliases import required_role_names
from fly_chess.fixture import build_fixture
from fly_chess.graph import Graph, Neuron
from fly_chess.resolve import ResolveError, resolve_graph


def test_fixture_resolves_all_required_roles() -> None:
    graph = build_fixture()
    resolved = resolve_graph(graph)
    for role in required_role_names():
        assert resolved.roles[role], role
    assert resolved.roles["feed_mn"]
    assert "feed_partners_optional" in resolved.missing_optional


def test_mn9_missing_fails_closed() -> None:
    graph = build_fixture()
    neurons = [n for n in graph.neurons if n.type != "MN9"]
    remap = {old.id: i for i, old in enumerate(neurons)}
    new_neurons = [
        Neuron(id=i, type=n.type, side=n.side, sign=n.sign, square=n.square)
        for i, n in enumerate(neurons)
    ]
    keep = [
        (remap[int(a)], remap[int(b)], float(w))
        for a, b, w in zip(graph.pre, graph.post, graph.weight)
        if int(a) in remap and int(b) in remap
    ]
    g2 = Graph(
        neurons=new_neurons,
        pre=[k[0] for k in keep],
        post=[k[1] for k in keep],
        weight=[k[2] for k in keep],
        source="no-mn9",
    )
    with pytest.raises(ResolveError):
        resolve_graph(g2)
