#!/usr/bin/env python3
# Copyright (c) 2026 Martial Systems LLC
"""Shuffled-wiring smoke. Same as `python -m fly_chess shuffle --exp ethology --n 4`."""

from __future__ import annotations

from fly_chess.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["shuffle", "--exp", "ethology", "--n", "4"]))
