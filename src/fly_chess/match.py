# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path

import chess
import numpy as np

from fly_chess import ALLOWED_ETHOLOGY, ALLOWED_PLANES
from fly_chess.board_feats import hanging_enemy_squares
from fly_chess.head import LinearHead
from fly_chess.mask import escapes_check, legal_moves
from fly_chess.paint import currents as paint_currents
from fly_chess.paths import CONFIG, LOGS, PROVENANCE
from fly_chess.planes import currents as plane_currents
from fly_chess.planes import readout_vector
from fly_chess.puzzles import labeled_positions
from fly_chess.session import Session, open_session, ply_rates, require_ethology
from fly_chess.verbs import choose_move


def load_gates() -> dict:
    return json.loads((CONFIG / "gates.json").read_text(encoding="utf-8"))


def refuse_online(args) -> None:
    for name in ("lichess", "chesscom", "chess_com", "online"):
        if getattr(args, name, False):
            raise SystemExit("no Lichess or chess.com client in this slice")


def random_move(board: chess.Board, rng: random.Random) -> chess.Move:
    legal = legal_moves(board)
    return rng.choice(legal)


def capture_preferring_move(board: chess.Board, rng: random.Random) -> chess.Move:
    legal = legal_moves(board)
    caps = [m for m in legal if board.is_capture(m)]
    return rng.choice(caps or legal)


@dataclass
class GameStats:
    n_games: int = 0
    score: float = 0.0
    illegal: int = 0
    ply: int = 0
    hanging_chances: int = 0
    hanging_taken: int = 0
    check_chances: int = 0
    check_escaped: int = 0
    verbs: dict[str, int] = field(default_factory=dict)


def ethology_move(session: Session, board: chess.Board) -> tuple[chess.Move, str]:
    require_ethology(session)
    i_ext = paint_currents(board, session.graph, session.resolved)
    hz = ply_rates(session, i_ext)
    return choose_move(board, session.graph, session.resolved, hz)


def planes_move(session: Session, board: chess.Board, head: LinearHead) -> chess.Move:
    i_ext = plane_currents(board, session.graph, session.resolved)
    hz = ply_rates(session, i_ext)
    feat = readout_vector(hz, session.resolved)
    return head.pick(board, feat)


def play_ethology(
    *,
    n: int,
    opponent: str,
    seed: int = 0,
    shuffled: bool = False,
    shuffle_seed: int = 1,
) -> dict:
    rng = random.Random(seed)
    session = open_session(shuffled=shuffled, seed=shuffle_seed if shuffled else 0)
    stats = GameStats()
    for g in range(n):
        board = chess.Board()
        us_white = g % 2 == 0
        result = _play_one(
            board,
            us_white=us_white,
            session=session,
            opponent=opponent,
            rng=rng,
            stats=stats,
            mode="ethology",
            head=None,
        )
        stats.n_games += 1
        stats.score += result
    return _ethology_report(
        stats,
        shuffled=shuffled,
        game_seed=seed,
        shuffle_seed=shuffle_seed if shuffled else None,
    )


def _play_one(
    board: chess.Board,
    *,
    us_white: bool,
    session: Session,
    opponent: str,
    rng: random.Random,
    stats: GameStats,
    mode: str,
    head: LinearHead | None,
    max_ply: int = 80,
) -> float:
    us = chess.WHITE if us_white else chess.BLACK
    while not board.is_game_over() and board.ply() < max_ply:
        if board.turn == us:
            if board.is_check() and any(escapes_check(board, m) for m in legal_moves(board)):
                stats.check_chances += 1
            hanging = hanging_enemy_squares(board, us)
            hanging_caps = [
                m
                for m in legal_moves(board)
                if board.is_capture(m) and m.to_square in hanging
            ]
            if hanging_caps:
                stats.hanging_chances += 1
            if mode == "ethology":
                move, verb = ethology_move(session, board)
                stats.verbs[verb] = stats.verbs.get(verb, 0) + 1
            else:
                assert head is not None
                move = planes_move(session, board, head)
                verb = "head"
            if move not in board.legal_moves:
                stats.illegal += 1
                move = random_move(board, rng)
            if hanging_caps and move in hanging_caps:
                stats.hanging_taken += 1
            if board.is_check() and escapes_check(board, move):
                stats.check_escaped += 1
            board.push(move)
            stats.ply += 1
        else:
            if opponent == "capture":
                board.push(capture_preferring_move(board, rng))
            else:
                board.push(random_move(board, rng))
            stats.ply += 1
    if board.is_checkmate():
        winner = not board.turn
        if winner == us:
            return 1.0
        return 0.0
    if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
        return 0.5
    return 0.5


def _ethology_report(
    stats: GameStats,
    *,
    shuffled: bool,
    game_seed: int,
    shuffle_seed: int | None,
) -> dict:
    score = stats.score / max(stats.n_games, 1)
    hang = stats.hanging_taken / max(stats.hanging_chances, 1)
    flee = stats.check_escaped / max(stats.check_chances, 1)
    lo, hi = mean_interval(score, stats.n_games)
    from fly_chess.schema import stamp_score

    claim = ALLOWED_ETHOLOGY.format(
        score=stamp_score(score), shuffled=str(shuffled).lower()
    )
    return {
        "experiment": "ethology",
        "claim": claim,
        "n_games": stats.n_games,
        "score": score,
        "score_lo": lo,
        "score_hi": hi,
        "illegal": stats.illegal,
        "hanging_capture_rate": hang,
        "hanging_chances": stats.hanging_chances,
        "flee_metric": "us_to_move_in_check",
        "check_escape_rate": flee,
        "check_chances": stats.check_chances,
        "verbs": stats.verbs,
        "shuffled": shuffled,
        "game_seed": game_seed,
        "shuffle_seed": shuffle_seed,
        "time_control": "1+0.1 random opponents; no Stockfish Elo",
    }


def mean_interval(score: float, n: int, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        return 0.0, 1.0
    se = (max(score, 0.0) * max(1.0 - score, 0.0) / n) ** 0.5
    return score - z * se, score + z * se


def fixture_sha256() -> str:
    lock = json.loads((PROVENANCE / "fixture.lock.json").read_text(encoding="utf-8"))
    return str(lock["sha256"])


def play_planes_gate0(*, n: int = 32, seed: int = 0) -> dict:
    session = open_session(shuffled=False, seed=seed)
    feat0 = readout_vector(np.zeros(session.graph.n), session.resolved)
    head = LinearHead.zeros(len(feat0))
    illegal = 0
    rng = random.Random(seed)
    for i in range(n):
        board = chess.Board()
        for _ in range(rng.randint(0, 6)):
            if board.is_game_over():
                break
            board.push(random_move(board, rng))
        if board.is_game_over():
            continue
        move = planes_move(session, board, head)
        if move not in board.legal_moves:
            illegal += 1
    claim = ALLOWED_PLANES.format(gate=0, shuffled="logged")
    return {
        "experiment": "planes",
        "gate": 0,
        "claim": claim,
        "n_positions": n,
        "illegal_rate": illegal / max(n, 1),
        "illegal": illegal,
    }


def train_planes_head(session: Session, *, n_train: int, seed: int = 0) -> LinearHead:
    puzzles = labeled_positions()
    feat0 = readout_vector(np.zeros(session.graph.n), session.resolved)
    head = LinearHead.zeros(len(feat0))
    epochs = max(4, n_train // max(len(puzzles), 1))
    for _ in range(epochs):
        for board, target, _ in puzzles:
            b = board.copy()
            i_ext = plane_currents(b, session.graph, session.resolved)
            hz = ply_rates(session, i_ext)
            feat = readout_vector(hz, session.resolved)
            head.train_step(feat, target, b, lr=0.08)
    return head


def play_planes_gate1(*, seed: int = 0) -> dict:
    gates = load_gates()
    session = open_session(shuffled=False, seed=seed)
    head = train_planes_head(session, n_train=int(gates["gate1"]["n_train"]), seed=seed)
    puzzles = labeled_positions()
    n_eval = min(int(gates["gate1"]["n_eval"]), len(puzzles))
    correct = 0
    for board, target, _ in puzzles[:n_eval]:
        move = planes_move(session, board.copy(), head)
        if move == target:
            correct += 1
    acc = correct / max(n_eval, 1)
    return {
        "experiment": "planes",
        "gate": 1,
        "claim": ALLOWED_PLANES.format(gate=1, shuffled="logged"),
        "accuracy": acc,
        "n_eval": n_eval,
        "correct": correct,
        "min_accuracy": gates["gate1"]["min_accuracy"],
        "passed": acc >= gates["gate1"]["min_accuracy"],
    }


def play_planes_gate2(
    *,
    n: int | None = None,
    seed: int = 0,
    shuffled: bool = False,
    shuffle_seed: int = 1,
) -> dict:
    gates = load_gates()
    n = int(n if n is not None else gates["gate2"]["n_games"])
    session = open_session(shuffled=shuffled, seed=shuffle_seed if shuffled else 0)
    head = train_planes_head(session, n_train=int(gates["gate1"]["n_train"]), seed=seed)
    rng = random.Random(seed)
    stats = GameStats()
    for g in range(n):
        board = chess.Board()
        result = _play_one(
            board,
            us_white=g % 2 == 0,
            session=session,
            opponent="random",
            rng=rng,
            stats=stats,
            mode="planes",
            head=head,
        )
        stats.n_games += 1
        stats.score += result
    score = stats.score / max(stats.n_games, 1)
    lo, hi = mean_interval(score, stats.n_games)
    passed = (not shuffled) and lo > float(gates["gate2"]["min_score"]) and stats.illegal == 0
    return {
        "experiment": "planes",
        "gate": 2,
        "claim": ALLOWED_PLANES.format(gate=2, shuffled=str(shuffled)),
        "n_games": stats.n_games,
        "score": score,
        "score_lo": lo,
        "score_hi": hi,
        "illegal": stats.illegal,
        "min_score": gates["gate2"]["min_score"],
        "passed": passed,
        "shuffled": shuffled,
        "game_seed": seed,
        "shuffle_seed": shuffle_seed if shuffled else None,
    }


def lock_ethology() -> dict:
    from fly_chess.schema import CHECK_ESCAPE_NOTE, document, stamp_score

    gates = load_gates()
    n = int(gates["ethology_n"])
    game_seed = int(gates["game_seed"])
    shuffle_seed = int(gates["shuffle_seed"])
    real = play_ethology(
        n=n, opponent="random", seed=game_seed, shuffled=False
    )
    shuffled = play_ethology(
        n=n,
        opponent="random",
        seed=game_seed,
        shuffled=True,
        shuffle_seed=shuffle_seed,
    )
    hang_real = float(real["hanging_capture_rate"])
    hang_shuf = float(shuffled["hanging_capture_rate"])
    flee_real = float(real["check_escape_rate"])
    flee_shuf = float(shuffled["check_escape_rate"])
    score_real = float(real["score"])
    score_shuf = float(shuffled["score"])
    claim = ALLOWED_ETHOLOGY.format(
        score=stamp_score(score_real),
        shuffled=stamp_score(score_shuf),
    )
    return document(
        experiment="ethology",
        claim=claim,
        fixture_sha256=fixture_sha256(),
        n_games=n,
        game_seed=game_seed,
        shuffle_seed=shuffle_seed,
        time_control=real["time_control"],
        real=real,
        shuffled=shuffled,
        load_bearing={
            "score_real_gt_shuffled": score_real > score_shuf,
            "hanging_capture_real_gt_shuffled": hang_real > hang_shuf,
            "check_escape_real_ge_shuffled": flee_real >= flee_shuf,
            "check_escape_same_n": int(real["check_chances"])
            == int(shuffled["check_chances"]),
            "gate1_accuracy_real_gt_shuffled": None,
            "gate2_score_real_gt_shuffled": None,
            "wiring_is_encoder": False,
        },
        graph="fixture, not MaleCNS v1.0",
        note=CHECK_ESCAPE_NOTE,
        gate2_passed=None,
    )


def lock_planes() -> dict:
    from fly_chess.schema import document

    gates = load_gates()
    game_seed = int(gates["game_seed"])
    shuffle_seed = int(gates["shuffle_seed"])
    n = int(gates["gate2"]["n_games"])
    g0 = play_planes_gate0(n=int(gates["gate0"]["n_positions"]), seed=game_seed)
    g1_real = play_planes_gate1(seed=game_seed)
    g2_real = play_planes_gate2(n=n, seed=game_seed, shuffled=False)
    g1_shuf = play_planes_gate1_on_shuffle(seed=game_seed, shuffle_seed=shuffle_seed)
    g2_shuf = play_planes_gate2(
        n=n, seed=game_seed, shuffled=True, shuffle_seed=shuffle_seed
    )
    claim = ALLOWED_PLANES.format(gate="0-2", shuffled="logged")
    real_arm = {**g2_real, "gate0": g0, "gate1": g1_real, "gate2": g2_real}
    shuf_arm = {**g2_shuf, "gate0": None, "gate1": g1_shuf, "gate2": g2_shuf}
    score_real = float(g2_real["score"])
    score_shuf = float(g2_shuf["score"])
    return document(
        experiment="planes",
        claim=claim,
        fixture_sha256=fixture_sha256(),
        n_games=n,
        game_seed=game_seed,
        shuffle_seed=shuffle_seed,
        time_control="1+0.1 random opponents; no Stockfish Elo",
        real=real_arm,
        shuffled=shuf_arm,
        load_bearing={
            "score_real_gt_shuffled": score_real > score_shuf,
            "hanging_capture_real_gt_shuffled": None,
            "check_escape_real_ge_shuffled": None,
            "check_escape_same_n": None,
            "gate1_accuracy_real_gt_shuffled": float(g1_real["accuracy"])
            > float(g1_shuf["accuracy"]),
            "gate2_score_real_gt_shuffled": score_real > score_shuf,
            "wiring_is_encoder": False,
        },
        graph="fixture, not MaleCNS v1.0",
        note="Wiring is not an encoder on this graph. Gate 2 real matches shuffled.",
        gate2_passed=bool(g2_real["passed"]),
    )


def play_planes_gate1_on_shuffle(*, seed: int, shuffle_seed: int) -> dict:
    gates = load_gates()
    session = open_session(shuffled=True, seed=shuffle_seed)
    head = train_planes_head(session, n_train=int(gates["gate1"]["n_train"]), seed=seed)
    puzzles = labeled_positions()
    n_eval = min(int(gates["gate1"]["n_eval"]), len(puzzles))
    correct = 0
    for board, target, _ in puzzles[:n_eval]:
        move = planes_move(session, board.copy(), head)
        if move == target:
            correct += 1
    acc = correct / max(n_eval, 1)
    return {
        "experiment": "planes",
        "gate": 1,
        "accuracy": acc,
        "n_eval": n_eval,
        "correct": correct,
        "min_accuracy": gates["gate1"]["min_accuracy"],
        "passed": acc >= gates["gate1"]["min_accuracy"],
        "shuffled": True,
        "shuffle_seed": shuffle_seed,
    }


def write_locked_gates() -> tuple[Path, Path]:
    LOGS.mkdir(parents=True, exist_ok=True)
    eth = lock_ethology()
    planes = lock_planes()
    p1 = LOGS / "ethology_gate.json"
    p2 = LOGS / "planes_gate.json"
    p1.write_text(json.dumps(eth, indent=2) + "\n", encoding="utf-8")
    p2.write_text(json.dumps(planes, indent=2) + "\n", encoding="utf-8")
    return p1, p2


def identity_stim(session: Session, role: str, current: float = 18.0) -> dict[str, float]:
    i_ext = np.zeros(session.graph.n, dtype=np.float64)
    for i in session.resolved.roles[role]:
        i_ext[i] = current
    hz = ply_rates(session, i_ext)
    from fly_chess.rates import mean_hz

    return {
        "feed_mn": mean_hz(hz, session.resolved.roles["feed_mn"]),
        "gf_escape": mean_hz(hz, session.resolved.roles["gf_escape"]),
        "sugar_grn": mean_hz(hz, session.resolved.roles["sugar_grn"]),
        "loom_vpn": mean_hz(hz, session.resolved.roles["loom_vpn"]),
    }
