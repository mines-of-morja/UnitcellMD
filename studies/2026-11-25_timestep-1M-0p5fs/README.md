# SC-1: is the 1 fs liquid too warm? Density and D at 1 fs against 0.5 fs

- **Label:** confirmatory. Plan, criteria and `analyze.py` (with tests) are committed before the first run.
- **Question:** with flexible bonds and a 1 fs step the thermostat holds the on-step kinetic energy, and the liquid should be
  warmer than displayed (`docs/research/water-pressure`: +6.5 K in water, +3.4 ± 0.5 K in the 1 M box, from stored frames).
  Does that change the density and D enough to matter, i.e. does SC-4 and T4 need 0.5 fs?
- **Requested by:** task SC-1 (`docs/tasks.toml`, no author gate). Constraints are not the test (they change the model).

## Runs

| System | 1 fs | 0.5 fs | 0.25 fs |
|---|---|---|---|
| 1 M, M1, 7036 atoms, 20 °C, 5 ns (first 1.5 ns skipped) | `base_s1..3` of `2026-11-24_parameter-sensitivity-1M` (done) | this folder | – |
| pure EMC, 500 molecules, 25 °C, 2 ns (0.5 skipped) | `2026-11-25_timestep-emc-1fs` | `2026-11-25_timestep-emc-0p5fs` | – |
| SPC/Fw water, 512 molecules, 298.16 K, 1 ns (0.2 skipped) | `2026-11-25_water-npt-gpu` (arm G of SC-3) | `2026-11-25_timestep-water-0p5fs` | `2026-11-25_timestep-water-0p25fs`, seed 1 only |

- Three seeds per arm. The 1 M arms start from the same three minimized packages. Other velocities and noise: the two
  trajectories of a pair separate within picoseconds, so the seeds count as independent.
- **Same at every step:** all intervals are the same in time, not in steps (barostat move, centre-of-mass removal, thermo,
  trajectory, checkpoint). Nose-Hoover tau 0.1 ps, pressure 1 atm, cut-offs and PME as in the 1 fs runs.
- **Engine and bridge:** 1 M and EMC: `ucmd` 2ea7e82, bridge c2cc427, HIP mixed (the scan's copies). Water: the
  same binary and bridge in double precision, as `2026-11-25_water-npt-gpu`. GPU power limit: 150 W for the 1 M baselines
  (finished before the reboot), 250 W now. EMC has both arms now.
- **Cost (estimate, 105 ns/day at 1 fs):** 1 M 3 × 137 min, EMC 3 × 27 + 3 × 55 min, water 3 × 40 + 80 min, about 14 h of GPU.

## Criteria, fixed before the runs

Seeds are the unit of error. s² is pooled over the two arms (4 degrees of freedom); SE of a difference is √(2 s²/3).

1. **Density, each system:** ρ(0.5 fs) − ρ(1 fs). It **matters** if it exceeds 2 SE and 0.1 % (the acceptance line of SC-1).
   **Below 0.1 %** if the difference plus 2 SE is at most 0.1 %. **Unresolved** otherwise. 2 SE with 4 degrees of freedom is a
   two-sided 88 % interval; the 95 % interval (2.776 SE) is printed next to it.
2. **Timestep for SC-4 and T4:** 0.5 fs, or a multiple time step (the author decides which), if the 1 M box or EMC
   matters; 1 fs if both are below 0.1 %; otherwise unresolved and the author decides. Water decides only about water.
3. **D** (from `ucmd-analyze diffusion`, 1 M: Li, PF6, EC, EMC; EMC: EMC) is **reported, not judged**: ln D(0.5) − ln D(1) with its
   SE. The run-to-run SD of ln D_Li is 0.10, so three seeds resolve about 0.16 at 2 SE, and the expected change is a few %.
4. **0.25 fs (one run, water):** reported, not judged. One run cannot decide the density law.
5. No seed is added after looking. A run is not dropped; a failed run is repeated from its checkpoint by the driver.

**Prediction (from SC-1 and the task text, before the runs):** 1 fs is about 3 K too warm in the electrolyte and the density about
0.3 % low, so 0.5 fs should raise the 1 M density by about three quarters of that, 0.2 %. Water and D: direction only (water
denser and D lower at 0.5 fs).

**Also computed, not judged:** the configurational temperature of every run (`docs/research/water-pressure/tconf.py`). Expected
excess if it follows Δt²: 1 M 3.4 → 0.9 K; water 6.5 → 1.6 → 0.4 K. The earlier 0.5 fs water value was +2.9 ± 0.8 K.

**Already seen:** the 1 M 1 fs densities, 1.1949, 1.1937, 1.1943 g/cm³ (SD 0.0006, so 2 SE is about 0.08 % for a difference; a
0.2 % change is resolved, a 0.1 % one is not). The EMC and 0.5 fs numbers and the water 1 fs numbers have not been seen.

## Running it

Queue jobs (CLAUDE.md, "Compute jobs"); needs `2026-11-25_water-npt-gpu` finished for the analysis only:

    submit command --needs gpu-hip-double -- bash studies/2026-11-25_timestep-1M-0p5fs/run_water.sh 0p5fs    (and 0p25fs)
    submit study 2026-11-25_timestep-emc-1fs --needs gpu-hip-mixed    (and …-emc-0p5fs, …-1M-0p5fs)

Then `HDF5_USE_FILE_LOCKING=FALSE python3 analyze.py OUT.json`.
