# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

from pathlib import Path

PKG = Path(__file__).resolve().parent
SRC = PKG.parent
REPO = SRC.parent
CONFIG = REPO / "config"
DATA = REPO / "data"
FIXTURE = DATA / "fixtures" / "graph.json"
PROVENANCE = REPO / "data-provenance"
LOGS = REPO / "logs"
ALIASES = CONFIG / "type_aliases.json"
RESOLVED = DATA / "resolved_types.json"
ETHOLOGY_MAP = DATA / "ethology_map.json"
PLANES_MAP = DATA / "planes_map.json"
