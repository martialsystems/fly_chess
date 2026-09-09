# fly_chess

Does a frozen fly-style graph take hanging pieces and flee check when the board is painted as food and looming?

Fixture harness. Score 0.4875 vs random, shuffled 0.4875. Gate 2 not passed. Wiring is not an encoder on this graph. Not MaleCNS v1.0.

Locked from `logs/ethology_gate.json` and `logs/planes_gate.json` at n=40, both colors, 1+0.1, game seed 0, fixture hash `06d030bbf88ab6ba549022db4536d8d51221025417f03d2e8aa265869b74f0ce`. Scores copy the JSON `score` field. Interval 0.3326 to 0.6424 still contains 0.5.

Approach/avoid controller, local score 0.4875 vs random, shuffled wiring 0.4875.

Piece-plane encoding plus a trained legal-move readout, Gate 0-2, shuffled control.

Experiment 1 is a legal-move mask plus a check detector. Real score 0.4875, shuffled 0.4875. `hanging_capture_real_gt_shuffled` is true (0.177 vs 0.159) but the arms saw 774 vs 668 hanging chances (`hanging_capture_same_n` is false), so it is not the same test set. Do not promote that bit. Check-escape is 1.0 on both wirings because paint marks in-check and the mask keeps legal king-safe moves. The runs saw 41 vs 31 check positions (`check_escape_same_n` is false). That 1.0 is not evidence the graph flees. Real fled 19 times and captured 124; shuffled fled once and captured 37; both scored 0.4875 vs random. Different twitch, same chess.

Experiment 2: Gate 0 illegal rate 0. Gate 1 31/32 vs 30/32. Gate 2 0.5 vs 0.5. `load_bearing.gate2_score_real_gt_shuffled` is false. `load_bearing.wiring_is_encoder` is false.

Labellar sugar cells are a global "there is food" gain. Square identity sits on synthetic `APP_LOCUS` / `AV_LOCUS` afferents. Capture readout is `MN9`. Quiet halt is `BB` / `FG`. Full MaleCNS v1.0 is CC BY 4.0 (Berg et al., *Cell* 2026). See `THIRD_PARTY.md`.

## Fixture rates (n=40)

Same game seed for real vs shuffled wiring.

| Slice | n | Score | Illegal |
|-------|--:|------:|--------:|
| Ethology real | 40 | 0.4875 | 0 |
| Ethology shuffled | 40 | 0.4875 | 0 |
| Planes Gate 2 real | 40 | 0.5 | 0 |
| Planes Gate 2 shuffled | 40 | 0.5 | 0 |

1+0.1 is a clock for random opponents.

## How the board enters the graph

Hanging enemy pieces raise a global sugar current and the reserved appetitive locus for that square. Checks raise a global LPLC2 current and the reserved aversive locus. The verb table then the legal-move mask. Experiment 2 injects piece-planes into `PLANE_SQ` cells and trains only a linear head. Graph weights stay frozen. Fixture PSPs are instant voltage jumps (`config/lif.json`).

## How to run

```bash
/opt/homebrew/bin/python3.12 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m fly_chess
.venv/bin/python -m fly_chess resolve
.venv/bin/python -m pytest
```

Do not use stock `/usr/bin/python3 -m pytest`. Fixture stays the pytest default. MaleCNS v1.0 is opt-in:

```bash
.venv/bin/python -m pip install -e ".[malecns]"
.venv/bin/python -m fly_chess fetch
.venv/bin/python -m fly_chess identity --source malecns
```

MaleCNS identity (475 cells: sugar GRNs, MN9, LPLC2, DNp01, and 39 sugar→MN9 bridges), locked in `logs/malecns_identity.json`: sugar stim raises MN9 to 50 Hz and leaves giant fiber at 0; LPLC2 stim raises DNp01 to 50 Hz and leaves MN9 at 0. The same stims on a degree-and-sign shuffle drive both readouts and the other pathway. Identity passes. Shuffle crosstalk is true. `check_escape_same_n` is still false on the fixture lock, so Gate 2 is not quoted.

Do not quote Gate 2 on MaleCNS until identity passes and `check_escape_same_n` is true. Do not raise n to pass Gate 2 on the 290-cell fixture.

| File | Role |
|------|------|
| [AGENTS.md](AGENTS.md) | Agent rules |
| `config/type_aliases.json` | Paper nicknames to types |
| `config/lif.json` | LIF; voltage-jump PSP note |
| `data/fixtures/graph.json` | 290-neuron fixture |
| `logs/ethology_gate.json` | Locked Experiment 1 |
| `logs/planes_gate.json` | Locked Experiment 2 |
| `logs/malecns_identity.json` | Sugar→MN9 and LPLC2→DNp01 on fetched weights |
| `config/datasets.json` | MaleCNS file URLs |
| `data-provenance/malecns_v1/source.lock.json` | Doomfly-style sha256 lock |
| `scripts/fetch_malecns.py` | Opt-in download |
| `tests/test_claims.py` | Banned-token scan |

Original code is MIT.
