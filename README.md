# fly_chess

A connectome-constrained network pointed at chess.

MaleCNS v1.0 (Berg et al., *Cell* 2026) is the published wiring of an adult male *Drosophila* central nervous system. This repo asks a narrow question: if that graph is run as a leaky integrate-and-fire network, with a chessboard written into a few sensory channels and a legal-move mask on the way out, what can be measured.

Two interfaces share the importer, the LIF kernel, the legal-move mask, and a degree-and-sign shuffle.

- Ethology. Hanging enemy pieces raise a sugar-like current. Check and hanging own pieces raise a looming-like current. Capture is read from MN9, flee from DNp01 (giant fiber), quiet from BB/FG. Square identity lives on reserved locus cells; labellar GRNs get a global gain only.
- Planes. Twelve piece occupancies, side to move, castling, and en passant inject into reserved `PLANE_SQ` cells. A linear head on a frozen readout pool maps rates to legal from-to moves.

Everyday tests use a 290-cell fixture. Circuit work uses a 475-cell MaleCNS slice (sugar GRNs, MN9, LPLC2, DNp01, and 39 disynaptic sugar→MN9 bridges). The full ~166k-cell table is not the default graph.

## Results

Copied from the lock files under `logs/`.

On the fixture, 40 games each color against a uniform random legal mover, time control 1+0.1:

| Interface | Score | Shuffled wiring |
|-----------|------:|----------------:|
| Ethology  | 0.4875 | 0.4875 |
| Planes    | 0.50   | 0.50 |

The two arms of the ethology hanging-piece count are not the same test set (774 vs 668 chances). Check-escape is 1.0 on both wirings when the paint marks check and the mask keeps king-safe moves; those runs saw 41 vs 31 check positions.

On the 475-cell MaleCNS slice, synapses are current-based (`malecns_current` in `config/lif.json`: 8.0 current-units per contact, leak through tau_m). 8.0 current-units is a grid pick because 4.0 was silent, not a fly biophysics constant. A sugar pulse raises MN9 and leaves DNp01 at rest. An LPLC2 pulse raises DNp01 and leaves MN9 at rest. The same pulses on a shuffled graph drive both readouts. Those hertz values track the injected pulse. 12.5 Hz and 37.5 Hz are injected-pulse responses on an intact path, and MN9 is a two-cell mean. Direct sugar→MN9 edges are absent; the path is the 39 bridges. Required-role signs all +1 is the 475-cell mix, not a whole-brain transmitter table.

A capped two-hop neighborhood of LPLC2 (917 cells under an 8,000-cell cap; hop 1 is already larger than the cap) reached saturate_frac 0.425 and max_hz 425. Hop 1 already hits the 8,000 cap, so 917 cells is a budgeted probe, not the true 2-hop map. That probe was aborted. It is not the circuit graph. Notes on why LPLC2 fans out, and why voltage-jump PSPs seize, are in [docs/dynamics.md](docs/dynamics.md).

## Data

MaleCNS v1.0 is CC BY 4.0 (FlyEM / Janelia, Cambridge, MRC LMB, Google Research). File URLs and sha256 locks live in `config/datasets.json` and `data-provenance/malecns_v1/source.lock.json`. The 1 GB edge table is not in git. Fetch it locally if you want the circuit commands.

## Run

```bash
/opt/homebrew/bin/python3.12 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m fly_chess
.venv/bin/python -m pytest
```

MaleCNS feathers, then the slice checks:

```bash
.venv/bin/python -m pip install -e ".[malecns]"
.venv/bin/python -m fly_chess fetch
.venv/bin/python -m fly_chess identity --source malecns
.venv/bin/python -m fly_chess circuit --source malecns
```

`play` uses the fixture. `play --source malecns` exits; the slice has no game loop.

`python -m fly_chess lock` rewrites `logs/ethology_gate.json` and `logs/planes_gate.json`. Restamp the table above from those files if the numbers move.

## Layout

| Path | Role |
|------|------|
| `config/type_aliases.json` | Paper names → types |
| `config/lif.json` | `fixture_voltage_jump` and `malecns_current` |
| `data/fixtures/graph.json` | 290-cell fixture |
| `logs/ethology_gate.json` | Experiment 1 lock |
| `logs/planes_gate.json` | Experiment 2 lock |
| `logs/malecns_identity.json` | 475-cell identity |
| `logs/malecns_circuit.json` | 475-cell paint check |
| `logs/malecns_hop_probe.json` | Capped LPLC2 neighborhood |
| `logs/malecns_signs.json` | Required-role transmitter census |
| `docs/dynamics.md` | PSP and fan-out notes |

Code is MIT. MaleCNS remains CC BY 4.0.
