# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

from fly_chess.match import play_planes_gate1, play_planes_gate2
from fly_chess.puzzles import labeled_positions


def test_puzzles_are_legal() -> None:
    labeled_positions()


def test_gate1_meets_accuracy() -> None:
    report = play_planes_gate1(seed=0)
    assert report["passed"]
    assert report["accuracy"] >= 0.5


def test_gate2_logs_score_and_no_illegal() -> None:
    report = play_planes_gate2(n=4, seed=0)
    assert report["illegal"] == 0
    assert 0.0 <= report["score"] <= 1.0
