# fly_chess

Does a frozen fly-style graph take hanging pieces and flee check when the board is painted as food and looming?

Fixture harness. Score 0.4875 vs random, shuffled 0.4875. Gate 2 not passed. Wiring is not an encoder on this graph. Not MaleCNS v1.0.

Locked from `logs/ethology_gate.json` and `logs/planes_gate.json` at n=40, both colors, 1+0.1, game seed 0, fixture hash `06d030bbf88ab6ba549022db4536d8d51221025417f03d2e8aa265869b74f0ce`. Scores copy the JSON `score` field. Interval 0.3326 to 0.6424 still contains 0.5.

Approach/avoid controller, local score 0.4875 vs random, shuffled wiring 0.4875.

Piece-plane encoding plus a trained legal-move readout, Gate 0-2, shuffled control.

Experiment 1 is a legal-move mask plus a check detector. Real score 0.4875, shuffled 0.4875. Hanging-capture 0.17700258397932817 vs 0.15868263473053892 is one extra capture in a noisy bin. Check-escape is 1.0 on both wirings because paint marks in-check and the mask keeps legal king-safe moves. The runs saw 41 vs 31 check positions (`load_bearing.check_escape_same_n` is false). That 1.0 is not evidence the graph flees.

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

Do not use stock `/usr/bin/python3 -m pytest`. `lock` rewrites the JSON at n=40; this slice keeps the committed numbers. Do not raise n to pass Gate 2 on the 290-cell fixture.

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
