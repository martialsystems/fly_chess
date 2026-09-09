# Agent notes: fly_chess

MIT for original code. MaleCNS data remains CC BY 4.0. No GraphForge pin in this slice. Claim-ban and no-network rules live as tests.

Required roles (fail closed at resolve): sugar_grn, aversive_grn, loom_vpn, gf_escape, walk_fwd, walk_back, steer_l, steer_r, halt, feed_mn, reserved_input_pool.

Capture readout is MN9. Halt quiet is BB/FG. Spatial sugar identity is synthetic APP_LOCUS cells.

Do not add a Lichess or chess.com client. `play.py` refuses `--lichess` / `--online`.

## Verify

`python3 ~/agent_laws_verify_before_done/vbd_gate.py check --app-root . --claim-done`

`vbd.runtime.json` runs pytest and a short ethology play smoke.
