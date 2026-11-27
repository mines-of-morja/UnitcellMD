# Queue controls on the second computer (not a result)

- **Label:** exploration; a test of the queue, not physics.
- **Run:** `minimized/T25.01C`: 512 SPC/Fw water (package of `2026-11-25_water-npt-gpu`, seed 1), 20 ps NVT, CPU, tag
  `cpu-soricel`, checkpoint every 1 ps. About 13 minutes on 6 threads.
- **Check, fixed before the run:**
  1. The thread count in `run.log` is the one chosen in the dashboard.
  2. "Free this computer" or "Stop" during the run: the job goes back to the queue (or waits), `status.json` says
     `stopped`, nothing keeps computing; "Use again" or "Continue" resumes from the checkpoint and the job ends `done`.
  3. The `thermo.tsv` of the interrupted run equals that of an uninterrupted run of the same `run.toml` here (CPU
     reference backend: bit-identical, also across a restart; CLAUDE.md invariant 8, ADR 0010). A difference is reported,
     not explained away.
