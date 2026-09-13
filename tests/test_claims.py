# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import io
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from fly_chess import BANNER
from fly_chess.claims import ClaimBanError, require_clean, scan_text
from fly_chess.cli import main

REPO = Path(__file__).resolve().parents[1]


def test_banner_is_clean() -> None:
    assert scan_text(BANNER) == []
    require_clean(BANNER, source="banner")


PLAIN_HOOK = (
    "Mix-0 occupancy plus search plays. "
    "One LIF ply on the real graph is silent. "
    "Shuffle does not save it. "
    "wiring_helped is false."
)


def test_readme_and_cli_help_are_clean() -> None:
    require_clean((REPO / "README.md").read_text(encoding="utf-8"), source="README.md")
    buf = io.StringIO()
    with redirect_stdout(buf):
        with pytest.raises(SystemExit):
            main(["--help"])
    require_clean(buf.getvalue(), source="cli-help")
    require_clean((REPO / "AGENTS.md").read_text(encoding="utf-8"), source="AGENTS.md")
    for path in (REPO / "docs").glob("*.md"):
        require_clean(path.read_text(encoding="utf-8"), source=str(path.relative_to(REPO)))
    desc = (REPO / "description.txt").read_text(encoding="utf-8").strip()
    assert desc == PLAIN_HOOK
    require_clean(desc, source="description.txt")


def test_banned_tokens_fail() -> None:
    with pytest.raises(ClaimBanError):
        require_clean("the engine learned chess today", source="x")
    with pytest.raises(ClaimBanError):
        require_clean("it plays on chess.com", source="x")


def test_cli_refuses_lichess() -> None:
    with pytest.raises(SystemExit):
        main(["play", "--exp", "ethology", "--lichess"])


def test_cli_refuses_malecns_gate2() -> None:
    with pytest.raises(SystemExit) as err:
        main(["play", "--exp", "planes", "--gate", "2", "--source", "malecns"])
    assert "identity" in str(err.value).lower() or "Gate 2" in str(err.value)
