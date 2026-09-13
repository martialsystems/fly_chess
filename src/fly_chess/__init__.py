# Copyright (c) 2026 Martial Systems LLC
"""MaleCNS fixture chess: ethological dictionary and piece-plane readout."""

from __future__ import annotations

__version__ = "0.1.0"

QUESTION = (
    "If that graph is run as a leaky integrate-and-fire network, "
    "with a chessboard written into a few sensory channels and a legal-move mask "
    "on the way out, what can be measured."
)

ALLOWED_ETHOLOGY = (
    "Approach/avoid controller, local score {score} vs random, shuffled wiring {shuffled}."
)
ALLOWED_PLANES = (
    "Piece-plane encoding plus a trained legal-move readout, Gate {gate}, shuffled control."
)
ALLOWED_VALUE = (
    "Mix-0 occupancy plus search plays. wiring_helped is false. Chess-on-wiring closed."
)
BANNER = (
    "Approach/avoid controller: paint food and loom, read named DNs, legal mask.\n"
    "Piece-plane encoding plus a trained legal-move readout. Graph frozen.\n"
    "Mix-0 occupancy plus search plays. wiring_helped is false. Chess-on-wiring closed."
)
