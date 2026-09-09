# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

from fly_chess.match import identity_stim
from fly_chess.session import open_session


def test_sugar_stim_raises_mn9() -> None:
    session = open_session()
    rest = identity_stim(session, "sugar_grn", current=0.0)
    on = identity_stim(session, "sugar_grn", current=18.0)
    assert on["feed_mn"] > rest["feed_mn"]
    assert on["feed_mn"] > 1.0


def test_loom_stim_raises_dnp01() -> None:
    session = open_session()
    rest = identity_stim(session, "loom_vpn", current=0.0)
    on = identity_stim(session, "loom_vpn", current=18.0)
    assert on["gf_escape"] > rest["gf_escape"]
    assert on["gf_escape"] > 1.0
