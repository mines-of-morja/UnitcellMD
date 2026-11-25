# SC-3: atomic pressure of flexible molecules at finite timestep (design note, for approval)

- **Status:** **option B approved by the author 2026-11-25.** No engine change made yet. The session
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
2. May test 2 run on the CPU (about 2 days for 3 × 1 ns)? → not before the reboot of 2026-11-25; asked again after it.

## Limits of option B (2026-11-25, from the session working on the water pressure; its numbers are preliminary)

- B removes the on-step bias of the **estimator**. It does not touch a liquid that is too warm at 1 fs (configurational
  temperatures above the displayed one: water about +6 to +8 K, M1 electrolyte about +3.6 K). So B must not be reported
  as removing the whole excess pressure; SC-1 tests the other part.
- Its direct atomic − molecular difference on stored GPU frames is −15 ± 53 bar (ρ = 1.000): not contradicting
  −129 ± 9, too noisy to confirm it.
- Wu 2006 ran leapfrog at 1 fs with a Melchionna barostat. If that used the atomic pressure (inferred, not stated in the
  paper), B moves our CPU density away from Wu's 1.012 g/cm³. Test 2 has to report this, not judge B by it.
