# Queue test of the second computer (not a result)

- **Label:** exploration; a test of the queue, not physics.
- **Run:** `minimized/T25.01C`: 512 SPC/Fw water from the minimized package of `2026-11-25_water-npt-gpu` (seed 1),
  5 ps NVT at 298.16 K, CPU, worker tag `cpu-soricel` (the second computer).
- **Check:** the job ends `done` and the run's `status.json` is `done`, written into this folder over the mount.
  Then the same `run.toml` once on the workstation: by ADR 0010 the thermo table should be identical, for any machine and
  thread count, if both use the same engine commit. A difference is reported, not explained away.

## Result (2026-11-27): identical

- Second computer: worker `soricel-pc`, job `done`, engine `ucmd 0.0.0 (c2cc427e6a10)`, 190.5 s, written into this folder
  over the mount.
- Workstation repeat of the same `run.toml` and package (in a scratch copy): engine `ucmd 0.0.0 (2ea7e826ccf5)`, whose
  Rust and Cargo files equal c2cc427 (`git diff` touches only the Python bridge), 4 threads, AMD Ryzen 7 2700X, 375 s.
- `thermo.tsv` (52 lines) is byte-identical: SHA-256 `cb64e0bd9f5cb04fc27ff76ef7a2a2a737cc744adefb5308d35c1cca6a8210d6`
  for both. ADR 0010 holds across the two CPUs (other vendor generation, other thread count) for this run.

