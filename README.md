# fly_chess

Approach/avoid controller, local score X vs random, shuffled wiring Y.

Piece-plane encoding plus a trained legal-move readout, Gate N, shuffled control.

Two experiments share MaleCNS-style LIF on a fixture graph that covers the required roles. They do not share claims. The default graph is a few hundred neurons so tests run without the multi-GB MaleCNS download. Full `male-cns:v1.0` stays CC BY 4.0 (Berg et al., *Cell* 2026; [download](https://male-cns.janelia.org/download/)). See `THIRD_PARTY.md`.

## Experiment 1: ethological controller

The board is painted as food and loom. Hanging enemy pieces drive a global sugar gain plus **synthetic** `APP_LOCUS` cells, one reserved afferent per square. Labellar GRNs (`LB3b`, `LB3c`, `PhG1a-c`, `LgLG3`, `LgLG4`) are not an 8×8 retina; they get a global gain only. Hottest square is argmax of reserved locus rates. Capture readout is `MN9` (optional `MN8` / `MN6`). If `MN9` is missing, Experiment 1 does not start. Fudog / `DNg67` / `GNG232` are optional partners.

Checks and hanging own pieces drive a global LPLC2 gain plus synthetic `AV_LOCUS` cells. Flee readout is `DNp01`. Quiet halt is `BB` / `FG`, not `BRK`, not a second `DNp09` decoder. Verb then legal-move mask.

## Experiment 2: piece-planes plus a head

Twelve piece occupancies, side to move, castling, and en passant inject into reserved `PLANE_SQ` cells. The graph is frozen. A linear head on the `HIDDEN` pool maps rates to legal from-to logits. Gate 0: illegal rate 0. Gate 1: mate-in-1 and hanging-piece puzzles. Gate 2: score vs a uniform random legal mover. Flee metric is `us_to_move_in_check` (`config/gates.json`). Time control 1+0.1 is a clock for random opponents; it is not a Stockfish Elo.

## How to run

```text
/opt/homebrew/bin/python3.12 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m fly_chess
.venv/bin/python -m fly_chess resolve
.venv/bin/python -m fly_chess play --exp ethology --opponent random --n 8 --out logs/ethology_gate.json
.venv/bin/python -m fly_chess play --exp planes --gate 0
.venv/bin/python -m fly_chess shuffle --exp ethology --n 4
.venv/bin/python -m pytest
```

## Files

| Path | Role |
|------|------|
| `config/type_aliases.json` | Paper nicknames to MaleCNS-style types |
| `data/fixtures/graph.json` | CI fixture |
| `data/ethology_map.json` | Frozen locus table (written by resolve) |
| `data/planes_map.json` | Frozen plane table (written by resolve) |
| `tests/test_claims.py` | Banned-token scan |
| `vbd.runtime.json` | pytest plus play smoke |

Original code is MIT. The connectome, if you fetch it later, remains CC BY 4.0.
