# Copyright (c) 2026 Martial Systems LLC
"""Build docs/method_note.pdf from locked JSON. Research note, not a pitch."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.utils import ImageReader

REPO = Path(__file__).resolve().parents[1]
LOGS = REPO / "logs"
DOCS = REPO / "docs"
OUT = DOCS / "method_note.pdf"
NOTE_DATE = "2026-09-12"
FIXTURE_SHA = "1924ff3b0c6e23b286ea33fd47357846ccb8095eb22cae790cf49278ba61c495"


def _json(name: str) -> dict:
    return json.loads((LOGS / name).read_text(encoding="utf-8"))


def _styles() -> dict:
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName="Times-Bold",
            fontSize=16,
            leading=20,
            alignment=TA_CENTER,
            spaceAfter=6,
        ),
        "sub": ParagraphStyle(
            "Sub",
            parent=base["Normal"],
            fontName="Times-Italic",
            fontSize=11,
            leading=14,
            alignment=TA_CENTER,
            spaceAfter=4,
        ),
        "meta": ParagraphStyle(
            "Meta",
            parent=base["Normal"],
            fontName="Times-Roman",
            fontSize=10,
            leading=13,
            alignment=TA_CENTER,
            spaceAfter=12,
        ),
        "h1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontName="Times-Bold",
            fontSize=12,
            leading=16,
            spaceBefore=14,
            spaceAfter=6,
            alignment=TA_LEFT,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["Normal"],
            fontName="Times-Roman",
            fontSize=11,
            leading=15,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
        ),
        "cap": ParagraphStyle(
            "Cap",
            parent=base["Normal"],
            fontName="Times-Italic",
            fontSize=9,
            leading=12,
            alignment=TA_LEFT,
            spaceBefore=4,
            spaceAfter=10,
        ),
        "cell": ParagraphStyle(
            "Cell",
            parent=base["Normal"],
            fontName="Times-Roman",
            fontSize=8,
            leading=10,
            alignment=TA_LEFT,
        ),
        "cellb": ParagraphStyle(
            "CellB",
            parent=base["Normal"],
            fontName="Times-Bold",
            fontSize=8,
            leading=10,
            alignment=TA_LEFT,
        ),
        "rev": ParagraphStyle(
            "Rev",
            parent=base["Normal"],
            fontName="Times-Roman",
            fontSize=10,
            leading=13,
            leftIndent=12,
            spaceAfter=3,
        ),
        "left": ParagraphStyle(
            "Left",
            parent=base["Normal"],
            fontName="Times-Roman",
            fontSize=11,
            leading=15,
            alignment=TA_LEFT,
            spaceAfter=8,
        ),
    }
    return styles


def _p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def _table(rows: list[list[str]], widths: list[float], styles: dict) -> Table:
    cell, cellb = styles["cell"], styles["cellb"]
    data = []
    for i, row in enumerate(rows):
        st = cellb if i == 0 else cell
        data.append([_p(c, st) for c in row])
    grid = Table(data, colWidths=widths, repeatRows=1)
    grid.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.Color(0.4, 0.4, 0.4)),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.92, 0.92, 0.92)),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return grid


def _figure(path: Path, caption: str, styles: dict, width: float = 6.2 * inch) -> list:
    img = ImageReader(str(path))
    iw, ih = img.getSize()
    h = width * ih / iw
    if h > 3.4 * inch:
        h = 3.4 * inch
        width = h * iw / ih
    return [
        KeepTogether(
            [
                Image(str(path), width=width, height=h, hAlign="CENTER"),
                _p(caption, styles["cap"]),
            ]
        )
    ]


def _header_footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Times-Roman", 8)
    canvas.drawString(inch, letter[1] - 0.55 * inch, "fly_chess methods note")
    canvas.drawRightString(letter[0] - inch, letter[1] - 0.55 * inch, NOTE_DATE)
    canvas.setStrokeColor(colors.Color(0.5, 0.5, 0.5))
    canvas.setLineWidth(0.4)
    canvas.line(inch, letter[1] - 0.62 * inch, letter[0] - inch, letter[1] - 0.62 * inch)
    canvas.line(inch, 0.6 * inch, letter[0] - inch, 0.6 * inch)
    canvas.setFont("Times-Roman", 8)
    canvas.drawString(inch, 0.42 * inch, "Martial Systems LLC. MIT. MaleCNS data CC BY 4.0.")
    canvas.drawRightString(letter[0] - inch, 0.42 * inch, f"{doc.page}")
    canvas.restoreState()


def build() -> Path:
    styles = _styles()
    eth = _json("ethology_gate.json")
    labels = _json("planes_labels.json")
    mix = _json("planes_mix.json")
    value = _json("value_lock.json")
    hang = labels["rows"][0]["families"]["hanging"]["factored"]
    teach = labels["rows"][0]["families"]["teacher"]["factored"]
    hang1 = labels["rows"][1]["families"]["hanging"]["factored"]
    teach1 = labels["rows"][1]["families"]["teacher"]["factored"]
    mix0 = mix["rows"][0]
    mix1 = mix["rows"][1]
    mix3 = mix["rows"][2]
    a = value["A"]
    has_b = "B_real" in value and "B_shuffle" in value

    story: list = []
    story.append(_p("From a failed move head to child-position value", styles["title"]))
    story.append(_p("fly_chess methods note", styles["sub"]))
    story.append(
        _p(
            "Martial Systems LLC. 2026-09-12. Fixture sha256 "
            f"{FIXTURE_SHA}.",
            styles["meta"],
        )
    )

    story.append(_p("Revisions", styles["h1"]))
    story.append(
        _p(
            "2026-09-12: first note. Records the closed hanging/teacher policy "
            "line, the decision to train child-position value, Stage A on mix-0 "
            "occupancy, and the mix-1 shuffle protocol that remains open.",
            styles["rev"],
        )
    )

    story.append(_p("Abstract", styles["h1"]))
    story.append(
        _p(
            "A 1,007-cell fly-shaped leaky integrate-and-fire graph was given a "
            "chessboard as reserved-channel current and a legal-move mask on the "
            "way out. Two readouts were trained. The first asked whether real "
            "wiring makes a labeled legal move linearly easier than a "
            "degree-and-sign shuffle. It does not. Mix 0 is a typed occupancy "
            "register: a factored from-to head reads hanging (0.887) and a "
            "hanging-or-escape teacher (0.693) from that register. One mix ply "
            "removes those labels on real and shuffled wiring. After three plys "
            "the teacher delta includes 0. Hidden geometry still differs "
            "(knight-versus-empty cosine 0 vs 0.34 at mix 3). The wires do "
            "something. They do not pick the labeled move.",
            styles["body"],
        )
    )
    story.append(
        _p(
            "The failure mode is the training object, not the epoch count. The "
            "pipeline was: one position, write occupancy, run 1 to 3 LIF plys, "
            "linear or factored head votes a move. Mix 0 works because it is a "
            "12 x 64 board register. Mix 1 and above fail because that register "
            "is gone, on real wiring and on shuffle. A hanging-heavy catalog of "
            "130 puzzles, more epochs, or policy RL on those same mix-1 rates "
            "would turn a clean zero into a mushy almost. The sequel trains a "
            "scalar value of a child position. Mix 0 occupancy is the player. "
            "Mix 1 hidden rates, real versus five shuffle seeds, are the "
            "science. A two-layer MLP is the nonlinear probe.",
            styles["body"],
        )
    )

    story.append(_p("1. Shared apparatus", styles["h1"]))
    story.append(
        _p(
            "MaleCNS v1.0 (Berg et al., <i>Cell</i> 2026) is a published adult "
            "male <i>Drosophila</i> central-nervous-system wiring diagram. Chess "
            "in this repo is not that table. Chess uses a 1,007-cell fixture "
            "(5,103 edges) with required roles resolved fail-closed, LIF mode "
            "fixture_voltage_jump (dt 0.5 ms, "
            "tau_m 20 ms, 40 steps per ply), a python-chess legal "
            "mask, and a degree-and-sign shuffle that permutes posts within each "
            "outgoing-sign class. Five shuffle seeds {1,2,3,4,5}. Graph frozen "
            "while a head trains. Chess play on the MaleCNS source is refused. "
            "The 475-cell MaleCNS slice is identity and circuit only: "
            "sugar lights MN9, loom lights DNp01, shuffle crosstalks. Named-cell "
            "Hz is the injected pulse. 8.0 current-units is a grid pick because "
            "4.0 was silent.",
            styles["body"],
        )
    )

    story.append(_p("2. Ethology paint (historical, n=40)", styles["h1"]))
    story.append(
        _p(
            "Hanging enemy pieces raise a sugar-like current. Check and hanging "
            "own pieces raise a looming-like current. Capture is MN9, flee is "
            "DNp01, quiet is BB/FG. Square identity is synthetic APP_LOCUS / "
            "AV_LOCUS. No linear head. Locked vs a uniform random legal mover, "
            "both colors, seed 0: score 0.4875 real and 0.4875 shuffled "
            f"({eth['n_games']} games). Hanging-capture 0.177 vs 0.159 is not a "
            "win (774 vs 668 chances). Check-escape 1.0 is the mask after paint "
            "marks check (41 vs 31 positions). Leave that lock as history. It is "
            "not restamped onto the occupancy register or onto child-value.",
            styles["body"],
        )
    )
    story.extend(
        _figure(
            DOCS / "fig_games.png",
            "Figure 1. Historical game locks, n=40, random-legal opponent. "
            "Ethology 0.4875 / 0.4875. Planes Gate 2 0.50 / 0.50. Chance line "
            "is score vs random.",
            styles,
        )
    )

    story.append(_p("3. Planes policy (closed, 2026-09-10)", styles["h1"]))
    story.append(
        _p(
            "Twelve reserved pools, one cell per square per piece type, plus "
            "side-to-move, four castling cells, and eight en-passant file cells. "
            "Occupancy current 12.0. Mix 0 reads those reserved pools (synapses "
            "unused). Mix 1 and 3 run 1 or 3 LIF plys. Two heads: 4096-way "
            "from-to, and factored 64-from plus 64-to with the legal mask on the "
            "pair. Eight epochs, learning rate 0.08. Labels from injected board "
            "facts: hanging capture; check-escape (first legal escape by UCI "
            "sort); teacher = highest-value hanging capture, else that escape, "
            "else exclude. Split by FEN, no overlap. No engine.",
            styles["body"],
        )
    )
    story.append(
        _p(
            "Question: does the wiring make the labeled move linearly easier "
            "than shuffle? Figure of merit: accuracy real minus accuracy "
            "shuffle, same head, same FENs, same mix depth. Delta is allowed "
            "to be nonzero only when synapses are in the readout (mix 1 and above).",
            styles["body"],
        )
    )
    story.extend(
        _figure(
            DOCS / "fig_labels.png",
            "Figure 2. Occupancy is readable at mix 0. One mix ply deletes the "
            "hanging and teacher labels on both arms. Hanging n_eval=53, "
            "teacher n_eval=88, five seeds.",
            styles,
        )
    )
    story.extend(
        _figure(
            DOCS / "fig_delta.png",
            "Figure 3. Shuffle-controlled delta across mix depth. Mix 3 "
            "teacher linear delta includes 0. Wiring does not make the "
            "labeled move linearly easier.",
            styles,
        )
    )
    story.extend(
        _figure(
            DOCS / "fig_cosine.png",
            "Figure 4. Knight-versus-empty cosine after three plys: 0 on real "
            "wiring, 0.341 on shuffle. Hidden geometry differs. The labeled "
            "move does not.",
            styles,
        )
    )

    story.append(_p("Locked label families (2026-09-10)", styles["h1"]))
    story.append(
        _table(
            [
                ["Family", "Mix 0 factored real / shuffle", "Mix 1 factored real / shuffle"],
                [
                    "Hanging",
                    f"{hang['real_acc']:.3f} / {hang['shuffle_acc_mean']:.3f}",
                    f"{hang1['real_acc']:.3f} / {hang1['shuffle_acc_mean']:.3f}",
                ],
                [
                    "Teacher",
                    f"{teach['real_acc']:.3f} / {teach['shuffle_acc_mean']:.3f}",
                    f"{teach1['real_acc']:.3f} / {teach1['shuffle_acc_mean']:.3f}",
                ],
            ],
            [1.4 * inch, 2.55 * inch, 2.55 * inch],
            styles,
        )
    )
    story.append(
        _p(
            "Check-escape flee_ok = 1.0 at every depth on both arms: the legal "
            "mask is the decoder. Do not quote check-escape exact-match as "
            "occupancy or wiring.",
            styles["cap"],
        )
    )
    story.append(_p("Locked mix-depth, 4096-way head, 130 train / 62 eval (2026-09-10)", styles["h1"]))
    story.append(
        _table(
            [
                ["Mix plys", "Real acc", "Shuffle acc", "delta acc mean [95%]", "Knight-empty cosine"],
                [
                    "0",
                    f"{mix0['real_acc']:.3f}",
                    f"{mix0['shuffle_acc_mean']:.3f}",
                    "0.00 [0.00, 0.00]",
                    f"{mix0['cosine_knight_vs_empty_real']:.3f} / {mix0['cosine_knight_vs_empty_shuffle_mean']:.3f}",
                ],
                [
                    "1",
                    f"{mix1['real_acc']:.3f}",
                    f"{mix1['shuffle_acc_mean']:.3f}",
                    "0.003 [-0.003, 0.010]",
                    f"{mix1['cosine_knight_vs_empty_real']:.3f} / {mix1['cosine_knight_vs_empty_shuffle_mean']:.3f}",
                ],
                [
                    "3",
                    f"{mix3['real_acc']:.3f}",
                    f"{mix3['shuffle_acc_mean']:.3f}",
                    "0.003 [-0.018, 0.024]",
                    f"{mix3['cosine_knight_vs_empty_real']:.3f} / {mix3['cosine_knight_vs_empty_shuffle_mean']:.3f}",
                ],
            ],
            [0.9 * inch, 1.1 * inch, 1.2 * inch, 1.8 * inch, 1.5 * inch],
            styles,
        )
    )
    story.append(
        _p(
            "Factored occupancy read at mix 0 is 0.790, delta 0. Mix hurts "
            "both arms. The reservoir does not refine occupancy into tactics. "
            "It throws occupancy away.",
            styles["cap"],
        )
    )

    story.append(_p("4. What the policy loop actually trained (2026-09-12)", styles["h1"]))
    story.append(
        _p(
            "The closed line is a linear classifier on a labeled legal move. "
            "At mix 0 the features are injection currents on the occupancy "
            "register. A factored head can read hanging and teacher from that "
            "register because those labels are board facts still sitting on "
            "typed cells. After one LIF ply the same head is reading mixed "
            "rates. On this fixture the 64 HIDDEN cells stay subthreshold on "
            "real wiring (start-position hidden rates all 0 Hz; voltage rises "
            "from -52 mV toward -45 mV and does not spike). Shuffle "
            "rewiring lets a few hidden cells spike. Cosine therefore splits "
            "the arms. Linear move-class does not.",
            styles["body"],
        )
    )
    story.append(
        _p(
            "The catalog made the mix-0 head look smart and every mixed readout "
            "look broken for a second reason. It is hanging-heavy, teacher-sparse, "
            "and it drops quiet positions. A 4096-way policy head trained on "
            "that set is a hanging detector on a register, then noise after a "
            "ply. More FENs of the same kind, more epochs at mix 3, or RL on "
            "those mix-1 rates, keep the same object. The clean zero would "
            "become an interval that includes 0 with a story attached.",
            styles["body"],
        )
    )
    story.append(
        _p(
            "Enumerating legal moves, scoring child boards, and picking the "
            "best is a 1-ply evaluator. That loop uses the occupancy layout. "
            "It is allowed as a ranker. It is not a claim that the fly produced "
            "the move as a policy from mixed rates.",
            styles["body"],
        )
    )

    story.append(_p("5. Child-position value (open, 2026-09-12)", styles["h1"]))
    story.append(
        _p(
            f"Question: {value['question']}",
            styles["body"],
        )
    )
    story.append(
        _p(
            "<b>A. Mix-0 value head (the player).</b> Input: 12 x 64 occupancy "
            "planes plus side-to-move, castling, and en passant (781 currents, "
            "synapses unused). Output: a scalar, White-centric pawn units, "
            "material plus a small piece-square table. At test: for every legal "
            "move, push, score the child, pick the max for the mover. Ridge on "
            "parents and all legal children of the train games.",
            styles["body"],
        )
    )
    story.append(
        _p(
            "<b>B. Mix-1 value head (the science).</b> Same targets. Features: "
            "64 HIDDEN-cell rates after one ply. One copy on real wiring, one "
            "on each of five shuffle seeds. If B-real matches B-shuffle, the "
            "synapses still are not playing. If B-real beats B-shuffle by a "
            "real delta on held-out value and on games, there is a wiring "
            "effect. Cosine already says the dynamics differ. Cosine does not "
            "say the difference is chess.",
            styles["body"],
        )
    )
    story.append(
        _p(
            "<b>C. Two-layer MLP on mix-1 rates.</b> Geometry can differ and "
            "still be linearly useless. Hidden width 32, tanh, same train and "
            "eval FENs, same shuffle seeds. If the MLP delta includes 0, that "
            "line stops too.",
            styles["body"],
        )
    )
    story.append(
        _p(
            "Data: 320 self-play games from the start position under random, "
            "capture-preferring, and 1-ply material policies. Sixteen positions "
            "per game. Hold out by game_id, not by row. Train 4,096 positions "
            "(256 games), eval 1,024 (64 games). Phase mix on train: opening "
            "1,068, middlegame 1,998, simple 1,030. Quiet positions stay in. "
            "Every legal child of an eval parent is scored. Opponent at play "
            "is random legal. Report score vs that opponent and vs the mix-0 "
            "head. Ethology sugar/loom stays a separate arm (locked 0.4875). "
            "It is not the main trainer.",
            styles["body"],
        )
    )

    story.append(_p("6. Order of operations", styles["h1"]))
    story.append(
        _p(
            "1. Get A playing. If mix-0 child scoring cannot beat random by a "
            "lot, the head or the data are wrong and the fly is irrelevant.",
            styles["body"],
        )
    )
    story.append(
        _p(
            "2. Freeze A. Train B and C on the same targets.",
            styles["body"],
        )
    )
    story.append(
        _p(
            "3. Table three numbers on the same eval set: A, B-real, B-shuffle. "
            "Games n at least 200, not n=40.",
            styles["body"],
        )
    )
    story.append(
        _p(
            "4. Only if B-real beats both A and B-shuffle on held-out value and "
            "on games is wiring_helped true.",
            styles["body"],
        )
    )
    story.append(
        _p(
            "5. Only then unfreeze anything. Unfreezing synapses first is a "
            "sparse RNN that was initialized as a fly. Valid experiment, "
            "different claim: fly init versus shuffle init versus random sparse "
            "init. Publish that as init.",
            styles["body"],
        )
    )
    story.append(
        _p(
            "Kept off this line: more epochs on hanging labels at mix 3; the "
            "4096-way head as the player; a ply loop on 166k MaleCNS cells; "
            "tuning until shuffle almost loses, then dropping the shuffle; "
            "policy RL before the value-on-children table.",
            styles["body"],
        )
    )

    story.append(_p("7. Stage A mix-0 ranker (2026-09-12)", styles["h1"]))
    story.append(
        _p(
            "Ridge on occupancy currents recovers the hand eval (Pearson "
            f"{a['held_out']['pearson']:.4f} on 1,024 held-out positions, MSE "
            f"{a['held_out']['mse']:.4f}). Child pairwise ranking vs the same "
            f"target is {a['held_out']['child_pairwise']:.3f}; best-child match "
            f"{a['held_out']['best_child_match']:.3f} (n_ranked="
            f"{a['held_out']['n_ranked']}). Versus random legal, n="
            f"{a['games']['n_games']}, both colors, seed 0: score "
            f"{a['games']['score']:.2f} "
            f"[{a['games']['score_lo']:.3f}, {a['games']['score_hi']:.3f}]. "
            f"Illegal moves {a['games']['illegal']}. "
            "beats_random is "
            f"{str(a['beats_random']).lower()}. Synapses unused. Elo is null. "
            "Call it a ranker sitting on a fly-shaped input layout. The ceiling "
            "exists. The fly is now relevant as a mix-1 probe, not as this player.",
            styles["body"],
        )
    )
    story.append(
        _table(
            [
                ["Arm", "Features", "Held-out pairwise", "Games n=200 vs random"],
                [
                    "A mix-0",
                    "occupancy 12 x 64 + STM/castle/EP",
                    f"{a['held_out']['child_pairwise']:.3f}",
                    f"{a['games']['score']:.2f} [{a['games']['score_lo']:.3f}, {a['games']['score_hi']:.3f}]",
                ],
                [
                    "B-real mix-1",
                    "HIDDEN 64 after one ply, real wiring",
                    "see lock" if has_b else "running",
                    "see lock" if has_b else "running",
                ],
                [
                    "B-shuffle mix-1",
                    "same features, seeds 1 to 5",
                    "see lock" if has_b else "running",
                    "see lock" if has_b else "running",
                ],
            ],
            [1.2 * inch, 2.3 * inch, 1.5 * inch, 1.5 * inch],
            styles,
        )
    )
    if has_b:
        br, bs = value["B_real"], value["B_shuffle"]
        story.append(
            _p(
                f"B-real games {br['games']['score']}; B-shuffle games "
                f"{bs['games']['score']}; wiring_helped="
                f"{str(value.get('wiring_helped')).lower()}. "
                f"{value.get('note', '')}",
                styles["body"],
            )
        )
    else:
        story.append(
            _p(
                "B and C were started after A locked. Mix-1 real hidden rates "
                "on this fixture are silent at the start position (0 Hz); "
                "shuffle spikes a handful of hidden cells. That is already a "
                "dynamics split. The value table asks whether that split ranks "
                "chess. Lock file: logs/value_lock.json after "
                "python -m fly_chess value.",
                styles["body"],
            )
        )

    story.append(_p("8. What we will do next", styles["h1"]))
    story.append(
        _p(
            "Finish the mix-1 linear table (B-real vs five shuffles) and the "
            "two-layer MLP (C) on the same game-id split. Games n at least 200 "
            "for A, B-real, and B-shuffle. Do not unfreeze. Do not drop a "
            "shuffle seed. Do not restamp ethology 0.4875 or Gate 2 n=40.",
            styles["body"],
        )
    )
    story.append(
        _p(
            "If B-real does not beat both A and B-shuffle, the synapses are "
            "not playing this value task. The cosine split remains a geometry "
            "fact. The player remains the mix-0 ranker. That is a publishable "
            "negative on the wiring-as-evaluator claim.",
            styles["body"],
        )
    )
    story.append(
        _p(
            "If C's shuffle delta includes 0 as well, stop the mix-1 value "
            "line. A later arm, if any, is init: train sparse RNN weights from "
            "fly wiring versus shuffle versus random sparse, and say so.",
            styles["body"],
        )
    )
    story.append(
        _p(
            "Self-play reward, if we get that far: +1 checkmate, 0 draw, "
            "-1 loss, a small term for material after a few plies. A "
            "fly-native sugar/loom current on hanging remains a separate "
            "ethology arm. It already scored 0.4875.",
            styles["body"],
        )
    )

    story.append(_p("9. Files", styles["h1"]))
    story.append(
        _table(
            [
                ["Path", "Role"],
                ["docs/planes_note.md", "Closed hanging/teacher policy write-up"],
                ["docs/value_note.md", "Child-value methods"],
                ["logs/planes_labels.json", "Label-family mix table"],
                ["logs/planes_mix.json", "Mix-depth by five seeds"],
                ["logs/ethology_gate.json", "Paint controller, n=40"],
                ["logs/value_lock.json", "Child-value table"],
                ["config/value.json", "Split, freeze, shuffle seeds"],
                ["src/fly_chess/train_value.py", "A, B, C"],
                ["data/fixtures/graph.json", "1,007-cell fixture"],
            ],
            [2.4 * inch, 4.1 * inch],
            styles,
        )
    )
    story.append(Spacer(1, 10))
    story.append(
        _p(
            "Reproduce with .venv/bin/python -m pytest. "
            "Rebuild this PDF with .venv/bin/python scripts/make_method_note.py "
            "after pip install -e \".[figures]\". "
            "Original code MIT. MaleCNS data CC BY 4.0.",
            styles["left"],
        )
    )
    story.append(
        _p(
            f"Generated {date.today().isoformat()}. Build clock. It does not "
            "replace the revision dates above.",
            styles["cap"],
        )
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=letter,
        leftMargin=inch,
        rightMargin=inch,
        topMargin=0.85 * inch,
        bottomMargin=0.75 * inch,
        title="From a failed move head to child-position value",
        author="Martial Systems LLC",
        subject="fly_chess methods note",
    )
    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return OUT


if __name__ == "__main__":
    path = build()
    print(path)
