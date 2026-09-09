# fly_chess

Does a frozen fly-style graph take hanging pieces and flee check when the board is painted as food and looming?

On the 290-neuron fixture it flees check when it can, and it takes some hanging pieces. It does not beat a random legal mover. Locked from `logs/ethology_gate.json` at n=40, both colors, 1+0.1, game seed 0. Score 0.487 vs random (interval 0.333 to 0.642). Hanging-capture 0.177 vs shuffled 0.159. Check-escape 1.0 on 41 us-to-move-in-check positions (shuffled 1.0 on 31). Illegal 0. Fixture hash `06d030bbf88ab6ba549022db4536d8d51221025417f03d2e8aa265869b74f0ce`.

Approach/avoid controller, local score 0.487 vs random, shuffled wiring 0.487.

Piece-plane encoding plus a trained legal-move readout, Gate 0-2, shuffled control.

This is a fixture harness. Labellar sugar cells are a global "there is food" gain. Square identity sits on synthetic `APP_LOCUS` / `AV_LOCUS` afferents. Capture readout is `MN9`. Flee is `DNp01`. Quiet halt is `BB` / `FG`. Fudog / `DNg67` / `GNG232` are optional and missing here. Full MaleCNS v1.0 is CC BY 4.0 (Berg et al., *Cell* 2026); it is not in this tree. See `THIRD_PARTY.md`.

## Fixture rates (n=40)

Locked from `logs/ethology_gate.json` and `logs/planes_gate.json`. Same game seed for real vs shuffled wiring.

| Slice | n | Score | Hanging capture | Check-escape | Illegal |
|-------|--:|------:|----------------:|-------------:|--------:|
| Ethology real | 40 | 0.487 | 0.177 | 1.0 (41) | 0 |
| Ethology shuffled | 40 | 0.487 | 0.159 | 1.0 (31) | 0 |
| Planes Gate 2 real | 40 | 0.50 |  |  | 0 |
| Planes Gate 2 shuffled | 40 | 0.50 |  |  | 0 |

Planes Gate 0: illegal rate 0 on 32 positions. Gate 1: 0.969 real vs 0.938 shuffled on 32 mate-in-1 and hanging-piece puzzles. Gate 2 score interval includes 0.5, so Gate 2 is not passed. Shuffled Gate 2 matches real: the wiring is not an encoder on this fixture.

1+0.1 is a clock for random opponents. It is not a Stockfish Elo.

## How the board enters the graph

Hanging enemy pieces raise a global sugar current and the reserved appetitive locus for that square. Checks and hanging own pieces raise a global LPLC2 current and the reserved aversive locus. The verb table reads `MN9`, `DNp01`, walk/steer/halt clusters, then the legal-move mask. Experiment 2 injects piece-planes into `PLANE_SQ` cells and trains only a linear head. Graph weights stay frozen. Fixture PSPs are instant voltage jumps (`config/lif.json`); that is a fixture calibration, not a Shiu full-brain synapse.

## How to run

```bash
/opt/homebrew/bin/python3.12 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m fly_chess
.venv/bin/python -m fly_chess resolve
.venv/bin/python -m fly_chess lock
.venv/bin/python -m pytest
```

Do not use stock `/usr/bin/python3 -m pytest`. `lock` rewrites the two JSON files at n=40; restamp the README from those files if the numbers move.

| File | Role |
|------|------|
| [AGENTS.md](AGENTS.md) | Agent rules |
| `config/type_aliases.json` | Paper nicknames to types |
| `config/lif.json` | LIF; voltage-jump PSP note |
| `data/fixtures/graph.json` | 290-neuron fixture |
| `logs/ethology_gate.json` | Locked Experiment 1 |
| `logs/planes_gate.json` | Locked Experiment 2 |
| `tests/test_claims.py` | Banned-token scan |

Original code is MIT.
