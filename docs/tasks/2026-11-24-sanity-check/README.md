# Sanity check of temperature, pressure and density (2026-11-24)

Evidence behind the SC tasks in [docs/tasks.toml](../../tasks.toml). Read-only on the project data; one
10 ps water run was made outside the repository. **Exploration**: one run, no replicas.

## Recomputed from the thermo tables (`npt_averages.py`, first 30 % skipped, 8 blocks)

| quantity | result |
|---|---|
| T | within 0.1 K of the set point in nearly all NPT runs (largest: 0.18 K); sigma_T / theory 0.977–1.012 |
| rho M0 (T2, 3 seeds) | 1.1839, 1.1841, 1.1852 g/cm³; +0.2 % against the Landesfeind fit at 1 M, 20 °C (1.1817) |
| rho M1 (T2, 3 seeds) | 1.1956, 1.1943, 1.1943; +1.1 %; scan `base_s1` with the fixed pressure probe 1.1949 |
| kappa_T of the 1 M box | about 4.6·10⁻⁵ per bar |

**Cancellation.** Ideal mixing of the model's pure solvents (EMC extrapolated to 20 °C) is +1.5 % (M0) and
+2.4 % (M1) above the fit at c = 0. The line through it and the 1 M point has slope 0.078–0.079 g/cm³ per M
against 0.0912; M1 would be +2.2 % at 0.1 M and −0.8 % at 3 M. An estimate, not a run.

## Fast vibrations at 1 fs

- **Pressure.** Virial theorem for velocity Verlet with on-step velocities: the atomic pressure is below the
  molecular one by Σ Δt² F²/(4m) / 3V (centre-of-mass part removed). SPC/Fw, 512 molecules, 1.012 g/cm³,
  298.16 K, NHC tau 0.1 ps, 1 fs, 1–10 ps (`water_1fs_run.toml`, `kinetic_split.py`): predicted −126.9 ± 0.4 bar,
  measured directly −129 ± 9 bar. GPU minus CPU in the water study: 122.6 − 26.1 = 96.5 bar, about 118 bar with
  the thermal pressure of the 2 K difference (about 11 bar/K). Engine d9a6b19 (`e29-pressure-tensor`).
- **Bond energy.** var(r_OH)/kT is 7 % larger at 1 fs (CPU viscosity run) than at 0.5 fs (CPU NPT run)
  (`bond_energy_two_timesteps.py`). The runs also differ in T, density and ensemble.
- **Temperature.** Half-step minus on-step T: 9.1 K in water; the e37 report has 288 against 293 K for the
  electrolyte. Our own estimate for harmonic modes under velocity Verlet (shadow Hamiltonian; the general point is
  in Eastwood et al. 2010, read as abstract only) puts the liquid above the displayed T by about two thirds of
  that: about 6 K in water, 3 K in the electrolyte. Molecule centres in the test:
  301.3 ± 1.5 K against 298.6 ± 0.5 K for the total. That points the right way but is neither 2 SE nor the full 6 K.

## What is not established

- A density bias of the CPU barostat: code and pressure bias suggest one, the 0.5 fs twins point the other way.
- The 3 K and the 0.3 % density effect in the electrolyte: theory only (SC-1 tests them).
- Table S2's temperatures: one search excerpt for DMC (SC-5).

## Commands

From the workspace root, `HDF5_USE_FILE_LOCKING=FALSE`, with `ucmd-analysis/.venv/bin/python`:
`npt_averages.py`; `bond_energy_two_timesteps.py`; `kinetic_split.py TRAJ.h5 1.0 1.0` (needs a trajectory with
velocities and forces). The package of `water_1fs_run.toml` is the exported last checkpoint of
`studies/2026-11-20_water-spcfw-viscosity-cpu` (`ucmd export`).
