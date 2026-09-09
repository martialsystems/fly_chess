# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import numpy as np

from fly_chess.fixture import build_fixture
from fly_chess.shuffle import shuffle_graph


def test_shuffle_preserves_degree_and_is_seeded() -> None:
    g = build_fixture()
    a = shuffle_graph(g, seed=3)
    b = shuffle_graph(g, seed=3)
    c = shuffle_graph(g, seed=4)
    assert np.array_equal(a.post, b.post)
    assert not np.array_equal(a.post, c.post)
    assert np.array_equal(a.pre, g.pre)
    in_a = np.bincount(a.post, minlength=g.n)
    in_g = np.bincount(g.post, minlength=g.n)
    assert np.array_equal(np.sort(in_a), np.sort(in_g))
    out_a = np.bincount(a.pre, minlength=g.n)
    out_g = np.bincount(g.pre, minlength=g.n)
    assert np.array_equal(out_a, out_g)
    pre_sign = np.array([g.neurons[int(i)].sign for i in g.pre])
    for sign in (1, -1):
        mask = pre_sign == sign
        assert np.array_equal(np.sort(a.post[mask]), np.sort(g.post[mask]))
