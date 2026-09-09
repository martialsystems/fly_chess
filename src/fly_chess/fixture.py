# Copyright (c) 2026 Martial Systems LLC
"""Deterministic few-hundred-neuron graph covering every required role."""

from __future__ import annotations

from fly_chess.graph import Graph, Neuron


def build_fixture(*, seed: int = 0) -> Graph:
    """Identity paths: sugar GRNs drive MN9; LPLC2 drives DNp01.

    Spatial chess identity lives on APP_LOCUS / AV_LOCUS / PLANE_SQ cells, not
    on labellar GRN geometry. Each appetitive locus synapses onto the sugar
    class as a copy; global sugar current still means "there is food."
    """
    neurons: list[Neuron] = []
    pre: list[int] = []
    post: list[int] = []
    weight: list[float] = []

    def add(type_: str, *, side: str = "", sign: int = 1, square: int | None = None) -> int:
        i = len(neurons)
        neurons.append(Neuron(id=i, type=type_, side=side, sign=sign, square=square))
        return i

    sugar = [
        add("LB3b", side="L"),
        add("LB3c", side="R"),
        add("PhG1a"),
        add("PhG1b"),
        add("PhG1c"),
        add("LgLG3"),
        add("LgLG4"),
    ]
    aversive = [add("AV_GRN"), add("Gr66a")]
    loom = [add("LPLC2", side="L", square=i) for i in range(8)]
    gf = [add("DNp01")]
    mn9 = [add("MN9")]
    mn_opt = [add("MN8"), add("MN6")]
    walk = [add("DNp09"), add("oDN1"), add("BDN2")]
    mdn = [add("MDN")]
    steer_l = [add("DNa02", side="L"), add("DNg13", side="L")]
    steer_r = [add("DNa02", side="R"), add("DNg13", side="R")]
    halt = [add("BB"), add("FG")]
    halt_groom = [add("BRK")]
    arousal = [add("PAM"), add("PPL101")]
    hidden = [add("HIDDEN", square=i) for i in range(64)]

    app_loci = [add("APP_LOCUS", square=sq) for sq in range(64)]
    av_loci = [add("AV_LOCUS", square=sq) for sq in range(64)]
    plane_sq = [add("PLANE_SQ", square=sq) for sq in range(64)]

    def edge(a: int, b: int, w: float) -> None:
        pre.append(a)
        post.append(b)
        weight.append(w)

    for s in sugar:
        for m in mn9 + mn_opt:
            edge(s, m, 3.2 if m in mn9 else 1.4)
    for loc in app_loci:
        for s in sugar:
            edge(loc, s, 1.8)
        for m in mn9:
            edge(loc, m, 0.6)
    for v in loom:
        for g in gf:
            edge(v, g, 3.5)
    for loc in av_loci:
        for v in loom:
            edge(loc, v, 1.2)
        for g in gf:
            edge(loc, g, 0.7)
        for a in aversive:
            edge(loc, a, 1.0)
    for a in aversive:
        for m in mn9:
            edge(a, m, -1.5)
    for loc, h in zip(plane_sq, hidden):
        edge(loc, h, 4.0)
    for w_id in walk:
        for s in sugar[:2]:
            edge(s, w_id, 0.8)
    for s in steer_l:
        edge(app_loci[0], s, 0.5)
    for s in steer_r:
        edge(app_loci[7], s, 0.5)
    edge(aversive[0], mdn[0], 1.2)
    for h_id in halt:
        edge(aversive[0], h_id, 0.8)
    edge(aversive[0], halt_groom[0], 0.4)
    for a in arousal:
        edge(sugar[0], a, 0.5)

    # touch seed so the builder stays deterministic if we add RNG later
    _ = seed
    return Graph(
        neurons=neurons,
        pre=pre,
        post=post,
        weight=weight,
        source="fixture",
    )
