# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from fly_chess import BANNER
from fly_chess.claims import require_clean
from fly_chess.connectome import fetch_malecns, write_fixture
from fly_chess.match import (
    load_gates,
    play_ethology,
    play_planes_gate0,
    play_planes_gate1,
    play_planes_gate2,
    refuse_online,
)
from fly_chess.paths import LOGS, RESOLVED
from fly_chess.session import open_session


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(
        prog="fly_chess",
        description=BANNER,
    )
    parser.add_argument("--lichess", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--chesscom", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--online", action="store_true", help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("banner", help="print the allowed banner")
    sub.add_parser("fetch", help="refuses: MaleCNS fetch is not this slice")
    sub.add_parser("resolve", help="write fixture maps and resolved types")

    play = sub.add_parser("play", help="run ethology or planes on the fixture")
    play.add_argument("--exp", choices=["ethology", "planes"], required=True)
    play.add_argument("--opponent", choices=["random", "capture"], default="random")
    play.add_argument("--n", type=int, default=None)
    play.add_argument("--gate", type=int, default=None)
    play.add_argument("--shuffle", action="store_true")
    play.add_argument("--seed", type=int, default=0)
    play.add_argument("--out", type=str, default=None)
    play.add_argument("--lichess", action="store_true", help=argparse.SUPPRESS)
    play.add_argument("--chesscom", action="store_true", help=argparse.SUPPRESS)
    play.add_argument("--online", action="store_true", help=argparse.SUPPRESS)

    sh = sub.add_parser("shuffle", help="ethology or planes shuffled-wiring control")
    sh.add_argument("--exp", choices=["ethology", "planes"], required=True)
    sh.add_argument("--n", type=int, default=None)
    sh.add_argument("--seed", type=int, default=1)
    sh.add_argument("--out", type=str, default=None)

    args = parser.parse_args(argv)
    refuse_online(args)
    require_clean(BANNER, source="banner")

    if args.cmd is None or args.cmd == "banner":
        print(BANNER)
        return 0
    if args.cmd == "fetch":
        fetch_malecns()
        return 1
    if args.cmd == "resolve":
        write_fixture()
        session = open_session()
        write_resolved = RESOLVED
        print(json.dumps(session.resolved.to_dict(), indent=2))
        print(f"wrote {write_resolved}")
        if session.resolved.missing_optional:
            print("optional missing:", json.dumps(session.resolved.missing_optional))
        return 0
    if args.cmd == "play":
        return _play(args)
    if args.cmd == "shuffle":
        return _shuffle(args)
    print(BANNER)
    return 0


def _write(payload: dict, out: str | None) -> None:
    require_clean(payload.get("claim") or "", source="claim")
    text = json.dumps(payload, indent=2) + "\n"
    print(text)
    if out:
        path = Path(out)
        if not path.is_absolute():
            from fly_chess.paths import REPO

            path = REPO / path if path.parts[0] == "logs" else LOGS / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _play(args) -> int:
    gates = load_gates()
    if args.exp == "ethology":
        n = int(args.n if args.n is not None else gates["ethology_n"])
        payload = play_ethology(
            n=n, opponent=args.opponent, seed=args.seed, shuffled=args.shuffle
        )
        _write(payload, args.out or "ethology_gate.json")
        return 0 if payload["illegal"] == 0 else 2
    gate = 0 if args.gate is None else args.gate
    if gate == 0:
        payload = play_planes_gate0(n=int(args.n or gates["gate0"]["n_positions"]), seed=args.seed)
    elif gate == 1:
        payload = play_planes_gate1(seed=args.seed)
    elif gate == 2:
        payload = play_planes_gate2(n=args.n, seed=args.seed, shuffled=args.shuffle)
    else:
        raise SystemExit("gate must be 0, 1, or 2")
    _write(payload, args.out or f"planes_gate{gate}.json")
    if payload.get("illegal"):
        return 2
    return 0


def _shuffle(args) -> int:
    gates = load_gates()
    n = args.n
    if args.exp == "ethology":
        payload = play_ethology(
            n=int(n if n is not None else gates["shuffle_n"]),
            opponent="random",
            seed=args.seed,
            shuffled=True,
        )
        _write(payload, args.out or "ethology_shuffle.json")
        return 0
    payload = play_planes_gate2(
        n=int(n if n is not None else gates["shuffle_n"]),
        seed=args.seed,
        shuffled=True,
    )
    _write(payload, args.out or "planes_shuffle.json")
    return 0
