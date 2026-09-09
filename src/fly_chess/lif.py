# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import json
from dataclasses import dataclass

import numpy as np

from fly_chess.graph import Graph
from fly_chess.paths import CONFIG


@dataclass
class LifConfig:
    dt_ms: float = 0.5
    tau_m_ms: float = 20.0
    v_rest_mV: float = -52.0
    v_reset_mV: float = -52.0
    v_thresh_mV: float = -45.0
    refractory_ms: float = 2.0
    steps_per_ply: int = 40
    gain: float = 1.0
    baseline_current_mV: float = 0.4

    @classmethod
    def load(cls) -> "LifConfig":
        raw = json.loads((CONFIG / "lif.json").read_text(encoding="utf-8"))
        return cls(**{k: raw[k] for k in cls.__dataclass_fields__ if k in raw})


class LifNet:
    def __init__(self, graph: Graph, cfg: LifConfig | None = None) -> None:
        self.graph = graph
        self.cfg = cfg or LifConfig.load()
        self.n = graph.n
        self.v = np.full(self.n, self.cfg.v_rest_mV, dtype=np.float64)
        self.ref = np.zeros(self.n, dtype=np.int32)
        self.i_ext = np.zeros(self.n, dtype=np.float64)
        self.spike_count = np.zeros(self.n, dtype=np.int32)
        self.last_spikes = np.zeros(self.n, dtype=np.float64)
        self._ref_steps = max(1, int(round(self.cfg.refractory_ms / self.cfg.dt_ms)))

    def reset(self) -> None:
        self.v[:] = self.cfg.v_rest_mV
        self.ref[:] = 0
        self.i_ext[:] = 0.0
        self.spike_count[:] = 0
        self.last_spikes[:] = 0.0

    def step(self) -> np.ndarray:
        cfg = self.cfg
        psp = np.zeros(self.n, dtype=np.float64)
        if self.graph.pre.size:
            contrib = self.graph.weight * self.last_spikes[self.graph.pre] * cfg.gain
            np.add.at(psp, self.graph.post, contrib)
        dv = (
            -(self.v - cfg.v_rest_mV)
            + self.i_ext
            + cfg.baseline_current_mV
        ) * (cfg.dt_ms / cfg.tau_m_ms)
        active = self.ref == 0
        self.v[active] += dv[active] + psp[active]
        spiked = (self.v >= cfg.v_thresh_mV) & active
        self.v[spiked] = cfg.v_reset_mV
        self.ref[spiked] = self._ref_steps
        cooling = self.ref > 0
        self.ref[cooling] -= 1
        self.spike_count += spiked.astype(np.int32)
        self.last_spikes = spiked.astype(np.float64)
        return spiked

    def run_ply(self, i_ext: np.ndarray) -> np.ndarray:
        self.i_ext = np.asarray(i_ext, dtype=np.float64)
        self.spike_count[:] = 0
        for _ in range(self.cfg.steps_per_ply):
            self.step()
        duration_s = self.cfg.steps_per_ply * self.cfg.dt_ms / 1000.0
        return self.spike_count.astype(np.float64) / max(duration_s, 1e-9)
