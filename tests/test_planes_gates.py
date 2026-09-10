# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

from fly_chess.match import play_planes_gate0, play_planes_gate2
from fly_chess.puzzles import labeled_positions, load_split, split_positions


def test_puzzles_are_legal() -> None:
    labeled_positions()


def test_train_eval_split_has_no_fen_overlap() -> None:
    split = load_split()
    assert split["train"]
    assert split["eval"]
    assert set(split["train"]).isdisjoint(set(split["eval"]))
    split_positions(arm="train")
    split_positions(arm="eval")


def test_gate0_illegal_is_zero() -> None:
    report = play_planes_gate0(n=8, seed=0)
    assert report["illegal"] == 0


def test_gate2_logs_score_and_no_illegal() -> None:
    report = play_planes_gate2(n=2, seed=0)
    assert report["illegal"] == 0
    assert 0.0 <= report["score"] <= 1.0
