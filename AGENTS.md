# Agent notes: fly_chess

MIT for original code. MaleCNS data remains CC BY 4.0. No GraphForge pin in this slice. Claim-ban and no-network rules live as tests.

Required roles (fail closed at resolve): sugar_grn, aversive_grn, loom_vpn, gf_escape, walk_fwd, walk_back, steer_l, steer_r, halt, feed_mn, reserved_input_pool.

Capture readout is MN9. Halt quiet is BB/FG. Spatial sugar identity is synthetic APP_LOCUS cells.

Do not add a Lichess or chess.com client. `play.py` refuses `--lichess` / `--online`.

Planes/ML is closed. Write-up: `docs/planes_note.md`. Do not train another linear or factored head on this graph. Do not restamp ethology 0.4875 / 0.4875 or Gate 2 n=40. Do not quote check-escape exact-match as occupancy or wiring (`flee_ok` = 1.0). The 475-cell MaleCNS identity/circuit work is a different object (sugar → MN9, loom → DNp01, shuffle crosstalk). `hanging_capture_real_gt_shuffled` is not a win: 774 vs 668 hanging chances.

MaleCNS fetch is opt-in. Pytest uses the 1,007-cell fixture. Chess stays on the fixture. MaleCNS identity and circuit use `malecns_current` in `config/lif.json` (8.0 current-units per contact, leak through tau_m). Fixture games stay on `fixture_voltage_jump`. Named-cell Hz is the injected pulse, not a rate discovery; contrast is shuffle crosstalk. A capped 2-hop LPLC2 probe saturates; do not expand the graph. No games, no Elo. Do not quote Gate 2. No `play --source malecns`. No 166k ply loop.

## Verify

`python3 ~/agent_laws_verify_before_done/vbd_gate.py check --app-root . --claim-done`

`vbd.runtime.json` runs pytest and a short ethology play smoke.
