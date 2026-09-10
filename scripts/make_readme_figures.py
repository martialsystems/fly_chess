# Copyright (c) 2026 Martial Systems LLC
"""Draw README figures from locked JSON. No new measurements."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO = Path(__file__).resolve().parents[1]
DOCS = REPO / "docs"
LOGS = REPO / "logs"

REAL = "#1f4e79"
SHUFFLE = "#c47b2b"
ZERO = "#444444"


def _load(name: str) -> dict:
    return json.loads((LOGS / name).read_text(encoding="utf-8"))


def _style(ax) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=9)


def fig_labels() -> None:
    """Factored hanging and teacher only. Mix 0 register; mix 1 collapse."""
    raw = _load("planes_labels.json")
    mixes = [0, 1, 3]
    hanging_real, hanging_sh, teacher_real, teacher_sh = [], [], [], []
    n_hang = n_teach = None
    for mix in mixes:
        row = next(r for r in raw["rows"] if r["mix_plies"] == mix)
        h = row["families"]["hanging"]["factored"]
        t = row["families"]["teacher"]["factored"]
        hanging_real.append(h["real_acc"])
        hanging_sh.append(h["shuffle_acc_mean"])
        teacher_real.append(t["real_acc"])
        teacher_sh.append(t["shuffle_acc_mean"])
        n_hang = h["n_eval"]
        n_teach = t["n_eval"]
    x = np.arange(len(mixes), dtype=float)
    w = 0.18
    fig, ax = plt.subplots(figsize=(6.4, 3.6), dpi=160)
    ax.bar(x - 1.5 * w, hanging_real, w, label="Hanging real", color=REAL)
    ax.bar(x - 0.5 * w, hanging_sh, w, label="Hanging shuffle", color=SHUFFLE)
    ax.bar(x + 0.5 * w, teacher_real, w, label="Teacher real", color=REAL, alpha=0.45)
    ax.bar(x + 1.5 * w, teacher_sh, w, label="Teacher shuffle", color=SHUFFLE, alpha=0.45)
    ax.set_xticks(x, ["0 (register)", "1", "3"])
    ax.set_ylabel("Factored accuracy")
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("Mix plys")
    ax.set_title("Occupancy then collapse")
    ax.legend(frameon=False, fontsize=8, ncol=2)
    _style(ax)
    fig.tight_layout()
    fig.savefig(DOCS / "fig_labels.png")
    plt.close(fig)
    _ = (n_hang, n_teach)


def fig_delta() -> None:
    raw = _load("planes_mix.json")
    xs, mean, lo, hi = [], [], [], []
    for row in raw["rows"]:
        xs.append(row["mix_plies"])
        mean.append(row["delta_acc_mean"])
        lo.append(row["delta_acc_lo"])
        hi.append(row["delta_acc_hi"])
    yerr = np.vstack([np.array(mean) - np.array(lo), np.array(hi) - np.array(mean)])
    fig, ax = plt.subplots(figsize=(6.4, 3.6), dpi=160)
    ax.axhline(0.0, color=ZERO, linewidth=1.0, linestyle="--")
    ax.errorbar(
        xs,
        mean,
        yerr=yerr,
        fmt="o",
        color=REAL,
        capsize=4,
        markersize=7,
        label="Linear head Δ (real minus shuffle)",
    )
    ax.set_xticks([0, 1, 3])
    ax.set_xlabel("Mix plys")
    ax.set_ylabel("Delta accuracy")
    ax.set_ylim(-0.08, 0.08)
    ax.set_title("Shuffle-controlled delta\nWiring does not make the labeled move linearly easier")
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    _style(ax)
    fig.tight_layout()
    fig.savefig(DOCS / "fig_delta.png")
    plt.close(fig)


def fig_cosine() -> None:
    raw = _load("planes_mix.json")
    xs, real, shuf = [], [], []
    for row in raw["rows"]:
        xs.append(row["mix_plies"])
        real.append(row["cosine_knight_vs_empty_real"])
        shuf.append(row["cosine_knight_vs_empty_shuffle_mean"])
    fig, ax = plt.subplots(figsize=(6.4, 3.6), dpi=160)
    ax.plot(xs, real, "o-", color=REAL, label="Real wiring", markersize=7)
    ax.plot(xs, shuf, "s--", color=SHUFFLE, label="Shuffle mean", markersize=7)
    ax.set_xticks([0, 1, 3])
    ax.set_xlabel("Mix plys")
    ax.set_ylabel("Knight vs empty cosine")
    ax.set_ylim(-0.05, 1.05)
    ax.set_title("Geometry contrast")
    ax.legend(frameon=False, fontsize=8)
    _style(ax)
    fig.tight_layout()
    fig.savefig(DOCS / "fig_cosine.png")
    plt.close(fig)


def fig_games() -> None:
    eth = _load("ethology_gate.json")
    planes = _load("planes_gate.json")
    labels = ["Ethology", "Planes Gate 2"]
    real = [eth["real"]["score"], planes["real"]["gate2"]["score"]]
    shuf = [eth["shuffled"]["score"], planes["shuffled"]["gate2"]["score"]]
    x = np.arange(2, dtype=float)
    w = 0.32
    fig, ax = plt.subplots(figsize=(5.2, 3.2), dpi=160)
    ax.axhline(0.5, color=ZERO, linewidth=1.0, linestyle="--", label="Chance vs random")
    ax.bar(x - w / 2, real, w, label="Real wiring", color=REAL)
    ax.bar(x + w / 2, shuf, w, label="Shuffled wiring", color=SHUFFLE)
    ax.set_xticks(x, labels)
    ax.set_ylabel("Score vs random legal")
    ax.set_ylim(0, 1.05)
    ax.set_title("Historical game locks (not restamped)")
    ax.legend(frameon=False, fontsize=8)
    _style(ax)
    fig.tight_layout()
    fig.savefig(DOCS / "fig_games.png")
    plt.close(fig)


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    fig_labels()
    fig_delta()
    fig_cosine()
    fig_games()


if __name__ == "__main__":
    main()
