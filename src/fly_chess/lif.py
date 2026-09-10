# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields

import numpy as np

from fly_chess.graph import Graph
from fly_chess.paths import CONFIG

HZ_NOTE = (
    "Named-cell Hz is the injected paint pulse on an intact path, "
    "not a firing-rate discovery. Contrast is shuffle crosstalk."
)
MN9_MEAN_NOTE = (
    "12.5 Hz and 37.5 Hz are injected-pulse responses on an intact path, "
    "and MN9 is a two-cell mean."
)
GAIN_PICK_NOTE = (
    "8.0 current-units is a grid pick because 4.0 was silent, "
    "not a fly biophysics constant."
)
SIGNS_MIX_NOTE = (
    "Required-role signs all +1 is the 475-cell mix, "
    "not a whole-brain transmitter table."
)
HOP_BUDGET_NOTE = (
    "Hop 1 already hits the 8,000 cap, so 917 cells is a budgeted probe, "
    "not the true 2-hop map."
)
READOUT_NOTES = (MN9_MEAN_NOTE, GAIN_PICK_NOTE, SIGNS_MIX_NOTE, HOP_BUDGET_NOTE)
NEAR_REST_HZ = 1.0


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
    psp: str = "voltage_jump"
    mV_per_contact: float = 1.0
    saturate_hz: float = 150.0
    mode: str = "fixture_voltage_jump"

    @staticmethod
    def raw() -> dict:
        return json.loads((CONFIG / "lif.json").read_text(encoding="utf-8"))

    @classmethod
    def for_mode(cls, mode: str, raw: dict | None = None) -> "LifConfig":
        raw = raw if raw is not None else cls.raw()
        allowed = {f.name for f in fields(cls)}
        shared = {k: raw[k] for k in allowed if k in raw}
        modes = raw.get("modes") or {}
        if mode not in modes:
            raise ValueError(f"unknown LIF mode {mode!r}")
        shared.update({k: v for k, v in modes[mode].items() if k in allowed})
        shared["mode"] = mode
        cfg = cls(**shared)
        if cfg.psp not in ("voltage_jump", "current"):
            raise ValueError(f"unknown psp {cfg.psp!r}")
        return cfg

    @classmethod
    def for_source(cls, source: str) -> "LifConfig":
        raw = cls.raw()
        mapped = (raw.get("source_mode") or {}).get(source)
        mode = mapped or raw.get("default_mode") or "fixture_voltage_jump"
        return cls.for_mode(mode, raw)

    @classmethod
    def load(cls) -> "LifConfig":
        """Fixture default. MaleCNS must call for_source('malecns')."""
        return cls.for_source("fixture")

    def payload(self) -> dict:
        row = asdict(self)
        row["hz_note"] = HZ_NOTE
        return row


def near_rest(hz: float, rest: float) -> bool:
    return float(hz) <= float(rest) + NEAR_REST_HZ


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
        syn = np.zeros(self.n, dtype=np.float64)
        if self.graph.pre.size:
            scale = cfg.gain
            if cfg.psp == "current":
                scale *= cfg.mV_per_contact
            contrib = self.graph.weight * self.last_spikes[self.graph.pre] * scale
            np.add.at(syn, self.graph.post, contrib)
        drive = -(self.v - cfg.v_rest_mV) + self.i_ext + cfg.baseline_current_mV
        if cfg.psp == "current":
            drive = drive + syn
        dv = drive * (cfg.dt_ms / cfg.tau_m_ms)
        active = self.ref == 0
        if cfg.psp == "voltage_jump":
            self.v[active] += dv[active] + syn[active]
        else:
            self.v[active] += dv[active]
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
