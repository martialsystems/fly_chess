# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import json
from pathlib import Path

from fly_chess.puzzles import load_split, split_positions

REPO = Path(__file__).resolve().parents[1]


def test_split_meets_mix_protocol() -> None:
    split = load_split()
    assert len(split["train"]) >= 80
    assert len(split["eval"]) >= 40
    assert set(split["train"]).isdisjoint(split["eval"])
    assert len(split_positions(arm="train")) == len(split["train"])
    assert len(split_positions(arm="eval")) == len(split["eval"])


def test_mix_lock_is_not_gate2() -> None:
    path = REPO / "logs" / "planes_mix.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["games"] == 0
    assert raw["elo"] is None
    assert raw["gate2_quoted"] is False
    assert raw["ethology_rerun"] is False
    assert raw["n_train"] >= 80
    assert raw["n_eval"] >= 40
    assert raw["shuffle_seeds"] == [1, 2, 3, 4, 5]
    depths = [row["mix_plies"] for row in raw["rows"]]
    assert depths == [0, 1, 3]
    assert raw["rows"][0]["synapses_used"] is False
    assert raw["rows"][1]["synapses_used"] is True
    assert "Wiring changes the hidden geometry" in raw["caption"]
    eth = json.loads((REPO / "logs" / "ethology_gate.json").read_text(encoding="utf-8"))
    assert eth["real"]["score"] == 0.4875
    assert eth["shuffled"]["score"] == 0.4875
    assert eth["n_games"] == 40
    planes = json.loads((REPO / "logs" / "planes_gate.json").read_text(encoding="utf-8"))
    assert planes["n_games"] == 40
    pointer = json.loads((REPO / "logs" / "planes_head.json").read_text(encoding="utf-8"))
    assert pointer["n_eval"] == 10
    assert pointer["real_mean_target_rank"] == 3.9
