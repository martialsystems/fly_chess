# Copyright (c) 2026 Martial Systems LLC
"""Draw README figures from locked JSON. No new measurements."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["axes.unicode_minus"] = False

REPO = Path(__file__).resolve().parents[1]
DOCS = REPO / "docs"
LOGS = REPO / "logs"

REAL = "#1f4e79"
SHUFFLE = "#c47b2b"
OCC = "#2e7d32"
ZERO = "#444444"


def _load(name: str) -> dict:
    return json.loads((LOGS / name).read_text(encoding="utf-8"))


def _style(ax) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=9)


def _acc_label(value: float) -> str:
    return f"{value:.3f}"


def _score_label(value: float) -> str:
    if abs(value - 0.5) < 1e-12:
        return "0.50"
    return f"{value:.4f}"


def _label_bars(ax, bars, values, fmt, dy: float) -> None:
    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            bar.get_height() + dy,
            fmt(val),
            ha="center",
            va="bottom",
            fontsize=8,
        )


def fig_labels() -> None:
    """Factored hanging and teacher. Mix 0 register vs mix 1 collapse. No mix 3."""
    raw = _load("planes_labels.json")
    row0 = next(r for r in raw["rows"] if r["mix_plies"] == 0)
    row1 = next(r for r in raw["rows"] if r["mix_plies"] == 1)
    hang0 = row0["families"]["hanging"]["factored"]
    teach0 = row0["families"]["teacher"]["factored"]
    hang1 = row1["families"]["hanging"]["factored"]
    teach1 = row1["families"]["teacher"]["factored"]
    if abs(hang0["real_acc"] - hang0["shuffle_acc_mean"]) > 1e-12:
        raise SystemExit("mix 0 hanging real != shuffle; occupancy bar would hide an arm")
    if abs(teach0["real_acc"] - teach0["shuffle_acc_mean"]) > 1e-12:
        raise SystemExit("mix 0 teacher real != shuffle; occupancy bar would hide an arm")
    n_hang = hang0["n_eval"]
    n_teach = teach0["n_eval"]
    x = np.arange(2, dtype=float)
    w = 0.24
    occ = [hang0["real_acc"], teach0["real_acc"]]
    m1_real = [hang1["real_acc"], teach1["real_acc"]]
    m1_sh = [hang1["shuffle_acc_mean"], teach1["shuffle_acc_mean"]]
    fig, ax = plt.subplots(figsize=(6.8, 3.8), dpi=160)
    b0 = ax.bar(x - w, occ, w, label="Mix 0 (occupancy)", color=OCC)
    b1 = ax.bar(x, m1_real, w, label="Mix 1 real", color=REAL)
    b2 = ax.bar(x + w, m1_sh, w, label="Mix 1 shuffle", color=SHUFFLE)
    _label_bars(ax, b0, occ, _acc_label, 0.02)
    _label_bars(ax, b1, m1_real, _acc_label, 0.02)
    _label_bars(ax, b2, m1_sh, _acc_label, 0.02)
    ax.set_xticks(x, [f"Hanging\n(n={n_hang})", f"Teacher\n(n={n_teach})"])
    ax.set_ylabel("Held-out accuracy (factored head)")
    ax.set_ylim(0, 1.05)
    ax.set_title("Occupancy is readable; one mix ply deletes the labels")
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    _style(ax)
    fig.tight_layout()
    fig.savefig(DOCS / "fig_labels.png")
    plt.close(fig)


def fig_delta() -> None:
    raw = _load("planes_mix.json")
    xs, mean, lo, hi = [], [], [], []
    for row in raw["rows"]:
        xs.append(row["mix_plies"])
        mean.append(row["delta_acc_mean"])
        lo.append(row["delta_acc_lo"])
        hi.append(row["delta_acc_hi"])
    yerr = np.vstack([np.array(mean) - np.array(lo), np.array(hi) - np.array(mean)])
    fig, ax = plt.subplots(figsize=(6.8, 3.8), dpi=160)
    ax.axhline(0.0, color="#888888", linewidth=1.0)
    ax.errorbar(
        xs,
        mean,
        yerr=yerr,
        fmt="o-",
        color=REAL,
        capsize=5,
        markersize=8,
        linewidth=1.6,
        ecolor=REAL,
    )
    ax.set_xticks([0, 1, 3])
    ax.set_xlabel("Mix plys")
    ax.set_ylabel("Delta acc (real minus shuffle mean)")
    ax.set_ylim(-0.04, 0.04)
    ax.set_title("Wiring does not make the labeled move linearly easier")
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
    n = eth["n_games"]
    if planes["n_games"] != n or planes["real"]["gate2"]["n_games"] != n:
        raise SystemExit("ethology and Gate 2 n_games disagree")
    labels = [f"Ethology\n(n={n})", f"Planes Gate 2\n(n={n})"]
    real = [eth["real"]["score"], planes["real"]["gate2"]["score"]]
    shuf = [eth["shuffled"]["score"], planes["shuffled"]["gate2"]["score"]]
    x = np.arange(2, dtype=float)
    w = 0.32
    fig, ax = plt.subplots(figsize=(5.6, 3.4), dpi=160)
    ax.axhline(0.5, color=ZERO, linewidth=1.0, linestyle="--", label="Chance vs random")
    bars_real = ax.bar(x - w / 2, real, w, label="Real wiring", color=REAL)
    bars_shuf = ax.bar(x + w / 2, shuf, w, label="Shuffled wiring", color=SHUFFLE)
    _label_bars(ax, bars_real, real, _score_label, 0.06)
    _label_bars(ax, bars_shuf, shuf, _score_label, 0.06)
    ax.set_xticks(x, labels)
    ax.set_ylabel("Score vs random legal")
    ax.set_ylim(0, 1.05)
    ax.set_title(f"Historical game locks (n={n}, not restamped)")
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
