# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import json
from pathlib import Path

from fly_chess.claims import require_clean
from fly_chess.paths import LOGS, PROVENANCE

REPO = Path(__file__).resolve().parents[1]


def test_ethology_gate_has_real_and_shuffled_rows() -> None:
    eth = json.loads((LOGS / "ethology_gate.json").read_text(encoding="utf-8"))
    lock = json.loads((PROVENANCE / "fixture.lock.json").read_text(encoding="utf-8"))
    require_clean(eth["claim"], source="ethology_gate.json")
    assert eth["n_games"] == 40
    assert eth["real"]["n_games"] == 40
    assert eth["shuffled"]["n_games"] == 40
    assert eth["real"]["illegal"] == 0
    assert eth["shuffled"]["illegal"] == 0
    assert eth["fixture_sha256"] == lock["sha256"]
    assert "hanging_capture_real_gt_shuffled" in eth["load_bearing"]
    assert "check_escape_real_ge_shuffled" in eth["load_bearing"]


def test_planes_gate_has_shuffle_and_fails_gate2() -> None:
    planes = json.loads((LOGS / "planes_gate.json").read_text(encoding="utf-8"))
    require_clean(planes["claim"], source="planes_gate.json")
    assert planes["n_games"] == 40
    assert planes["gate0"]["illegal"] == 0
    assert planes["gate2_real"]["n_games"] == 40
    assert planes["gate2_shuffled"]["n_games"] == 40
    assert planes["gate2_passed"] is False
    assert "gate2_score_real_gt_shuffled" in planes["load_bearing"]
