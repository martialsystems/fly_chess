# Child-position value

**fly_chess value readout.** Martial Systems LLC. 2026-09-12.

Frozen connectome, legal-move mask, five shuffle seeds. The player is a mix-0 occupancy ranker that scores children. Mix-1 hidden rates are the wiring probe.

## Revisions

- 2026-09-12: first write-up. New object: child-position value. Planes hanging/teacher policy stays closed.
- 2026-09-12: public methods PDF `docs/method_note.pdf` pinned on the README.
- 2026-09-12: lock table. A 0.91 vs random n=200. B-real 0.4825. B-shuffle 0.5665. wiring_helped false.

## Abstract

The hanging/teacher policy head read a mix-0 occupancy register and lost those labels after one mix ply on real and shuffled wiring. More epochs on that catalog would not put the register back.

This measurement trains a scalar value of a position. At test it enumerates legal moves, scores each child, and picks the max. Mix 0 uses the 12×64 occupancy planes plus side-to-move, castling, and en passant. Mix 1 uses the 64 HIDDEN-cell rates after one LIF ply. One linear copy on real wiring, one on each of five degree-and-sign shuffles. A two-layer MLP is the nonlinear mix-1 probe.

## 1. Question

On dense game positions, does mix-0 child scoring beat a uniform random legal mover, and do mix-1 hidden rates on real wiring beat shuffle at the same value task?

Wiring helped only if mix-1 real beats both mix-0 and shuffle on held-out child ranking and on games n≥200.

## 2. Methods

Same fixture (1,007 cells), same LIF (`fixture_voltage_jump`), same legal mask, same shuffle seeds {1,2,3,4,5}. Graph frozen. The player is the mix-0 occupancy ranker. Chess stays on this fixture. The trainer is the self-play catalog.

**Target.** White-centric hand eval in pawn units: material plus a small piece-square table. Mate is terminal. Ethology sugar/loom stays a separate historical arm (0.4875 / 0.4875, n=40).

**Catalog.** Self-play games from the start position under random, capture-preferring, and 1-ply material policies. Sample opening, middlegame, and simple positions. Hold out by `game_id`. Every legal child of an eval parent is scored. Quiet positions stay in.

**Heads.**

1. Mix-0 linear value on occupancy currents (synapses unused). This is the player.
2. Mix-1 linear value on hidden rates, real vs shuffle.
3. Mix-1 two-layer tanh MLP (hidden 32) on the same rates and the same split.

**Play.** 1-ply: push each legal move, score the child, pick the max for the mover. Opponent is random legal. Report score vs that opponent, not Elo.

## 3. Results (2026-09-12)

Copied from `logs/value_lock.json`. Catalog: 4,096 train / 1,024 eval positions, hold out by game_id. Games n=200 vs random legal.

| Arm | Held-out pairwise | Games vs random |
|-----|------------------:|----------------:|
| A mix-0 occupancy | 0.959 | 0.91 [0.870, 0.950] |
| B-real mix-1 hidden | 0.00685 | 0.4825 |
| B-shuffle mix-1 hidden | 0.265 | 0.5665 |

A Pearson vs hand eval is 0.9997. Mix-1 real hidden rates are silent (`train_rate_max` 0). Shuffle spikes a few cells. Games delta real minus shuffle -0.084 [-0.110, -0.058]. `wiring_helped` false. `unfreeze_allowed` false.

C, two-layer MLP: real pairwise 0.00685, shuffle 0.260. Pairwise delta -0.253 [-0.266, -0.239]. The interval excludes 0 and the sign is negative. The mix-1 value line stops. The player is the mix-0 ranker.

## 4. Files

| Path | Role |
|------|------|
| `config/value.json` | Split, seeds, freeze |
| `src/fly_chess/hand_eval.py` | White-centric target |
| `src/fly_chess/child_value.py` | Legal-child loop |
| `src/fly_chess/dense_catalog.py` | Game-id holdout |
| `src/fly_chess/train_value.py` | A, B, C |
| `logs/value_lock.json` | Table |
| `docs/planes_note.md` | Closed hanging/teacher policy |

Original code MIT. MaleCNS data CC BY 4.0.
