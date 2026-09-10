# Copyright (c) 2026 Martial Systems LLC
"""Label-family sweep. Encoder frozen. Not Gate 2. No engine."""

from __future__ import annotations

import json

import numpy as np

from fly_chess.head import FactoredHead, LinearHead
from fly_chess.labels import (
    check_escape_family,
    escapes_check,
    family_split,
    hanging_family,
    teacher_family,
)
from fly_chess.lif import HZ_NOTE
from fly_chess.mix_sweep import (
    EPOCHS,
    LR,
    MIX_DEPTHS,
    SHUFFLE_SEEDS,
    _cache,
    _eval,
    _mean_interval,
    _train,
)
from fly_chess.paths import LOGS
from fly_chess.planes import load_planes_cfg
from fly_chess.session import open_session

TABLE_PATH = LOGS / "planes_labels.json"


def _eval_family(head, feats, rows, *, family: str) -> dict:
    out = _eval(head, feats, rows)
    if family == "check_escape":
        flee = 0
        for feat, (board, _target, _k) in zip(feats, rows):
            move = head.pick(board.copy(), feat)
            if board.is_check() and escapes_check(board, move):
                flee += 1
        out["flee_ok"] = flee / max(len(rows), 1)
    return out


def _subset_cache(all_rows, all_feats, subset) -> list:
    index = {b.fen(): i for i, (b, _t, _k) in enumerate(all_rows)}
    feats = []
    kept = []
    for board, target, kind in subset:
        i = index.get(board.fen())
        if i is None:
            continue
        feats.append(all_feats[i])
        kept.append((board, target, kind))
    return feats, kept


def _family_block(real_ev, shuf_evs) -> dict:
    deltas = [real_ev["accuracy"] - row["accuracy"] for row in shuf_evs]
    dmean, dlo, dhi = _mean_interval(deltas)
    ranks = [real_ev["mean_target_rank"] - row["mean_target_rank"] for row in shuf_evs]
    rmean, _rlo, _rhi = _mean_interval(ranks)
    out = {
        "n_eval": real_ev["n"],
        "real_acc": real_ev["accuracy"],
        "real_mean_target_rank": real_ev["mean_target_rank"],
        "shuffle_acc_mean": float(np.mean([r["accuracy"] for r in shuf_evs])),
        "shuffle_mean_target_rank_mean": float(
            np.mean([r["mean_target_rank"] for r in shuf_evs])
        ),
        "delta_acc_mean": dmean,
        "delta_acc_lo": dlo,
        "delta_acc_hi": dhi,
        "delta_rank_mean": rmean,
        "shuffle_acc": [r["accuracy"] for r in shuf_evs],
        "interval_excludes_zero": not (dlo <= 0.0 <= dhi),
        "delta_positive": dmean > 0 and not (dlo <= 0.0 <= dhi),
    }
    if "flee_ok" in real_ev:
        out["real_flee_ok"] = real_ev["flee_ok"]
        out["shuffle_flee_ok_mean"] = float(np.mean([r["flee_ok"] for r in shuf_evs]))
    return out


def run_labels_sweep(*, epochs: int = EPOCHS, lr: float = LR, seed: int = 0) -> dict:
    hanging = hanging_family()
    escapes = check_escape_family()
    teacher = teacher_family(hanging, escapes)
    families = {
        "hanging": hanging,
        "check_escape": escapes,
        "teacher": teacher,
    }
    union = []
    seen: set[str] = set()
    for rows in families.values():
        for board, target, kind in rows:
            fen = board.fen()
            if fen in seen:
                continue
            seen.add(fen)
            union.append((board, target, kind))
    real = open_session(source="fixture", shuffled=False)
    depths = []
    for mix in MIX_DEPTHS:
        real_all = _cache(real, union, mix_plies=mix)
        real_fams = {}
        shuf_fams = {name: [] for name in families}
        for name, rows in families.items():
            train_rows = family_split(rows, arm="train")
            eval_rows = family_split(rows, arm="eval")
            tr_f, tr_r = _subset_cache(union, real_all, train_rows)
            ev_f, ev_r = _subset_cache(union, real_all, eval_rows)
            lin = LinearHead.zeros(len(tr_f[0]))
            _train(lin, tr_f, tr_r, epochs=epochs, lr=lr, seed=seed)
            real_lin = _eval_family(lin, ev_f, ev_r, family=name)
            fac = FactoredHead.zeros(len(tr_f[0]))
            _train(fac, tr_f, tr_r, epochs=epochs, lr=lr, seed=seed)
            real_fac = _eval_family(fac, ev_f, ev_r, family=name)
            real_fams[name] = {
                "n_train": len(tr_r),
                "linear": real_lin,
                "factored": real_fac,
                "train_rows": train_rows,
                "eval_rows": eval_rows,
            }
        for shuf_seed in SHUFFLE_SEEDS:
            shuf = open_session(source="fixture", shuffled=True, seed=shuf_seed)
            shuf_all = _cache(shuf, union, mix_plies=mix)
            for name, rows in families.items():
                pack = real_fams[name]
                tr_f, tr_r = _subset_cache(union, shuf_all, pack["train_rows"])
                ev_f, ev_r = _subset_cache(union, shuf_all, pack["eval_rows"])
                h = LinearHead.zeros(len(tr_f[0]))
                _train(h, tr_f, tr_r, epochs=epochs, lr=lr, seed=seed)
                ev = _eval_family(h, ev_f, ev_r, family=name)
                fh = FactoredHead.zeros(len(tr_f[0]))
                _train(fh, tr_f, tr_r, epochs=epochs, lr=lr, seed=seed)
                fev = _eval_family(fh, ev_f, ev_r, family=name)
                shuf_fams[name].append({"linear": ev, "factored": fev})
        family_out = {}
        for name in families:
            family_out[name] = {
                "n_train": real_fams[name]["n_train"],
                "linear": _family_block(
                    real_fams[name]["linear"],
                    [s["linear"] for s in shuf_fams[name]],
                ),
                "factored": _family_block(
                    real_fams[name]["factored"],
                    [s["factored"] for s in shuf_fams[name]],
                ),
            }
        depths.append(
            {
                "mix_plies": mix,
                "readout": "reserved_pools" if mix == 0 else "hidden_mix",
                "synapses_used": mix > 0,
                "families": family_out,
            }
        )
    teacher0 = depths[0]["families"]["teacher"]["linear"]
    teacher0_fac = depths[0]["families"]["teacher"]["factored"]
    teacher_mix_fac = [
        d["families"]["teacher"]["factored"] for d in depths if d["mix_plies"] > 0
    ]
    collapsed = bool(
        teacher0_fac["real_acc"] > 0
        and all(
            row["real_acc"] < 0.5 * teacher0_fac["real_acc"]
            and row["shuffle_acc_mean"] < 0.5 * teacher0_fac["real_acc"]
            for row in teacher_mix_fac
        )
    )
    wiring_chess = bool(
        depths[-1]["families"]["teacher"]["linear"]["delta_positive"]
        or depths[-1]["families"]["teacher"]["factored"]["delta_positive"]
    )
    payload = {
        "experiment": "planes_labels",
        "graph": "fixture, not MaleCNS v1.0",
        "encoding": load_planes_cfg()["encoding"],
        "encoder_frozen": True,
        "linear_head": "4096-way from-to, train_step unchanged",
        "factored_head": "64 from-logits + 64 to-logits",
        "mix_depths": list(MIX_DEPTHS),
        "shuffle_seeds": list(SHUFFLE_SEEDS),
        "epochs": epochs,
        "lr": lr,
        "n_hanging": len(hanging),
        "n_check_escape": len(escapes),
        "n_teacher": len(teacher),
        "rows": depths,
        "pass_fail": {
            "teacher_linear_high_at_mix0": teacher0["real_acc"] >= 0.5,
            "teacher_factored_high_at_mix0": teacher0_fac["real_acc"] >= 0.5,
            "teacher_collapses_after_mix_both_arms": collapsed,
            "teacher_holds_at_mix3_delta_excludes_zero": wiring_chess,
            "verdict": (
                "this graph-plus-mix is not a linear chess encoder; "
                "it is a typed occupancy register plus a geometry change"
                if collapsed and not wiring_chess
                else "see family rows"
            ),
        },
        "pre_register": {
            "teacher_high_at_0": "occupancy still readable",
            "teacher_collapses_at_1_and_3_both_arms": (
                "mix erases the board facts; more FENs will not help; "
                "read out at 0 plys or stop mixing"
            ),
            "teacher_holds_at_3_delta_gt_0": (
                "wiring is carrying a small chess dictionary"
            ),
            "hanging_vs_check_escape": (
                "whether hanging dominance was the whole 0.79 occupancy read"
            ),
        },
        "caption": (
            "Labels are hanging capture, check-escape, and a deterministic "
            "teacher of those two facts. No engine."
        ),
        "games": 0,
        "elo": None,
        "gate2_quoted": False,
        "ethology_rerun": False,
        "planes_head_untouched": True,
        "hz_note": HZ_NOTE,
    }
    LOGS.mkdir(parents=True, exist_ok=True)
    TABLE_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def write_labels_sweep() -> dict:
    return run_labels_sweep()
