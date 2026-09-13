# Copyright (c) 2026 Martial Systems LLC
"""2-ply / 3-ply search over locked mix-0 eval at inference. Not a new head."""

from __future__ import annotations

import json

from fly_chess.dense_catalog import load_value_cfg
from fly_chess.lif import HZ_NOTE
from fly_chess.paths import LOGS
from fly_chess.play_match import play_policies
from fly_chess.search import pick_search

TABLE_PATH = LOGS / "search_lock.json"
POISONED = "4k3/4p3/8/8/8/8/4Q3/4K3 w - - 0 1"


def _pick(plies: int):
    return lambda board: pick_search(board, plies=plies)


def run_search_table(*, tiny: bool = False, n: int | None = None) -> dict:
    cfg = load_value_cfg()
    n_games = 2 if tiny else int(n if n is not None else (cfg.get("search") or {}).get("games_n", 200))
    n_three = 0 if tiny else int((cfg.get("search") or {}).get("games_n_3ply", 40))
    max_ply = 16 if tiny else int((cfg.get("search") or {}).get("max_ply", 400))
    seed = int((cfg.get("search") or {}).get("seed", 3))
    one = _pick(1)
    two = _pick(2)
    three = _pick(3)
    from fly_chess.search import pick_search as _ps
    import chess

    board = chess.Board(POISONED)
    ply1 = _ps(board, plies=1).uci()
    ply2 = _ps(board, plies=2).uci()
    canary = {
        "fen": POISONED,
        "ply1": ply1,
        "ply2": ply2,
        "ply1_takes_e7": ply1 == "e2e7",
        "ply2_avoids_e7": ply2 != "e2e7",
        "search_differs_from_1ply": ply1 != ply2,
    }
    two_vs_one = play_policies(
        two, one, n=n_games, seed=seed, us_name="2ply", them_name="1ply_A", max_ply=max_ply
    )
    three_vs_one = (
        {
            "skipped": True,
            "n_games": 0,
            "n_same_policy": 0,
            "n_decisive": 0,
            "same_policy_is_not_a_match": True,
            "us": "3ply",
            "them": "1ply_A",
            "elo": None,
        }
        if tiny
        else play_policies(
            three,
            one,
            n=n_three,
            seed=seed + 1,
            us_name="3ply",
            them_name="1ply_A",
            max_ply=max_ply,
        )
    )
    one_vs_one = play_policies(
        one, one, n=n_games, seed=seed + 2, us_name="1ply_A", them_name="1ply_A", max_ply=max_ply
    )
    payload = {
        "experiment": "mix0_search_at_inference",
        "eval": "locked_hand_eval_mix0",
        "new_head": False,
        "distill_is_A": True,
        "canary": canary,
        "two_vs_one": two_vs_one,
        "three_vs_one": three_vs_one,
        "one_vs_one_control": one_vs_one,
        "note": (
            "Search is a loop at test time over the mix-0 eval. "
            "same_policy games are not a 0.50 match result. "
            "Do not lock distill equal to 2-ply."
        ),
        "elo": None,
        "gate2_quoted": False,
        "wiring_helped": False,
        "unfreeze_allowed": False,
        "hz_note": HZ_NOTE,
        "tiny": tiny,
        "claim": (
            "2-ply and 3-ply search over the locked mix-0 eval at inference. "
            "Graph frozen. Distill is A."
        ),
    }
    if not tiny:
        LOGS.mkdir(parents=True, exist_ok=True)
        TABLE_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def write_search_table(*, tiny: bool = False, n: int | None = None) -> dict:
    return run_search_table(tiny=tiny, n=n)
