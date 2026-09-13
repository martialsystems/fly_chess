# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import json
from pathlib import Path

import pytest

from fly_chess.cli import main
from fly_chess.dense_catalog import load_value_cfg
from fly_chess.train_value import SHUFFLE_SEEDS, run_value

REPO = Path(__file__).resolve().parents[1]


def test_value_config_keeps_shuffle_and_freezes_graph() -> None:
    cfg = load_value_cfg()
    assert cfg["shuffle_seeds"] == [1, 2, 3, 4, 5]
    assert tuple(SHUFFLE_SEEDS) == (1, 2, 3, 4, 5)
    assert cfg["mix0_plies"] == 0
    assert cfg["mix1_plies"] == 1
    assert cfg["graph_frozen"] is True
    assert cfg["synapses_trainable"] is False
    assert cfg["player"] == "mix0_child_ranker"
    assert cfg["catalog"]["n_games"] >= 10
    assert cfg["player"] == "mix0_child_ranker"
    note = cfg["note"].lower()
    assert "self-play" in note or "occupancy" in note
    assert "hanging/teacher policy stays closed" in note


def test_value_sources_do_not_revive_policy_heads() -> None:
    src = (REPO / "src" / "fly_chess" / "train_value.py").read_text(encoding="utf-8")
    assert "labeled_positions" not in src
    assert "LinearHead" not in src
    assert "FactoredHead" not in src
    assert "train_planes" not in src
    assert "dopamine" not in src.lower()
    child = (REPO / "src" / "fly_chess" / "child_value.py").read_text(encoding="utf-8")
    assert "legal_moves" in child
    assert "4096" not in child


def test_value_cli_refuses_malecns() -> None:
    with pytest.raises(SystemExit) as err:
        main(["value", "--stage", "A", "--tiny", "--source", "malecns"])
    assert "fixture" in str(err.value).lower() or "identity" in str(err.value).lower()


def test_tiny_mix0_run_is_legal_and_does_not_claim_wiring() -> None:
    payload = run_value(stage="A", tiny=True, n_play=2)
    assert payload["A"]["synapses_used"] is False
    assert payload["A"]["mix_plies"] == 0
    assert payload["A"]["games"]["illegal"] == 0
    assert payload["A"]["games"]["elo"] is None
    assert payload["catalog"]["holdout"] == "game_id"
    assert payload["catalog"]["not_hanging_catalog"] is True
    assert payload["graph_frozen"] is True
    assert "B_real" not in payload
    eth = json.loads((REPO / "logs" / "ethology_gate.json").read_text(encoding="utf-8"))
    assert eth["real"]["score"] == 0.4875
    assert eth["n_games"] == 40


def test_tiny_table_does_not_unfreeze() -> None:
    payload = run_value(stage="all", tiny=True, n_play=0)
    assert payload["A"]["held_out"]["n_positions"] >= 1
    assert payload["B_real"]["synapses_used"] is True
    assert payload["B_shuffle"]["shuffle_seeds"] == [1, 2, 3, 4, 5]
    assert payload["C"]["head"] == "mlp_two_layer"
    assert payload["C"]["mlp_hidden"] == 32
    assert payload["unfreeze_allowed"] is False
    assert payload["wiring_helped"] is False
    assert payload["elo"] is None
    with pytest.raises(SystemExit) as err:
        main(["value", "--stage", "A", "--tiny", "--n", "0"])
    assert "closed" in str(err.value).lower()
