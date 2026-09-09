#!/usr/bin/env python3
# Copyright (c) 2026 Martial Systems LLC
"""Download MaleCNS v1.0 into data/malecns. Hash-locked. Not a pytest path."""

from __future__ import annotations

from fly_chess.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["fetch"]))
