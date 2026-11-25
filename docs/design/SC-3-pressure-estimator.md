# SC-3: atomic pressure of flexible molecules at finite timestep (design note, for approval)

- **Status:** **option B approved by the author 2026-11-25.** The barostat half is coded on ucmd-engine
  branch `sc3-molecular-pressure` (not pushed, not merged); question 3 is decided (3a) and built. The session
  looking for the cause of the water pressure writes no engine code. No new runs before the reboot of that day. Evidence: `docs/tasks/2026-11-24-sanity-check/README.md`.

## The effect

The engine's pressure is P = (2K + W)/V with full-step velocities and the atomic virial (`kinetics.rs`,
`dynamics.rs`). For velocity Verlet the discrete virial theorem holds with the **half-step** velocities:
⟨Σ r·F⟩ = −⟨Σ m v_half²⟩ (bound motion). Full-step kinetic energy is smaller by Σ Δt²F²/(8m). The atomic pressure
is therefore low by

    ΔP = Σ Δt² F²/(4m) / (3V)   (the centre-of-mass part removed for the internal motion)

It scales with Δt² and comes from O–H and C–H stretching. Water, 1 fs: 126.9 predicted, 129 ± 9 bar measured.
Electrolyte, 1 fs: about 62 bar, from the 5 K half-step/full-step difference of the e37 report (estimate).
The **molecular** pressure has no such term beyond the molecule centres (about 0.5 bar in water).

**Where it enters.** NVT pressure column and tensor diagonal on the CPU; C-rescale for molecules without constraints
(`scaling_virial`, `scaling_kinetic_tensor` use the molecular form only for molecules in `rigid`). The GPU
is not affected: MonteCarloBarostat and the pressure probe are molecular.

**Not shown:** that the CPU's NPT density is off. Expected about +0.3 % (electrolyte) and +0.6 % (water) at 1 fs;
the 0.5 fs water twins differ by 0.4 % the other way (2.2 σ), and the electrolyte twins by +0.2 ± 0.1 %.

## Options

| | change | for | against |
|---|---|---|---|
| A | none; document, use 0.5 fs or constraints where P matters | no risk | the 1 fs column stays biased |
| **B** | barostat and pressure column molecular for **all** molecules (the code for `rigid` exists) | same definition as the GPU; bias gone | changes every flexible NPT run and the golden hash; bitwise restarts across versions break; E2.7 decision |
| C | add Σ Δt² F⊗F/(4m) (half-step kinetic tensor) | keeps the atomic virial, tensor still atomic | one more convention; its effect on Green–Kubo has to be tested |

**Recommendation:** B, after the test below; keep the atomic tensor as it is for Green–Kubo until its own test.

## Tests (before any change)

1. Bias at 1, 0.5 and 0.25 fs from the same state, water and electrolyte: ratios 16 : 4 : 1 (direct and predicted).
2. NPT density of water at 1 fs, CPU (atomic), CPU (option B, on a branch) and GPU, at least 3 seeds. The verdict on the
   density comes from this test only.
3. Green–Kubo η of the existing water run with the atomic tensor against a molecular tensor (A4 or B of the
   1 M box is T4's matter).

CPU cost: about 2.7 ns/day for 1536 atoms on 8 threads; runs wait until Psi4 (`t6_geometries`) is done.

## Questions for the author

1. A, B or C? → **B** (author, 2026-11-25).
2. May test 2 run on the CPU? → **yes, right after the reboot of 2026-11-25** (author, the same day). Plan, criteria and analysis:
   `studies/2026-11-25_water-npt-cpu-molecular/` (both CPU arms need 6 × 1 ns, about 2.2 days; GPU arm about 1 h).

## Limits of option B (`docs/research/water-pressure/README.md`, 2026-11-25, other session)

- B removes the on-step bias of the **estimator** only. The liquid is also warmer than displayed at 1 fs (configurational
  temperatures: water +6.5 K, electrolyte M1 +3.4 ± 0.5 K), worth about 72 bar in water; 49 ± 12 bar remain. B must not be
  reported as removing the whole excess. SC-1 (1 fs against 0.5 fs) tests this part.
- CPU and GPU agree once both use the molecular definition (about 109 and 122.6 ± 11.9 bar at 1.012 g/cm³).
- Wu 2006 ran leapfrog at 1 fs with a Melchionna barostat. If that used the atomic pressure (inferred, not stated in the
  paper), B moves our CPU density away from Wu's 1.012 g/cm³. Test 2 reports this and is not judged by it.

## Implementation (2026-11-25, branch `sc3-molecular-pressure` from `e25-constraints`)

- **Barostat:** every group of atoms connected by bonds or constraints is shifted with its centre of mass, and the
  barostat's pressure and virial are the molecular ones of that move. Single atoms and atoms that nothing connects are scaled on
  their own, so systems without bonds (argon, the NaCl and Kob–Andersen fixtures) do not change.
- **Why groups and not molecule types:** the spec allows a type with several unconnected atoms; the first version moved those
  as one body and failed the existing ideal-gas test. The test was right and is unchanged.
- **Tests (written first; two of them failed on the old code):**
  - barostat virial against −dE/dε of the move: −346.541807 and −346.541807 kJ/mol (old code −19 529);
  - free stiff dimers, NVE: barostat pressure = Σ M V²/(3V) to 5·10⁻¹⁵ at every step; atomic minus molecular −2.12 bar at
    1 fs and −10.01 bar at 2 fs against −2.09 and −10.00 from Σ Δt²F²/(4m)/(3V);
  - NPT of stiff dimers: range of the conserved quantity 0.151 kJ/mol (molecular), 0.159 (atomic): no worse.
- **Changes** every flexible NPT run on the CPU (not bitwise comparable with older versions). It supersedes "atomic scaling"
  of E2.7 §2 and extends E2.5 §2 to molecules without constraints.
- **Not shown:** any effect on the density. That is test 2, which has not run.

## Question 3: the pressure column needs a spec decision → **3a** (author, 2026-11-25)

**Built the same day:** spec 0.1.3 (`[output.thermo] pressure_molecular`, off by default, defined in units.md §4; not tagged) and
engine commit `f291a40`. Off by default keeps the thermo tables and restart fingerprints of older runs. CPU tests as
under "Checks"; bridge 37 passed on CPU platforms. On the GPU bridge both columns hold the same (molecular) value. H5MD
observables are unchanged. The text below is the question as asked.

Option B as written above includes the pressure column. That column is defined in the tagged spec: P = (Σ m v⊗v + W)/V
(units.md §4), and `pressure_bar` is the trace / 3 of `pressure_tensor` (run-config.md). It therefore stays atomic for now. Until this is
decided, a flexible CPU run under NPT at 1 fs will show a mean `pressure_bar` **below its target** by the bias (water about 129 bar,
electrolyte about 62 bar, the latter an estimate), although the barostat holds the molecular pressure at the target.

| | change | for | against |
|---|---|---|---|
| **3a** | add a column `pressure_molecular_bar` (spec addition, like 0.1.1) | nothing changes meaning; Green–Kubo tensor untouched; both visible | two columns |
| 3b | redefine `pressure_bar` as molecular | one number | changes a tagged definition; no longer the trace of the tensor |
| 3c | leave it, document it | no spec change | easily misread |

The bridge already writes the **molecular** pressure into `pressure_bar` (documented in `openmm_backend.py`), so the column means
different things on CPU and GPU today. **Recommendation: 3a.**

## Checks

- Commit on `sc3-molecular-pressure`; fmt, clippy (`-D warnings`), architecture check and `--no-default-features` build pass. Full
  workspace tests: everything passes except two `ucmd-io` contract tests, which fail in the same way on `e25-constraints` without this change:
  that branch predates spec 0.1.2 (`pair_overrides`) and reads the workspace's newer fixtures. With the spec commit that CI pins
  (`da27ef7`) all three contract tests pass.
- Run `cargo test -p ucmd-md -- the_barostat_ bonded_groups npt_with` (about 2 minutes) to repeat the numbers above.
