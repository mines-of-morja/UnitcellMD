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
0.2 % change is resolved, a 0.1 % one is not). Older runs with other protocols or bridges are
known too: EMC at 1 fs, 25 °C, 1.0347 g/cm³ (500 ps, one run); water at 0.5 fs, GPU 1.0103(12) and CPU 1.0064(13) g/cm³, both
short. No run of this study, and no run of `2026-11-25_water-npt-gpu`, has been looked at.

## Running it

Queue jobs (CLAUDE.md, "Compute jobs"); needs `2026-11-25_water-npt-gpu` finished for the analysis only:

    submit command --needs gpu-hip-double -- bash studies/2026-11-25_timestep-1M-0p5fs/run_water.sh 0p5fs    (and 0p25fs)
    submit study 2026-11-25_timestep-emc-1fs --needs gpu-hip-mixed    (and …-emc-0p5fs, …-1M-0p5fs)

Then `HDF5_USE_FILE_LOCKING=FALSE python3 analyze.py OUT.json`.

## Result (2026-11-27, all 16 runs done; `analyze.py`, output `docs/research/timestep/sc1.json`)

**The step matters in all three liquids.** By criterion 2, SC-4 and T4 need **0.5 fs or a multiple time step**; the
author decides which.

| System | ρ(0.5 fs) − ρ(1 fs) | 95 % interval | criterion 1 |
|---|---|---|---|
| 1 M box, 20 °C | +0.227 ± 0.039 % (+0.00271 g/cm³) | +0.12 to +0.33 % | **matters** |
| pure EMC, 25 °C | +0.308 ± 0.030 % (+0.00319 g/cm³) | +0.23 to +0.39 % | **matters** |
| water, 298.16 K | +0.141 ± 0.046 % (+0.00142 g/cm³) | +0.01 to +0.27 % | **matters** |

± is 1 SE from the seeds. The prediction for the 1 M box was +0.2 %.

**D, reported, not judged** (ln D(0.5) − ln D(1) as a percentage, ± 1 SE, 95 % interval):

| | Li⁺ | PF₆⁻ | EC | EMC |
|---|---|---|---|---|
| 1 M box | −11 % (−0.116 ± 0.094; −31 to +16 %) | −13 % (−0.135 ± 0.099) | −8 % (−0.087 ± 0.036) | −9 % (−0.089 ± 0.065) |
| pure EMC | | | | −6 % (−0.058 ± 0.021; −11 to 0 %) |

All are lower at 0.5 fs, the direction predicted. None is resolved at 95 % on its own.

**Not judged:**
- **Water at 0.25 fs (one run):** 1.00896 g/cm³. That is 0.07 % above the 0.5 fs mean, against a quarter of the
  1 → 0.5 fs step (0.035 %) if the bias goes as Δt². One run's spread is about 0.05 %.
- **Halves:** the three 0.5 fs runs of the 1 M box all rise between their halves (+0.0008 to +0.0014 g/cm³). If they are
  still settling, the 0.5 fs density and the difference are underestimated. The 1 fs arm shows no common sign.
- **Configurational temperatures** (added 2026-11-27; `docs/research/timestep/tconf/`, `run_all.sh` and `combine.py`, 200 frames
  per run). Configurational minus displayed T, mean of the seeds ± SE of the seeds:

  | | 1 fs | 0.5 fs | 0.25 fs | expected (Δt²) |
  |---|---|---|---|---|
  | 1 M box | +3.7 ± 0.5 K | +1.7 ± 0.9 K | – | 3.4 → 0.9 K |
  | pure EMC | +5.3 ± 1.6 K | −0.2 ± 0.6 K | – | – |
  | water | +6.0 ± 0.6 K | +2.4 ± 1.0 K | +0.3 K (one run) | 6.5 → 1.6 → 0.4 K |

  The excess shrinks with the step, as the shadow-Hamiltonian estimate says. The error of one run (jackknife, 1.3–1.7 K) is as large
  as the 0.5 fs values, so the Δt² law is neither confirmed nor rejected. Computed after the result above and not part of the verdict.
  This was planned for the queue, but ran by hand on the workstation at nice 19 (19 runs in under 20 min, beside SC-3's CPU job).

**Provenance and the one interruption:** all 16 runs used `ucmd` 2ea7e82, bridge c2cc427, HIP (1 M and EMC mixed, water
double). `emc_500_s1` at 1 fs hung on the GPU at 241 ps (telemetry, 2026-11-26 02:34 UTC). It was continued from its
200 ps checkpoint by the driver, as criterion 5 provides. No run was dropped and no seed was added.

**What this means for results at 1 fs (estimate, not tested):** T2, the 1 M sensitivity scan and the transport pilot
read the density about 0.2–0.3 % low and D about 5–10 % high against 0.5 fs. Comparisons between models at the same
step should largely cancel.
