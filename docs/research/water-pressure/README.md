# Why the pressure of SPC/Fw water is too high at Wu's density (2026-11-25)

- **Label:** exploration. No new simulation: stored frames are evaluated again (positions only), on
  OpenMM's CPU platform.
- **Question (author):** which parts make up the pressure, and what is the root of the excess?
  At 1.012 g/cm³ (Wu 2006) the GPU gives 122.6 ± 11.9 bar and the CPU engine 26 ± 7 bar; about 1 bar is expected.

## Answer

**The root is the 1 fs step with flexible O–H bonds.** It has two separate effects:

1. **Two definitions of the pressure differ by about 127 bar.** The GPU reports the molecular pressure
   (molecule centres), the CPU engine the atomic one (all atoms, on-step velocities).
   - In exact dynamics both averages are equal. At a finite step the on-step kinetic energy of the bonds
     is too small for the atomic virial, and the atomic value is low by Σ Δt²F²/(4m)/(3V)
     (`docs/tasks/2026-11-24-sanity-check`: −126.9 predicted, −129 ± 9 measured).
   - The CPU frames, evaluated here by the molecular definition, give 131 ± 15 bar at 300.2 K, about
     109 bar at 298.16 K (GPU: 122.6 ± 11.9). **Both engines agree once the definition is the same.**
   - The engine's sum is right: the atomic pressure computed here equals the logged one frame by frame
     (mean difference 0.24 bar, scatter 0.56 bar, frames of a 1255 bar spread).
2. **The liquid is warmer than displayed, and that raises the true pressure.** The thermostat holds the
   on-step kinetic energy of *all* atoms at the set temperature. The fast bonds show too little of it,
   so the slow motion takes the rest.

   | run | excess over the set temperature (K) | expected, ⅔ of (half-step − on-step) |
   |---|---|---|
   | water, 1 fs, 5 runs (GPU and CPU) | +6.5 ± 0.2; the runs spread from 5.0 to 8.2 | +6.1 |
   | water, 0.5 fs, 2 runs | +2.9 ± 0.8 | +1.5 |
   | electrolyte M1, 1 M, 1 fs, 3 replicas | +3.4 ± 0.5 | +3.6 |

   These are configurational temperatures of molecule translation and, for water, rotation: from
   forces and their derivatives, without velocities. The thermostat does not act on them directly.

## Pressure budget at 1.012 g/cm³, 298.16 K, 1 fs

| part (molecular) | bar |
|---|---|
| ideal, molecule centres | +1390 |
| Coulomb | −41 945 ± 35 |
| Lennard-Jones within the cutoff | +40 885 ± 72 |
| Lennard-Jones tail | −285 |
| bonds and angles | 0 (exact: they act inside a molecule) |

The sum of these 300 frames is 69 ± 45 bar; the thermo log has ten times the samples and gives 122.6 ± 11.9:

| contribution to the 122.6 ± 11.9 bar | bar |
|---|---|
| excess temperature, 6.5 K × 11.2 bar/K (Wu's α_P and κ_T) | 72 ± 2 |
| 1 atm | 1 |
| remainder: model, box size and what else the step changes | 49 ± 12 |

- **Remainder:** it corresponds to 1.0095 ± 0.0006 g/cm³ at 1 atm without the temperature effect. The 0.5 fs
  runs gave 1.0079 ± 0.0012 and 1.0089 ± 0.0011. An estimate, not a run.
- **Wu's 1.012 may be the atomic pressure.** Atomic P at 1.012 is −4 ± 12 bar (GPU) and about 4 bar (CPU, at
  298.16 K), i.e. 1 atm. Wu used DL_POLY 2.13, leapfrog, 1 fs, a Melchionna barostat. That this barostat used the
  atomic virial is an inference; the paper does not say. If it holds, the 0.47 % density gap is the pressure
  definition, and 1.012 is not the model's density.

## What is not established

- **The Δt² law of the temperature:** 0.5 fs gives +2.9 ± 0.8 K where +1.5 is expected (1.7 σ). Kinetic energies of
  the molecule centres from the GPU log give +5.3 ± 1.1 K there, 3 σ above; unexplained. Zero at Δt → 0 is therefore
  assumed, not shown.
- **Errors:** from 8 jackknife blocks of one run each. χ²/dof of the rotation values is 4.1, so ±0.2 K is too small;
  the run-to-run spread is the better guide.
- **Direct atomic − molecular difference here:** −147 ± 37 bar (CPU), −98 ± 34 (Wu run). The three GPU scans give
  −15 ± 53, −243 ± 76, 2 ± 52. Consistent with −127, too noisy to add to it.
- **Other molecules:** the electrolyte's pressure was not decomposed.

## Candidate fixes (nothing changed; for the author)

| | fixes | cost | remaining |
|---|---|---|---|
| **1. Molecular pressure and barostat** (SC-3 option B) | effect 1 | none at run time | effect 2; moves the CPU density away from Wu's 1.012 |
| **2. Step 0.5 fs** | both, to a quarter if Δt² holds | twice the run time, no code | about 1–3 K in water |
| **3. Multiple time step (RESPA)**: bonded terms at 0.25 fs, the rest at 1 fs | both, to about 1/16 if Δt² holds; the model and the definitions stay | engine and bridge code, validation; run time unmeasured | resonance test needed |
| 4. Thermostat on ⅓ K(on-step) + ⅔ K(half-step) | effect 2, to leading order | small code change | effect 1; temperature column changes meaning |
| 5. Constrain X–H bonds | both, mostly | faster | **changes the model**; Wu and Lehnert did not |

**Recommendation:** 1, as already approved, plus 2 as the test that decides. If SC-1 (1 fs against 0.5 fs, three seeds)
confirms the temperature effect, build 3 as the permanent fix. Not 4: it corrects the number, not the cause.

**SC-1 result (added 2026-11-27):** the test that decides was run. At 0.5 fs every density is higher than at 1 fs, by
+0.23 ± 0.04 % (1 M box), +0.31 ± 0.03 % (EMC) and +0.14 ± 0.05 % (water), each beyond the criterion
(`studies/2026-11-25_timestep-1M-0p5fs`). So effect 2 is real in density. Building option 3 (RESPA) or moving to 0.5 fs is the
author's choice; the temperatures themselves were not yet measured in these runs.

## Consequences for existing results (1 fs)

- Water: the runs at 298.16 K describe about 304 K. ΔH_vap, D, ε and η carry that; agreement with Wu is like with like
  if Wu's run had the same artefact.
- Electrolyte: about 3.4 K too warm, so D and κ are a little too high and ρ a little too low. This does not explain
  the factor 2 in κ: it goes the other way.
- T1 and T2 compare models under the same step, so a common shift should largely cancel (not tested).

## Files

`pdecomp.py` (water: temperatures, pressure by component), `tconf.py` (any molecules: configurational
temperature), `combine.py` (the numbers above), `data/` (one JSON per run). Commands, from the workspace root with
`PYTHONPATH=ucmd-engine-constraints/bridge/src HDF5_USE_FILE_LOCKING=FALSE` and `ucmd-engine/bridge/.venv/bin/python`
(OpenMM 8.6.1.dev, CPU platform; `model.py` and `package.py` of bridge c2cc427):

    pdecomp.py PACKAGE RUN_OUT SKIP_PS FRAMES CUTOFF_NM EWALD_TOL T_SET OUT.json
    tconf.py   PACKAGE RUN_OUT SKIP_PS FRAMES CUTOFF_NM EWALD_TOL OUT.json
    ucmd-analysis/.venv/bin/python docs/research/water-pressure/combine.py

| data | study, run | skip (ps), frames |
|---|---|---|
| `water_gpu_rho*` | `2026-11-23_water-pressure-vs-density` | 500, 300 |
| `water_wu` | `2026-11-20_water-spcfw-wu` | 500, 1200 |
| `water_cpu1` | `2026-11-20_water-spcfw-viscosity-cpu` | 200, 1200 |
| `water_cpu05`, `water_gpu05` | `2026-11-20_water-spcfw-cpu`, `…-gpu-twin` | 50, 201 |
| `electrolyte_m1_s*` | `2026-11-21_trial-t2-ec-model-1M`, `t2_m1_s*` | 1000, 360 |
