# fly_chess

Can you point a fruit-fly wiring diagram at a chessboard and get legal moves out?

Short answer: we can get legal moves. We cannot honestly say the wiring is playing chess.

## What this is

A fly's brain map says which cells talk to which. We run a small stand-in of that map (290 cells for everyday tests; a 475-cell slice of the real MaleCNS map for one circuit check). Chess never falls out of a fly looking for food. We built two translators:

- Food and danger: hanging enemy pieces count as food. Check counts as something looming. Named fly cells vote capture, flee, or sit still. Illegal votes are thrown away.
- Spreadsheet board: each square and piece type turns on reserved input cells. A tiny extra layer picks a legal move. The fly wiring stays frozen.

Both play only against a random legal opponent, on this computer. Not chess.com. Not Lichess.

## What happened

On the small test map, both translators score like coin flips (0.4875 and 0.50 in 40 games). If we scramble the wires and keep the same translator, the score does not drop. So on that map the wiring is not doing the chess work. The rulebook mask and the extra layer are.

One number looks like a win if you squint (taking hanging pieces 0.177 vs 0.159). It is not a win. The two tests did not even see the same chances (774 vs 668). We do not advertise it.

Getting out of check every time is also not a win. The paint says you are in check and the rulebook only allows safe king moves. A scrambled map does the same thing.

## What the real fly map showed

We poked sugar and looming cells on a small piece of the real fly map. The right motor cells answered. Scrambled wires did not stay specific. That is not a chess rating.

We downloaded MaleCNS v1.0 (the published male fly wiring, used here under CC BY). We did not run chess on all 166,000 cells. The 475-cell slice is sugar sensors, the feeding motor cell MN9, looming cells, and the giant-fiber escape cell. Synapses there are current-based: 8.0 current-units per contact, then leak (`docs/dynamics.md`). Touch sugar, only MN9 lights. Touch looming, only DNp01 lights. That is the paint pulse on the named cell, not a new firing-rate finding. Scramble the wires, both cells light up for both touches. Chess stays on the 290-cell fixture.

A capped two-hop-from-looming probe saturated (917 cells, 0.425 of them at the Hz cap). We aborted it. It is not the circuit graph.

## Numbers

Copied from locked files. Scores are the JSON `score` fields. MaleCNS Hz values are the injected pulse, not a firing-rate discovery.

| Test | Games | Score vs random | Same test after scrambling wires |
|------|------:|----------------:|---------------------------------:|
| Food/danger | 40 | 0.4875 | 0.4875 |
| Spreadsheet board | 40 | 0.50 | 0.50 |

MaleCNS 475-cell circuit (`logs/malecns_circuit.json`): games 0, elo null. Real sugar: MN9 37.5 Hz, DNp01 0. Real loom: DNp01 125 Hz, MN9 0. Shuffle crosstalks.

Full dumps: `logs/ethology_gate.json`, `logs/planes_gate.json`, `logs/malecns_identity.json`, `logs/malecns_circuit.json`.

## Run it

```bash
/opt/homebrew/bin/python3.12 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m fly_chess
.venv/bin/python -m pytest
```

Real MaleCNS files are optional and large. Circuit check only (paint sugar/loom on the 475-cell slice). No chess games on that graph:

```bash
.venv/bin/python -m pip install -e ".[malecns]"
.venv/bin/python -m fly_chess fetch
.venv/bin/python -m fly_chess identity --source malecns
.venv/bin/python -m fly_chess circuit --source malecns
```

Why voltage jumps seize, and why a 2-hop LPLC2 probe still saturates under current-based synapses: [docs/dynamics.md](docs/dynamics.md). That is a kernel note, not a chess gate.

Original code is MIT. MaleCNS data stays CC BY 4.0 (Berg et al., *Cell* 2026).
