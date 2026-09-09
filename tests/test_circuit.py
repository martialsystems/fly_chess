# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import json

import pytest

from fly_chess.circuit import run_circuit
from fly_chess.cli import main
from fly_chess.fetch import malecns_present


def test_fixture_circuit_separates_mn9_and_dnp01() -> None:
    payload = run_circuit(source="fixture")
    assert payload["games"] == 0
    assert payload["elo"] is None
    assert payload["gate2_quoted"] is False
    assert "not a firing-rate discovery" in payload.get("hz_note", "")
    assert payload["paint"]["loci"] is False
    assert payload["passed"]["mn9_vs_dnp01_separate"] is True
    assert payload["kernel"]["psp"] == "voltage_jump"
    assert payload["kernel"]["mode"] == "fixture_voltage_jump"
    sugar = payload["real"]["sugar"]
    loom = payload["real"]["loom"]
    assert sugar["feed_mn"] > payload["real"]["rest"]["feed_mn"]
    assert sugar["gf_escape"] == 0.0
    assert loom["gf_escape"] > payload["real"]["rest"]["gf_escape"]
    assert loom["feed_mn"] == 0.0


def test_malecns_circuit_skips_without_download() -> None:
    if malecns_present():
        pytest.skip("MaleCNS files present on this machine")
    with pytest.raises(FileNotFoundError):
        run_circuit(source="malecns")


def test_play_malecns_still_refused() -> None:
    with pytest.raises(SystemExit) as err:
        main(["play", "--exp", "ethology", "--source", "malecns"])
    msg = str(err.value).lower()
    assert "gate 2" in msg or "identity/circuit" in msg or "no play" in msg
