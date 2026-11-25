# Queue test of the second computer (not a result)

- **Label:** exploration; a test of the queue, not physics.
- **Run:** `minimized/T25.01C`: 512 SPC/Fw water from the minimized package of `2026-11-25_water-npt-gpu` (seed 1),
  5 ps NVT at 298.16 K, CPU, worker tag `cpu-soricel` (the second computer).
- **Check:** the job ends `done` and the run's `status.json` is `done`, written into this folder over the mount.
  Then the same `run.toml` once on the workstation: by ADR 0010 the thermo table should be identical, for any machine and
  thread count, if both use the same engine commit. A difference is reported, not explained away.
