# Copyright (c) 2026 Martial Systems LLC
"""MaleCNS fixture chess: ethological dictionary and piece-plane readout."""

from __future__ import annotations

__version__ = "0.1.0"

QUESTION = (
    "Does a frozen fly-style graph take hanging pieces and flee check "
    "when the board is painted as food and looming?"
)

ALLOWED_ETHOLOGY = (
    "Approach/avoid controller, local score {score} vs random, shuffled wiring {shuffled}."
)
ALLOWED_PLANES = (
    "Piece-plane encoding plus a trained legal-move readout, Gate {gate}, shuffled control."
)
BANNER = (
    "Approach/avoid controller: paint food and loom, read named DNs, legal mask.\n"
    "Piece-plane encoding plus a trained legal-move readout. Graph frozen."
)
