# Copyright (c) 2026 Martial Systems LLC
"""Current-based PSP unit suite. Does not touch fixture game locks."""

from __future__ import annotations

import numpy as np

from fly_chess.graph import Graph, Neuron
from fly_chess.lif import LifConfig, LifNet
from fly_chess.match import identity_stim
from fly_chess.session import open_session


def _pair(*, weight: float, sign: int = 1) -> Graph:
    return Graph(
        neurons=[
            Neuron(id=0, type="PRE", sign=sign),
            Neuron(id=1, type="POST", sign=1),
        ],
        pre=[0],
        post=[1],
        weight=[weight],
    )


def _current_cfg(**overrides) -> LifConfig:
    cfg = LifConfig.for_mode("malecns_current")
    cfg.baseline_current_mV = 0.0
    cfg.gain = 1.0
    cfg.steps_per_ply = 80
    for key, value in overrides.items():
        setattr(cfg, key, value)
    return cfg


def test_modes_are_named_and_source_gated() -> None:
    fix = LifConfig.for_source("fixture")
    fly = LifConfig.for_source("malecns")
    default = LifConfig.load()
    assert fix.mode == "fixture_voltage_jump"
    assert fix.psp == "voltage_jump"
    assert fly.mode == "malecns_current"
    assert fly.psp == "current"
    assert default.psp == "voltage_jump"
    assert default.mode == fix.mode


def test_one_contact_rises_then_decays_toward_rest() -> None:
    cfg = _current_cfg(mV_per_contact=2.0)
    net = LifNet(_pair(weight=1.0), cfg)
    net.last_spikes[0] = 1.0
    rest = cfg.v_rest_mV
    net.step()
    expected = rest + cfg.mV_per_contact * (cfg.dt_ms / cfg.tau_m_ms)
    assert abs(net.v[1] - expected) < 1e-9
    peak = float(net.v[1])
    for _ in range(40):
        net.step()
    assert net.v[1] < peak
    assert net.v[1] > rest
    assert abs(net.v[1] - rest) < abs(peak - rest)


def test_two_contacts_twice_the_charge() -> None:
    cfg = _current_cfg(mV_per_contact=2.0)
    one = LifNet(_pair(weight=1.0), cfg)
    two = LifNet(_pair(weight=2.0), cfg)
    one.last_spikes[0] = 1.0
    two.last_spikes[0] = 1.0
    one.step()
    two.step()
    d1 = one.v[1] - cfg.v_rest_mV
    d2 = two.v[1] - cfg.v_rest_mV
    assert abs(d2 - 2.0 * d1) < 1e-9


def test_inhibitory_sign_flips_the_direction() -> None:
    cfg = _current_cfg(mV_per_contact=2.0)
    exc = LifNet(_pair(weight=1.0), cfg)
    inh = LifNet(_pair(weight=-1.0, sign=-1), cfg)
    exc.last_spikes[0] = 1.0
    inh.last_spikes[0] = 1.0
    exc.step()
    inh.step()
    up = exc.v[1] - cfg.v_rest_mV
    down = inh.v[1] - cfg.v_rest_mV
    assert up > 0
    assert down < 0
    assert abs(up + down) < 1e-9


def test_voltage_jump_is_still_instant() -> None:
    cfg = LifConfig.for_mode("fixture_voltage_jump")
    cfg.baseline_current_mV = 0.0
    net = LifNet(_pair(weight=3.0), cfg)
    net.last_spikes[0] = 1.0
    net.step()
    # Instant millivolt jump plus leak of 0 at rest.
    assert abs(net.v[1] - (cfg.v_rest_mV + 3.0)) < 1e-9


def test_fixture_identity_still_sugar_mn9_and_shuffle_fails() -> None:
    real = open_session(source="fixture", shuffled=False)
    shuf = open_session(source="fixture", shuffled=True, seed=1)
    assert real.net.cfg.psp == "voltage_jump"
    rest = identity_stim(real, "sugar_grn", current=0.0)
    on = identity_stim(real, "sugar_grn", current=18.0)
    assert on["feed_mn"] > rest["feed_mn"]
    assert on["feed_mn"] > 1.0
    shuf_on = identity_stim(shuf, "sugar_grn", current=18.0)
    shuf_rest = identity_stim(shuf, "sugar_grn", current=0.0)
    # Toy shuffle drops the sugar→MN9 path.
    assert shuf_on["feed_mn"] <= shuf_rest["feed_mn"] + 1.0
