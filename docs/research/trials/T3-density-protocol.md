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

**Amendment 1 (2026-11-25, no run of this trial started; author: "apply the corrections"):**

- "Why it is contested" compares the wrong number. 1.202 g/cm³ is the *nominal* density of the start box, 47 ion
  pairs at exactly 1.0 M. It is neither measured nor the NPT density of our model, and it was set against 25 °C.
- The NPT densities of T2 at 20 °C are 1.184 (M0) and 1.195 (M1) g/cm³, +0.2 % and +1.1 % against the Landesfeind fit
  at 1 M, 20 °C (1.182). **The defect this trial can see is +1.1 % (M1), not 2.2 %.** T3's two states
  therefore lie closer together, and a difference in D is harder to resolve than the plan assumed.
- The second reading of the Landesfeind SI is done (SC-8, [reading](../landesfeind-density/README.md)) and
  agrees. It puts the uncertainty of the reference at about ±0.6 %.
- The plan and the decision rule are unchanged.
