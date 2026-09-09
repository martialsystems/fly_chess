# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import json

from fly_chess.claims import require_clean
from fly_chess.paths import LOGS, PROVENANCE
from fly_chess.schema import ARM_KEYS, LOAD_BEARING_KEYS, TOP_KEYS


def test_lock_files_share_schema() -> None:
    eth = json.loads((LOGS / "ethology_gate.json").read_text(encoding="utf-8"))
    planes = json.loads((LOGS / "planes_gate.json").read_text(encoding="utf-8"))
    lock = json.loads((PROVENANCE / "fixture.lock.json").read_text(encoding="utf-8"))
    require_clean(eth["claim"], source="ethology_gate.json")
    require_clean(planes["claim"], source="planes_gate.json")
    assert tuple(eth.keys()) == TOP_KEYS
    assert tuple(planes.keys()) == TOP_KEYS
    assert tuple(eth["real"].keys()) == ARM_KEYS
    assert tuple(eth["shuffled"].keys()) == ARM_KEYS
    assert tuple(planes["real"].keys()) == ARM_KEYS
    assert tuple(planes["shuffled"].keys()) == ARM_KEYS
    assert tuple(eth["load_bearing"].keys()) == LOAD_BEARING_KEYS
    assert tuple(planes["load_bearing"].keys()) == LOAD_BEARING_KEYS
    assert eth["n_games"] == 40
    assert planes["n_games"] == 40
    assert eth["real"]["hanging_chances"] == 774
    assert eth["shuffled"]["hanging_chances"] == 668
    assert eth["real"]["check_chances"] == 41
    assert eth["shuffled"]["check_chances"] == 31
    assert eth["load_bearing"]["check_escape_same_n"] is False
    assert eth["load_bearing"]["hanging_capture_same_n"] is False
    assert eth["load_bearing"]["hanging_capture_real_gt_shuffled"] is True
    assert eth["load_bearing"]["wiring_is_encoder"] is False
    assert planes["load_bearing"]["wiring_is_encoder"] is False
    assert planes["load_bearing"]["gate2_score_real_gt_shuffled"] is False
    assert planes["gate2_passed"] is False
    assert eth["fixture_sha256"] == lock["sha256"]
    assert planes["fixture_sha256"] == lock["sha256"]
    assert "0.4875" in eth["claim"]
    assert eth["real"]["score"] == 0.4875
    assert eth["shuffled"]["score"] == 0.4875
