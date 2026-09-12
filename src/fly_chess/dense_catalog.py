# Copyright (c) 2026 Martial Systems LLC
"""Dense game-position catalog. Hold out by game, not by row. Not the hanging catalog."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

import chess
import numpy as np

from fly_chess.hand_eval import hand_eval, phase_name
from fly_chess.mask import legal_moves
from fly_chess.paths import CONFIG

POLICIES = ("random", "capture", "material")


@dataclass(frozen=True)
class PositionRow:
    fen: str
    game_id: int
    ply: int
    phase: str
    y_white: float
    policy: str


def load_value_cfg() -> dict:
    return json.loads((CONFIG / "value.json").read_text(encoding="utf-8"))


def _material_move(board: chess.Board, rng: np.random.Generator) -> chess.Move:
    from fly_chess.child_value import pick_child

    legal = legal_moves(board)
    if rng.random() < 0.2:
        return legal[int(rng.integers(0, len(legal)))]
    return pick_child(board, hand_eval)


def _policy_move(board: chess.Board, rng: np.random.Generator, kind: str) -> chess.Move:
    legal = legal_moves(board)
    if kind == "capture":
        caps = [m for m in legal if board.is_capture(m)]
        pool = caps or legal
        return pool[int(rng.integers(0, len(pool)))]
    if kind == "material":
        return _material_move(board, rng)
    return legal[int(rng.integers(0, len(legal)))]


def _play_game(game_id: int, *, max_ply: int, rng: np.random.Generator) -> list[tuple[chess.Board, int, str]]:
    kind = POLICIES[game_id % len(POLICIES)]
    board = chess.Board()
    frames: list[tuple[chess.Board, int, str]] = []
    for ply in range(max_ply):
        if board.is_game_over() or not any(board.legal_moves):
            break
        frames.append((board.copy(stack=False), ply, kind))
        board.push(_policy_move(board, rng, kind))
    return frames


def _sample_frames(
    frames: list[tuple[chess.Board, int, str]],
    *,
    k: int,
    rng: np.random.Generator,
) -> list[tuple[chess.Board, int, str]]:
    if len(frames) <= k:
        return frames
    idx = np.sort(rng.choice(len(frames), size=k, replace=False))
    return [frames[int(i)] for i in idx]


def build_catalog(
    *,
    n_games: int,
    positions_per_game: int,
    max_ply: int,
    seed: int,
    holdout_frac: float,
) -> dict[str, list[PositionRow]]:
    rng = np.random.default_rng(seed)
    rows: list[PositionRow] = []
    for gid in range(n_games):
        frames = _play_game(gid, max_ply=max_ply, rng=rng)
        for board, ply, kind in _sample_frames(frames, k=positions_per_game, rng=rng):
            rows.append(
                PositionRow(
                    fen=board.fen(),
                    game_id=gid,
                    ply=ply,
                    phase=phase_name(board),
                    y_white=hand_eval(board),
                    policy=kind,
                )
            )
    game_ids = list(range(n_games))
    rng2 = np.random.default_rng(seed + 1)
    rng2.shuffle(game_ids)
    n_hold = max(1, int(round(n_games * holdout_frac)))
    eval_games = set(game_ids[:n_hold])
    train = [r for r in rows if r.game_id not in eval_games]
    eval_rows = [r for r in rows if r.game_id in eval_games]
    if not train or not eval_rows:
        raise RuntimeError("catalog split emptied an arm")
    train_ids = {r.game_id for r in train}
    eval_ids = {r.game_id for r in eval_rows}
    if train_ids & eval_ids:
        raise RuntimeError("game_id leaked across value split")
    return {"train": train, "eval": eval_rows}


def catalog_payload(split: dict[str, list[PositionRow]]) -> dict:
    def arm(rows: list[PositionRow]) -> dict:
        phases = {name: 0 for name in ("opening", "middlegame", "simple")}
        for r in rows:
            phases[r.phase] = phases.get(r.phase, 0) + 1
        return {
            "n": len(rows),
            "n_games": len({r.game_id for r in rows}),
            "phases": phases,
            "policies": sorted({r.policy for r in rows}),
            "rows": [asdict(r) for r in rows],
        }

    return {
        "source": "selfplay_games",
        "holdout": "game_id",
        "not_hanging_catalog": True,
        "train": arm(split["train"]),
        "eval": arm(split["eval"]),
    }
