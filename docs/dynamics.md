# Dynamics: current-based kernel on the 475-cell slice

This is a kernel note. It is not a chess gate and not a MaleCNS Elo. That work is dynamics. It is not Gate 2.

Named-cell Hz is the injected pulse on an intact path, not a firing-rate discovery. The useful contrast is shuffle crosstalk.

## Config

`config/lif.json` has two named modes. Source selects the mode. The global default stays `fixture_voltage_jump`.

| Mode | PSP | Who uses it |
|------|-----|-------------|
| `fixture_voltage_jump` | instant millivolt jump equal to `weight` | 290-cell pytest and fixture games |
| `malecns_current` | current `mV_per_contact` per synaptic contact, then leak through `tau_m` | MaleCNS identity and circuit only |

Shared membrane: `dt_ms` 0.5, `tau_m_ms` 20.0, `v_rest_mV` -52, `v_thresh_mV` -45, `refractory_ms` 2.0.

`malecns_current` after the gain sweep (`logs/malecns_gain_sweep.json`): `mV_per_contact` 8.0, `steps_per_ply` 80 (40 ms). One spike delivers `8.0 * dt / tau_m` = 0.20 mV per contact, then leak. 8.0 current-units is a grid pick because 4.0 was silent, not a fly biophysics constant. Those Hz values are the injected pulse on the path, not a biological firing rate.

## Why voltage_jump seizes

MaleCNS `weight` is a synapse count. LPLC2 → DNp01 is 185 edges and 4,862 contacts. One DNp01 cell takes about 2,220 of those. `voltage_jump` adds that count as millivolts in one step. A 2-hop neighborhood of the identity seeds was 155,728 cells; rest 0, stim about 250 to 300 Hz on real and shuffle. Discarded. Not a lock file.

## 475-cell current-based result

Locked identity graph: sugar GRNs (247) + MN9 (2) + LPLC2 (185) + DNp01 (2) + 39 sugar→MN9 bridges = 475 cells. Direct sugar → MN9: 0 edges. Direct LPLC2 → DNp01: 185 edges.

`logs/malecns_identity.json` and `logs/malecns_circuit.json` (writer restamp, kernel `malecns_current`, 8.0 mV/contact):

- Real sugar: MN9 up, DNp01 at rest
- Real loom: DNp01 up, MN9 at rest
- Degree-and-sign shuffle: crosstalk
- games 0, elo null, gate2_quoted false

Identity pulse 18: named sensory cells 75 Hz, MN9 12.5 Hz on sugar, DNp01 75 Hz on loom. Circuit pulse 26: sensory 125 Hz, MN9 37.5 Hz on sugar, DNp01 125 Hz on loom. 12.5 Hz and 37.5 Hz are injected-pulse responses on an intact path, and MN9 is a two-cell mean.

## 2-hop LPLC2 probe (aborted)

Default circuit graph stays 475. A capped outgoing 2-hop from LPLC2 (`n_cap` 2000) built 917 retained cells, 59,606 edges, `saturate_frac` 0.425, `max_hz` 425. Hop 1 already hits the 8,000 cap, so 917 cells is a budgeted probe, not the true 2-hop map. Aborted. `logs/malecns_hop_probe.json`. That graph is not the circuit graph and not a player.

Do not expand the graph while a capped loom neighborhood saturates.

Outgoing hop counts (`logs/malecns_neighborhood.json`, `n_cap` 8000): LPLC2 hop 1 already hits the cap. MN9 hop 1 is 1,196 cells, 20,282 edges, max incoming |weight| 5,107, which would seize under voltage_jump. Default circuit graph stays 475.

Transmitter audit on the 475-cell slice (`logs/malecns_signs.json`): 16,370 edges with a required-role presynaptic cell, 0 missing NT, 0 unknown, 0 monoamine. Fallback +1 was not used. Required-role signs all +1 is the 475-cell mix, not a whole-brain transmitter table. Unclear and monoamine stay at fallback; they are not flipped per synapse.

## Until a larger graph is allowed

- no `play --source malecns` as a player
- no Gate 2 quoted on MaleCNS
- no full 166k ply loop
- no photoreceptor board-in
- no PPL checkmate teacher
- no Lichess
