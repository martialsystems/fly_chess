# Copyright (c) 2026 Martial Systems LLC
"""Shared lock-file schema for ethology and planes JSON."""

from __future__ import annotations

TOP_KEYS = (
    "experiment",
    "claim",
    "fixture_sha256",
    "n_games",
    "game_seed",
    "shuffle_seed",
    "time_control",
    "flee_metric",
    "real",
    "shuffled",
    "load_bearing",
    "graph",
    "note",
    "gate2_passed",
)

ARM_KEYS = (
    "n_games",
    "score",
    "score_lo",
    "score_hi",
    "illegal",
    "hanging_capture_rate",
    "hanging_chances",
    "check_escape_rate",
    "check_chances",
    "verbs",
    "gate0",
    "gate1",
    "gate2",
    "game_seed",
    "shuffle_seed",
)

LOAD_BEARING_KEYS = (
    "score_real_gt_shuffled",
    "hanging_capture_real_gt_shuffled",
    "hanging_capture_same_n",
    "check_escape_real_ge_shuffled",
    "check_escape_same_n",
    "gate1_accuracy_real_gt_shuffled",
    "gate2_score_real_gt_shuffled",
    "wiring_is_encoder",
)

CHECK_ESCAPE_NOTE = (
    "Check-escape 1.0 is the legal-move mask keeping king-safe moves after "
    "paint marks in-check. Real and shuffled saw different check counts, so "
    "they are not the same position set. Do not read 1.0 as graph skill."
)

HANGING_CAPTURE_NOTE = (
    "hanging_capture_real_gt_shuffled is true (0.177 vs 0.159) but the arms "
    "saw 774 vs 668 hanging chances, so it is not the same test set. Score "
    "is identical. Do not promote the hanging-capture bit. wiring_is_encoder "
    "stays false."
)

FIXTURE_NOTE = CHECK_ESCAPE_NOTE + " " + HANGING_CAPTURE_NOTE

MALECNS_LOCK_KEYS = (
    "hz_note",
    "games",
    "elo",
    "gate2_quoted",
)


def stamp_score(value: float) -> str:
    """JSON score as written, not rounded to 3 decimals."""
    return format(value, ".10g")


def empty_arm() -> dict:
    return {k: None for k in ARM_KEYS}


def fill_arm(src: dict | None) -> dict:
    row = empty_arm()
    if not src:
        return row
    for k in ARM_KEYS:
        if k in src:
            row[k] = src[k]
    return row


def empty_load_bearing() -> dict:
    return {k: None for k in LOAD_BEARING_KEYS}


def document(*, experiment: str, claim: str, fixture_sha256: str, n_games: int,
             game_seed: int, shuffle_seed: int, time_control: str,
             real: dict, shuffled: dict, load_bearing: dict,
             graph: str, note: str, gate2_passed: bool | None,
             flee_metric: str | None = "us_to_move_in_check") -> dict:
    lb = empty_load_bearing()
    lb.update({k: v for k, v in load_bearing.items() if k in LOAD_BEARING_KEYS})
    out = {
        "experiment": experiment,
        "claim": claim,
        "fixture_sha256": fixture_sha256,
        "n_games": n_games,
        "game_seed": game_seed,
        "shuffle_seed": shuffle_seed,
        "time_control": time_control,
        "flee_metric": flee_metric,
        "real": fill_arm(real),
        "shuffled": fill_arm(shuffled),
        "load_bearing": lb,
        "graph": graph,
        "note": note,
        "gate2_passed": gate2_passed,
    }
    return out
