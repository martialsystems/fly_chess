# A typed occupancy register plus a geometry change

**fly_chess planes readout.** Martial Systems LLC. 2026-09-10.

Frozen connectome, legal-move mask, trained linear then factored head. Shuffle-controlled. No engine.

## Revisions

- 2026-09-10: first write-up from locked JSON. Planes/ML line closed.
- 2026-09-10: wall sentence: 475-cell MaleCNS identity/circuit is a different object from the planes readout.

## Abstract

If a fly-shaped leaky integrate-and-fire graph is given a chessboard as reserved-channel current, and a legal-move mask sits on the way out, does the wiring make a labeled move linearly easier than a degree-and-sign shuffle of the same graph?

No. Mix 0 is a typed occupancy register. A factored 64-from plus 64-to head reads hanging (0.887) and a hanging-or-escape teacher (0.693) from that register; a 4096-way from-to head does not (hanging 0.170, teacher 0.239). One mix ply removes those labels on real and shuffled wiring (teacher factored 0.693 to 0.261 / 0.273). After three plys the teacher Δ includes 0. Hidden geometry still differs (knight-versus-empty cosine 0 vs 0.34). The wires do something. They do not do this.

## 1. Question

MaleCNS v1.0 (Berg et al., *Cell* 2026) is a published adult male *Drosophila* central-nervous-system wiring diagram. This repo does not train that table as a chess player. It asks whether a LIF run of a small stand-in graph, with the board written into reserved cells and illegal votes thrown away, yields a wiring-dependent linear class for a labeled legal move.

The figure is shuffle-controlled Δ: accuracy on real wiring minus accuracy on a degree-and-sign shuffle, same head, same FENs, same mix depth. Δ is allowed to be nonzero only when synapses are in the readout (mix ≥ 1). At mix 0 the injection never uses edges, so Δ must be ~0.

## 2. Methods

Two interfaces share the importer, the LIF kernel (`config/lif.json`), the legal-move mask (`python-chess`), and the shuffle (`src/fly_chess/shuffle.py`: permute posts within outgoing-sign class).

**Ethology (paint controller).** Hanging enemy pieces raise a sugar-like current. Check and hanging own pieces raise a looming-like current. Capture is MN9, flee is DNp01, quiet is BB/FG. Square identity is synthetic APP_LOCUS / AV_LOCUS. Labellar GRNs get a global gain only. No linear head. Locked at n=40 vs a uniform random legal mover, both colors, seed 0: score 0.4875 real and 0.4875 shuffled (`logs/ethology_gate.json`). Hanging-capture 0.177 vs 0.159 is not a win (774 vs 668 chances). Check-escape 1.0 is the mask after paint marks check (41 vs 31 positions). Leave that lock as history. Do not restamp it onto the occupancy register.

**Planes (frozen graph, trained head).** Twelve reserved pools, one cell per square per piece type, plus STM, four castling cells, and eight EP-file cells. Occupancy current is 12.0 on the matching pool cell (`config/planes.json`). Mix 0 reads those reserved pools (synapses unused). Mix 1 and 3 run 1 or 3 LIF plys and read the hidden pool. Fixture LIF is `fixture_voltage_jump`: dt 0.5 ms, tau_m 20 ms, 40 steps per ply. Two heads, graph frozen: 4096-way from-to (`LinearHead.train_step` unchanged) and factored 64+64 with the legal mask on the pair. Eight epochs, lr 0.08. Five shuffle seeds {1,2,3,4,5}. No Stockfish. No Lichess. No Elo.

**Label families** (`logs/planes_labels.json`), split by FEN, no overlap (`config/planes_labels_split.json`):

1. Hanging capture: current hanging catalog only (165 unique FENs; 112 train / 53 eval). No new hanging twins.
2. Check-escape: us to move in check and a legal escape exists. Exact-match target is the first legal escape by UCI sort. Also log flee_ok: chosen move is legal and leaves the side not in check (same metric as ethology).
3. Teacher, deterministic: if a hanging enemy piece can be taken, take the highest-value one; else if in check, that same first escape; else exclude the position (186 train / 88 eval).

**Fixture.** 1,007 cells, 5,103 edges, sha256 `1924ff3b0c6e23b286ea33fd47357846ccb8095eb22cae790cf49278ba61c495` (`data-provenance/fixture.lock.json`). Not the 166k-cell MaleCNS table. `play --source malecns` exits.

**MaleCNS circuit (separate).** 475-cell sugar/loom slice, current-based synapses, 8.0 current-units per contact because 4.0 was silent. Identity and paint split hold; shuffle crosstalks. Named-cell Hz is the injected pulse. Games 0, elo null, gate2_quoted false. A capped 2-hop LPLC2 probe aborted (917 cells, saturate_frac 0.425, max_hz 425). See `docs/dynamics.md`. The 475-cell MaleCNS identity/circuit work is a different object (sugar → MN9, loom → DNp01, shuffle crosstalk). It is a path check on a slice. It is not the planes readout and not a move class.

## 3. Results

Caption:

1. Reserved pools reconstruct occupancy; a factored from-to head reads a hanging/teacher label from that register.
2. One mix ply removes those labels on real and shuffled wiring.
3. Hidden geometry differs after three plys; the labeled move does not.

**Mix-depth table** (`logs/planes_mix.json`), pooled hanging-heavy catalog, 130 train / 62 eval, five seeds. 4096-way head unless noted.

| Mix plys | Real acc / rank | Shuffle acc / rank | Δ acc mean [95%] | Knight-empty cosine real / shuffle |
|----------|----------------:|-------------------:|------------------:|-----------------------------------:|
| 0 (reserved pools) | 0.226 / 6.39 | 0.226 / 6.39 | 0.00 [0.00, 0.00] | 0.824 / 0.824 |
| 1 | 0.177 / 3.98 | 0.174 / 4.34 | 0.003 [-0.003, 0.010] | 0 / 0 |
| 3 | 0.177 / 4.76 | 0.174 / 5.47 | 0.003 [-0.018, 0.024] | 0 / 0.341 |

Factored head at mix 0: 0.790 both arms, Δ 0. After mix it does not beat shuffle (mix 3: 0.258 vs 0.306). Mix hurts both arms: 4096-way 0.226 to 0.177 after one ply. The reservoir does not refine occupancy into tactics. It throws occupancy away.

**Label families** (`logs/planes_labels.json`). Factored mix-0 vs mix-1; mix-3 teacher linear Δ.

| Family | Mix 0 factored real / shuffle | Mix 1 factored real / shuffle | Mix 3 linear Δ acc [95%] |
|--------|------------------------------:|------------------------------:|-------------------------:|
| Hanging | 0.887 / 0.887 | 0.208 / 0.204 | 0.011 [-0.003, 0.026] |
| Teacher | 0.693 / 0.693 | 0.261 / 0.273 | -0.016 [-0.050, 0.018] |

Check-escape is not a third occupancy or wiring family. flee_ok = 1.0 at every mix depth on both arms: the legal mask is the decoder. Do not quote 0.771 as a wiring or occupancy result. Exact-match check-escape numbers live in the JSON for completeness only.

`logs/planes_head.json` is a one-seed pointer (n_eval=10, rank 3.9 vs 1.9, acc 0.5 vs 0.7). Two puzzles. Leave it. Do not treat -0.2 as a lock.

**Pre-register vs this table.** Teacher factored is high at mix 0 (occupancy still readable). It drops on both arms after one ply. Mix 3 teacher Δ includes 0: wiring is not carrying a small chess dictionary. Frozen connectome plus linear or factored head plus legal mask is not a move picker that uses synapses. More FENs, more epochs, or a bigger W cannot recover a code the mix already erased.

**Ethology and Gate 2.** Historical game locks on a random-legal opponent, n=40: ethology 0.4875 / 0.4875; planes Gate 2 0.50 / 0.50, `gate2_passed` false, `wiring_is_encoder` false (`logs/planes_gate.json`). Do not restamp those onto the occupancy register. They are not skill.

## 4. Limits

- Fixture, not 166k cells. No MaleCNS games.
- Hanging-heavy catalog. Teacher is hanging else escape else exclude.
- Check-escape set is mask-degenerate (flee_ok = 1.0).
- Five shuffle seeds, eight epochs, lr 0.08. Mix 0 features are injection currents, not hidden rates.
- 8.0 current-units on MaleCNS is a grid pick because 4.0 was silent, not a biophysics constant. 12.5 Hz and 37.5 Hz on MN9 are injected-pulse responses; MN9 is a two-cell mean.

## 5. Files and how to rerun

Do not start a new head on this object. Rerun only to reproduce the locks.

```bash
/opt/homebrew/bin/python3.12 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m pytest
.venv/bin/python -m fly_chess mix-sweep
.venv/bin/python -m fly_chess labels-sweep
```

MaleCNS circuit (optional, large feathers, not games):

```bash
.venv/bin/python -m pip install -e ".[malecns]"
.venv/bin/python -m fly_chess fetch
.venv/bin/python -m fly_chess identity --source malecns
.venv/bin/python -m fly_chess circuit --source malecns
```

`play --source malecns` exits.

| Path | Role |
|------|------|
| `logs/planes_labels.json` | Label-family mix table (this note) |
| `logs/planes_mix.json` | Pooled mix-depth × five seeds |
| `logs/planes_head.json` | One-seed pointer; not a lock |
| `logs/ethology_gate.json` | Paint controller, n=40 |
| `logs/planes_gate.json` | Gate 0 to 2 history, n=40 |
| `config/planes_labels_split.json` | Label-family FEN split |
| `config/planes_split.json` | Mix-sweep FEN split |
| `config/planes.json` | Occupancy currents and mix_plies |
| `config/lif.json` | `fixture_voltage_jump`, `malecns_current` |
| `data/fixtures/graph.json` | 1,007-cell fixture |
| `src/fly_chess/head.py` | LinearHead and FactoredHead |
| `src/fly_chess/labels.py` | Teacher: hanging else escape else exclude |
| `docs/dynamics.md` | MaleCNS PSP and 2-hop abort |
| `description.txt` | GitHub hook |

Sequel work, if any, needs a new question. Another catalog, another head, or RL on the same rates is how a clean zero becomes a mushy almost. Occupancy is readable before a ply. One mix ply deletes the labels. That is closed.

Original code MIT. MaleCNS data CC BY 4.0.
