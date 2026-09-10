# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from fly_chess.connectome import write_fixture
from fly_chess.paths import FIXTURE, PROVENANCE


def test_checked_in_fixture_matches_lock() -> None:
    write_fixture()
    digest = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
    lock = json.loads((PROVENANCE / "fixture.lock.json").read_text(encoding="utf-8"))
    assert digest == lock["sha256"]
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert len(raw["neurons"]) == lock["neurons"] == 1007
    assert len(raw["edges"]) == lock["edges"] == 5103
