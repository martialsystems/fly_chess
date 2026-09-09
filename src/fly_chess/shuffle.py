# Copyright (c) 2026 Martial Systems LLC
"""Degree- and sign-preserving rewire. Seed is logged."""

from __future__ import annotations

import numpy as np

from fly_chess.graph import Graph


def shuffle_graph(graph: Graph, *, seed: int) -> Graph:
    """Permute postsynaptic IDs within each outgoing-sign class.

    Preserves each presynaptic out-degree, the multiset of posts (hence
    in-degree), and Dale: a neuron's outgoing signs stay with that neuron.
    """
    rng = np.random.default_rng(seed)
    if graph.pre.size == 0:
        return graph
    pre_sign = np.array([graph.neurons[int(i)].sign for i in graph.pre], dtype=np.int32)
    new_post = graph.post.copy()
    for sign in (1, -1):
        mask = pre_sign == sign
        if not np.any(mask):
            continue
        posts = graph.post[mask].copy()
        rng.shuffle(posts)
        new_post[mask] = posts
    return Graph(
        neurons=list(graph.neurons),
        pre=graph.pre.copy(),
        post=new_post,
        weight=graph.weight.copy(),
        source=f"{graph.source}:shuffle:{seed}",
    )
