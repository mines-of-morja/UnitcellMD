# T5 — ion-charge scaling: fitted to κ, or from the refractive index

## Why it is contested

Lehnert fits ζ = 0.75 to κ, which makes κ an input. The electronic continuum correction (ECC)
gives ζ = 1/n_D from the solvent's refractive index, which keeps κ a prediction; carbonates have
n_D ≈ 1.38–1.42 (to be sourced), so ζ ≈ 0.70–0.73. ECC's standard justification is for ions in
polar solvents; whether it carries over to carbonates is the open point (strategy M3).

## Plan (fixed 2026-11-21; runs wait for the n_D sources, UnitcellMD#3)

- **Runs:** the model that passes T2–T4, 1 M, 20 °C, NPT, at ζ_ECC from n_D of EC:EMC 3:7 (or the
  mass-weighted mean of the pure solvents, stated), and at ζ = 0.75; three replicas each.
- **Measured:** first-shell composition and Li⁺–PF₆⁻ association (structure); κ, t₊, D reported.

**Decision rule:**

1. ζ_ECC is the default; it is not tested against κ. It is replaced only if its structure fails
   the fit-side data: the first-shell EC count against the DRS bound as in T2, and contact-ion-pair
   fractions against Raman (sources from UnitcellMD#2).
2. The κ obtained with ζ_ECC is the prediction and is compared with the pass criteria (κ ±15 % at
   1 M, 20 °C; κ maximum ±0.2 M). If it fails, the failure is reported as a result, and ζ fitted
   to κ (C1) becomes the stated fallback, labelled as a fit.
