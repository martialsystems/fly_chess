# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import io
from contextlib import redirect_stdout

from fly_chess import BANNER
from fly_chess.cli import main


def test_empty_cli_prints_allowed_banner() -> None:
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = main([])
    assert rc == 0
    assert buf.getvalue().strip() == BANNER
