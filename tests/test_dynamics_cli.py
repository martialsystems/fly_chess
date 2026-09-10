# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import json

import pytest

from fly_chess.cli import main
from fly_chess.fetch import malecns_present
from fly_chess.paths import LOGS


def test_dynamics_commands_skip_without_download() -> None:
    if malecns_present():
        pytest.skip("MaleCNS files present on this machine")
    for cmd in ("gain-sweep", "neighborhood", "hop-probe", "signs"):
        with pytest.raises(FileNotFoundError):
            main([cmd])


def test_gain_sweep_lock_is_not_a_player() -> None:
    path = LOGS / "malecns_gain_sweep.json"
    if not path.is_file():
        pytest.skip("gain sweep lock not written")
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["games"] == 0
    assert raw["elo"] is None
    assert raw["gate2_quoted"] is False
    assert raw["default_circuit_graph"] == "475_identity_slice"
    assert "not a biological firing rate" in raw["note"]
    assert "not a firing-rate discovery" in raw["hz_note"]
    assert raw["picked_mV_per_contact"] == 8.0
    assert raw["split_held"] is True


def test_hop_probe_aborted_and_is_not_the_circuit_graph() -> None:
    path = LOGS / "malecns_hop_probe.json"
    if not path.is_file():
        pytest.skip("hop probe lock not written")
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["aborted"] is True
    assert raw["used_as_circuit_graph"] is False
    assert raw["default_circuit_graph"] == "475_identity_slice"
    assert raw["games"] == 0
    assert raw["gate2_quoted"] is False
    assert raw["n_neurons"] == 917
    assert any("budgeted probe" in n for n in raw.get("readout_notes", []))


def test_signs_do_not_flip_unclear() -> None:
    path = LOGS / "malecns_signs.json"
    if not path.is_file():
        pytest.skip("signs lock not written")
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["fallback_sign"] == 1
    assert "not flipped" in raw["unclear_and_monoamine"]
    assert raw["games"] == 0
    assert raw["n_neurons"] == 475
    assert any("475-cell mix" in n for n in raw.get("readout_notes", []))
