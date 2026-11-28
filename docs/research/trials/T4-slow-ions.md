# T4 — why are the ions slow: the solvent, or Li⁺ binding?

## Why it is contested

κ is a factor 2.0 below experiment and κ_NE a factor 1.8, so the ions move too slowly; association
does not explain it. Two causes are defensible and lead to different fixes:

- **(a) the solvent is too viscous** (LigParGen EMC is 2.9 % too dense): fix the solvent (M2).
- **(b) Li⁺ sticks to its shell** (ion charges, Li⁺–O): fix the ion side (M3).

## Plan (fixed 2026-11-21; needs spec 0.1.1, the pressure tensor in the thermo table, which the
author has not approved yet)

- **Runs:** Green–Kubo shear viscosity of pure EMC and of the 1 M electrolyte (the T2 winner), 25 °C,
  NVT at the NPT density, pressure tensor every step, enough length for the integral to plateau
  (about 9 GPU hours in total; the method is validated on SPC/Fw water,
  `studies/2026-11-20_water-spcfw-viscosity-cpu`).
- **Reference:** Logan et al. 2018, Fig. 3a (LiPF₆ in EC:EMC 30:70 w:w, 0–2 mol/kg, 10–40 °C) and the
  pure-EMC row of their Table I; values read off the figure go into the ledger with their reading
  error.

**Decision rule** (viscosity is a property of the solvent model, not a transport target of the
model choice; still, nothing is fitted to it here):

1. η(EMC) and η(1 M) both more than 25 % above experiment: cause (a); the next step is M2.
2. Both within 25 %: cause (b); the next step is M3 (ζ from n_D, then Li⁺–O).
3. Pure EMC right but 1 M too high: the excess comes from the ions; cause (b), M3 first.
The 25 % margin is a proposal for the author; it is wider than the expected statistical error of
Green–Kubo viscosity (10–20 %).

## Amendment 2026-11-27 (author: margin approved; time step 1 fs)

- **The 25 % margin is approved** ("lets try the 25 % margin"). The decision rule above stands
  as written.
- **Time step:** 1 fs (ADR 0017). SC-1 puts D about 5–10 % high at 1 fs against 0.5 fs; the
  viscosity is expected to shift by a similar amount the other way, well inside the 25 %
  margin, and is reported with that band.
- **What blocks the runs:** the GPU backend refuses `pressure_tensor` (spec 0.1.1), because
  OpenMM has no virial. The CPU engine computes the tensor, but runs the 1 M box at about
  1.2 ns/day (70 ms per step on 16 threads, `validation/m2a`), too slow for Green–Kubo.
- **Route found:** OpenMM 8.5's `MonteCarloFlexibleBarostat.computeCurrentPressure` returns
  all six tensor components (finite-difference derivatives of the energy with respect to the
  box matrix; atomic virial with `scaleMoleculesAsRigid = false`). Implemented in the bridge,
  it would let the GPU fill the six columns of spec 0.1.1 without a spec change.
- **Step 0, measurement only:** `docs/research/viscosity/bench_tensor.py` (queue job, after the
  3 M map) times one tensor against one MD step on the 1 M box and on pure EMC, in mixed and
  double precision. The cost decides the sampling interval and whether the route is affordable.
  The bridge change itself needs a design note and the author's approval (CLAUDE.md, phases).
