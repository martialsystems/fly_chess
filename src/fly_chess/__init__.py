# Copyright (c) 2026 Martial Systems LLC
"""MaleCNS fixture chess: ethological dictionary and piece-plane readout."""

from __future__ import annotations

__version__ = "0.1.0"

QUESTION = (
    "Can you point a fruit-fly wiring diagram at a chessboard and get legal moves out?"
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
