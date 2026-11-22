# T3 — transport at the model's density (NPT) or at the measured density (NVT)

## Why it is contested

Our boxes come out 2.2 % denser than Landesfeind's fit (1.202 against 1.176 g/cm³ at 1 M, 25 °C;
the fit is read once, by Jo's agent). Many electrolyte MD studies run NVT at the measured density;
Lehnert runs NPT. NVT at the measured density removes a known error at the cost of a non-zero
pressure; NPT keeps the model self-consistent.

## Plan (fixed 2026-11-21; runs wait for the second reading of the Landesfeind SI)

- **Systems:** the T2 winner, 1 M, 20 °C. (a) NPT as in T2. (b) NVT at ρ_exp(1 M, 20 °C) from the
  Landesfeind fit, started from (a)'s last frame rescaled. Two replicas each, 10 ns, last 8 ns.
- **Measured:** mean pressure of (b); D of Li⁺, PF₆⁻, EC, EMC; first-shell composition.

**Decision rule** (transport is reported, not used to choose):

1. If D changes by less than 2 combined SE between (a) and (b): the density error does not matter
   for transport at our precision; production stays NPT.
2. If it changes by more: the density error is a force-field defect. It is fixed on the fit side
   (strategy M2, LJ refit to ρ and ΔH_vap), production stays NPT with the fixed model, and the NVT
   results are reported as a sensitivity bound. NVT at an imposed density is not adopted, because it
   hides the defect instead of fixing it.
