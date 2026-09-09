# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import json

from fly_chess.paths import LOGS
from fly_chess.schema import MALECNS_LOCK_KEYS


def test_malecns_locks_share_required_keys() -> None:
    for name in ("malecns_identity.json", "malecns_circuit.json"):
        raw = json.loads((LOGS / name).read_text(encoding="utf-8"))
        for key in MALECNS_LOCK_KEYS:
            assert key in raw, f"{name} missing {key}"
        assert raw["games"] == 0
        assert raw["elo"] is None
        assert raw["gate2_quoted"] is False
        assert "not a firing-rate discovery" in raw["hz_note"]


def test_fixture_locks_still_reject_hanging_same_n() -> None:
    eth = json.loads((LOGS / "ethology_gate.json").read_text(encoding="utf-8"))
    assert eth["load_bearing"]["hanging_capture_same_n"] is False
    assert eth["load_bearing"]["check_escape_same_n"] is False
    assert eth["load_bearing"]["wiring_is_encoder"] is False
