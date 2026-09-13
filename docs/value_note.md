# Child-position value

Closed 2026-09-12. Chess-on-wiring is done. Do not restamp. Tables stay in `docs/method_note.pdf` and the lock JSON.

**fly_chess value readout.** Martial Systems LLC. 2026-09-12.

Frozen connectome, legal-move mask, five shuffle seeds. The player is a mix-0 occupancy ranker that scores children. Mix-1 hidden rates are the wiring probe.

## Revisions

- 2026-09-12: first write-up. New object: child-position value. Planes hanging/teacher policy stays closed.
- 2026-09-12: public methods PDF `docs/method_note.pdf` pinned on the README.
- 2026-09-12: lock table. A 0.91 vs random n=200. B-real 0.4825. B-shuffle 0.5665. wiring_helped false.
- 2026-09-12: mix-0 self-play. 0.6075 vs random n=200. 0.25 vs A. Graph frozen.
- 2026-09-12: truncated-return self-play closed. Distill A-vs-A children with hand-eval: 0.905 vs random. 2-ply residual 0.83 vs random, 0 vs searched A.
- 2026-09-12: distill is A. Residual not promoted. 2-ply search 0.995 vs 1-ply A, n=200 decisive. Mix-1 child distill real silent, wiring_helped false.
- 2026-09-12: chess-on-wiring closed. Do not restamp. Mix-1 chess distill stays off.

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

**Mix-0 self-play** (`logs/value_selfplay.json`). 400 games from the frozen A ranker, half vs random, half vs itself. 22,003 train / 5,365 eval positions, hold out by game. +1 / 0 / -1 for White plus 0.05 tanh(hand_eval/10) on truncation. 155 mates, 245 truncations. Held-out Pearson 0.786.

| Player | vs random n=200 | vs A n=200 |
|--------|----------------:|-----------:|
| A hand-eval mix-0 | 0.91 [0.870, 0.950] | same player |
| Self-play mix-0 | 0.6075 [0.540, 0.675] | 0.25 [0.190, 0.310] |

Self-play beats random. It does not beat A. Outcome labels are weaker than dense child hand-eval for this occupancy ranker.

**Mix-0 distill** (`logs/value_distill.json`). 200 A-vs-A games after a short random opening. Every legal child labeled with hand-eval, not an 80-ply truncated return. 8,681 train / 2,335 eval parents, 50,812 eval children, hold out by game. Pearson 0.989. `matches_A` true.

| Player | vs random n=200 | vs 1-ply A | vs 2-ply search |
|--------|----------------:|-----------:|----------------:|
| Distill mix-0 | 0.905 [0.864, 0.946] | 0.50 | 0.50 |
| Distill + 0.2 residual toward 2-ply | 0.83 [0.778, 0.882] | 0.25 | 0.00 |

Distill is A. Residual not promoted. `value --stage selfplay` exits.

**Search at inference** (`logs/search_lock.json`). 2-ply and 3-ply loops over the mix-0 eval. Cap: mate, resign at an 8-pawn swing from the start eval, or 400 ply. 1-ply vs 1-ply is 200 same-policy games, not a 0.50 result. 2-ply vs 1-ply A: 0.995, 200 decisive, 0 same-policy, mean ply 19.7. 3-ply vs 1-ply A: 1.0, n=40 decisive. Canary FEN `4k3/4p3/8/8/8/8/4Q3/4K3 w - - 0 1`: 1-ply Qxe7, 2-ply Qb5.

**Mix-1 child distill** (`logs/mix1_distill.json`). A's child hand-eval onto 64 HIDDEN rates after one ply. Real arm silent (0 Hz), Pearson 0.0, 0.025 vs A (n=200 decisive). Shuffle Pearson mean 0.147, vs A 0.01 to 0.225. `wiring_helped` false.

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
