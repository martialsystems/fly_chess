# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

from fly_chess.schema import stamp_score


def test_stamp_score_keeps_four_decimals() -> None:
    assert stamp_score(0.4875) == "0.4875"
    assert stamp_score(0.5) == "0.5"
