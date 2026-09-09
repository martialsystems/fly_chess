# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import numpy as np

def mean_hz(hz: np.ndarray, ids: list[int]) -> float:
    if not ids:
        return 0.0
    return float(np.mean(hz[np.array(ids, dtype=np.int32)]))
