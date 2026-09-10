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
    write_locked_gates,
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
    fetch_p = sub.add_parser("fetch", help="download MaleCNS v1.0 into data/malecns (opt-in, hash-locked)")
    fetch_p.add_argument("--force", action="store_true")
    ident = sub.add_parser("identity", help="sugar→MN9 and LPLC2→DNp01 on fixture or fetched MaleCNS")
    ident.add_argument("--source", choices=["fixture", "malecns"], default="fixture")
    ident.add_argument("--lichess", action="store_true", help=argparse.SUPPRESS)
    ident.add_argument("--chesscom", action="store_true", help=argparse.SUPPRESS)
    ident.add_argument("--online", action="store_true", help=argparse.SUPPRESS)
    circ = sub.add_parser(
        "circuit",
        help="paint sugar/loom global gains on the identity subgraph; no games",
    )
    circ.add_argument("--source", choices=["fixture", "malecns"], default="fixture")
    circ.add_argument("--lichess", action="store_true", help=argparse.SUPPRESS)
    circ.add_argument("--chesscom", action="store_true", help=argparse.SUPPRESS)
    circ.add_argument("--online", action="store_true", help=argparse.SUPPRESS)
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
    play.add_argument("--source", choices=["fixture", "malecns"], default="fixture")

    sub.add_parser("lock", help="write logs/ethology_gate.json and logs/planes_gate.json at locked n")
    sub.add_parser("diagnose-planes", help="real vs shuffled readout diagnostics on the fixture")
    tr = sub.add_parser("train-planes", help="train linear head on locked FEN split; write acc table")
    sub.add_parser("mix-sweep", help="mix-depth × shuffle-seed table; not Gate 2")
    sub.add_parser("labels-sweep", help="hanging / check-escape / teacher labels; encoder frozen")
    tr.add_argument("--lichess", action="store_true", help=argparse.SUPPRESS)
    tr.add_argument("--chesscom", action="store_true", help=argparse.SUPPRESS)
    tr.add_argument("--online", action="store_true", help=argparse.SUPPRESS)

    sh = sub.add_parser("shuffle", help="ethology or planes shuffled-wiring control")
    sh.add_argument("--exp", choices=["ethology", "planes"], required=True)
    sh.add_argument("--n", type=int, default=None)
    sh.add_argument("--seed", type=int, default=1)
    sh.add_argument("--out", type=str, default=None)

    for name, help_text in (
        ("gain-sweep", "mV/contact grid on the 475-cell slice; no games"),
        ("neighborhood", "hop counts from LPLC2 and MN9; no play"),
        ("hop-probe", "capped 2-hop LPLC2 saturate probe; not the circuit graph"),
        ("signs", "transmitter audit on the 475-cell slice"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--lichess", action="store_true", help=argparse.SUPPRESS)
        p.add_argument("--chesscom", action="store_true", help=argparse.SUPPRESS)
        p.add_argument("--online", action="store_true", help=argparse.SUPPRESS)

    args = parser.parse_args(argv)
    refuse_online(args)
    require_clean(BANNER, source="banner")

    if args.cmd is None or args.cmd == "banner":
        print(BANNER)
        return 0
    if args.cmd == "fetch":
        report = fetch_malecns(force=bool(getattr(args, "force", False)))
        print(json.dumps(report, indent=2))
        return 0
    if args.cmd == "identity":
        from fly_chess.identity import write_identity

        payload = write_identity(source=args.source)
        print(json.dumps(payload, indent=2))
        return 0 if payload["passed"]["identity"] else 2
    if args.cmd == "circuit":
        from fly_chess.circuit import write_circuit

        payload = write_circuit(source=args.source)
        print(json.dumps(payload, indent=2))
        return 0 if payload["passed"]["mn9_vs_dnp01_separate"] else 2
    if args.cmd == "resolve":
        write_fixture()
        session = open_session()
        write_resolved = RESOLVED
        print(json.dumps(session.resolved.to_dict(), indent=2))
        print(f"wrote {write_resolved}")
        if session.resolved.missing_optional:
            print("optional missing:", json.dumps(session.resolved.missing_optional))
        return 0
    if args.cmd == "diagnose-planes":
        from fly_chess.diagnose_planes import write_diagnose

        payload = write_diagnose()
        print(json.dumps(payload, indent=2))
        return 0
    if args.cmd == "train-planes":
        from fly_chess.train_planes import write_train

        payload = write_train()
        print(json.dumps(payload, indent=2))
        return 0
    if args.cmd == "mix-sweep":
        from fly_chess.mix_sweep import write_mix_sweep

        payload = write_mix_sweep()
        print(json.dumps(payload, indent=2))
        return 0
    if args.cmd == "labels-sweep":
        from fly_chess.labels_sweep import write_labels_sweep

        payload = write_labels_sweep()
        print(json.dumps(payload, indent=2))
        return 0
    if args.cmd == "lock":
        p1, p2 = write_locked_gates()
        for path in (p1, p2):
            payload = json.loads(path.read_text(encoding="utf-8"))
            require_clean(payload.get("claim") or "", source=str(path))
            print(path)
            print(json.dumps(payload, indent=2))
        return 0
    if args.cmd == "play":
        return _play(args)
    if args.cmd == "shuffle":
        return _shuffle(args)
    if args.cmd == "gain-sweep":
        from fly_chess.gain_sweep import write_gain_sweep

        payload = write_gain_sweep()
        print(json.dumps(payload, indent=2))
        return 0 if payload["split_held"] else 2
    if args.cmd == "neighborhood":
        from fly_chess.neighborhood import write_neighborhood

        payload = write_neighborhood()
        print(json.dumps(payload, indent=2))
        return 0
    if args.cmd == "hop-probe":
        from fly_chess.hop_probe import write_hop_probe

        payload = write_hop_probe()
        print(json.dumps(payload, indent=2))
        return 2 if payload["aborted"] else 0
    if args.cmd == "signs":
        from fly_chess.signs import write_signs

        payload = write_signs()
        print(json.dumps(payload, indent=2))
        return 0
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
    source = getattr(args, "source", "fixture")
    if source == "malecns":
        raise SystemExit(
            "MaleCNS is identity/circuit only. "
            "Do not quote Gate 2. No play --source malecns."
        )
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
