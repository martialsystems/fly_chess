# Dynamics: why 2-hop LPLC2 seizes

This is a kernel note. It is not a chess gate and not a MaleCNS Elo.

## What we measured

MaleCNS v1.0 annotations (local fetch, hash-locked):

- LPLC2: 185 cells
- DNp01 (giant fiber): 2 cells
- Direct LPLC2 → DNp01: 185 edges, 4,862 synaptic contacts
- Sugar GRNs in our alias set: 247 cells
- MN9: 2 cells
- Direct sugar → MN9: 0 edges
- Disynaptic sugar → X → MN9 bridges: 39 cells

The locked identity graph is those seeds plus the 39 bridges: 475 cells. `logs/malecns_identity.json`. Circuit paint on the same slice: `logs/malecns_circuit.json`. Named-cell Hz (50 Hz identity, 100 Hz paint) is the injected pulse on an intact path, not a firing-rate discovery. The useful contrast is shuffle crosstalk.

## Why two hops from LPLC2 is ~156k

LPLC2 is a visual-projection type with 185 members. One hop already fans into a large visual and central set. A second hop from that set covers most of the retained nervous system. A run that took the 2-hop neighborhood of the identity seeds produced 155,728 cells (almost the MaleCNS neuron table). That run is discarded. It is not a lock file.

## Why full-graph LIF with these gains seizes

`config/lif.json` uses `psp: voltage_jump`: each spike adds `weight` millivolts on the postsynaptic cell in one step. MaleCNS `weight` is a synapse count. On LPLC2 → DNp01 that count is thousands. One volley drives the postsynaptic cell through threshold and, with a dense 2-hop graph, the rest of the map. In the discarded 155,728-cell run, rest rates were 0 and a sugar or loom pulse put MN9, giant fiber, and LPLC2 all near 250 to 300 Hz, including after a degree-and-sign shuffle. That is seizure, not a circuit.

The fixture (290 cells, hand-set weights) still uses voltage jumps so everyday tests stay cheap. Do not copy that PSP into a 166k ply loop.

## Next kernel (not this slice)

Current-based synapses: a small millivolt per contact, then leak through `tau_m`. Run that kernel on the 475-cell slice first.

- If the 475-cell slice still seizes, the gain is wrong.
- If it stays specific (sugar → MN9 only, loom → DNp01 only) and a 2-hop loom neighborhood no longer saturates, then a larger graph is in play.

That work is dynamics. It is not Gate 2. Chess stays on the 290-cell fixture until this kernel exists.

Until then:

- no `play --source malecns` as a player
- no Gate 2 quoted on MaleCNS
- no full 166k ply loop
- no photoreceptor board-in
- no PPL checkmate teacher
- no Lichess
