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

We downloaded MaleCNS v1.0 (the published male fly wiring, used here under CC BY). We did not run chess on all 166,000 cells.

We kept a 475-cell slice: sugar sensors, the feeding motor cell MN9, looming cells, and the giant-fiber escape cell. Touch sugar, only the feeding cell lights up. Touch looming, only the escape cell lights up. Scramble the wires, both cells light up for both touches. That means those two fly circuits are really in the file. It does not mean the fly can play chess.

A wider two-hop-from-looming slice was about 156,000 cells and the model froze. We threw that run away. It is not in the lock files.

## Numbers

Copied from locked files. Scores are the JSON `score` fields.

| Test | Games | Score vs random | Same test after scrambling wires |
|------|------:|----------------:|---------------------------------:|
| Food/danger | 40 | 0.4875 | 0.4875 |
| Spreadsheet board | 40 | 0.50 | 0.50 |

Full dumps: `logs/ethology_gate.json`, `logs/planes_gate.json`, `logs/malecns_identity.json`, `logs/malecns_circuit.json`.

## Run it

```bash
/opt/homebrew/bin/python3.12 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m fly_chess
.venv/bin/python -m pytest
```

Real MaleCNS files are optional and large. Circuit check only (paint sugar/loom gains on the 475-cell slice). No chess games on that graph:

```bash
.venv/bin/python -m pip install -e ".[malecns]"
.venv/bin/python -m fly_chess fetch
.venv/bin/python -m fly_chess identity --source malecns
.venv/bin/python -m fly_chess circuit --source malecns
```

Why a 2-hop LPLC2 slice seizes: [docs/dynamics.md](docs/dynamics.md). That is a kernel bug, not a chess gate.

Original code is MIT. MaleCNS data stays CC BY 4.0 (Berg et al., *Cell* 2026).
