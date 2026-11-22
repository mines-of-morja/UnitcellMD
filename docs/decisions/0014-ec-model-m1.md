# 0014 — EC model: OPLS-AA atom types of Caleman 2012 (M1) (amends ADR 0009)

- **Status:** accepted 2026-11-22 by the author ("that sounds reasonable, continue with
  that"), on the result of trial T2.
- **Context:**
  - ADR 0009 takes EC from LigParGen (M0). In the gas phase, M0 has Li⁺ binding EC no more
    strongly than the linear carbonates. QM says EC binds 6.24 kcal/mol more strongly than EMC
    (MP2/aug-cc-pVTZ, `tools/qm`).
  - Trial T2 (`docs/research/trials/T2-ec-model-1M.md`; 1 M, 3 seeds per model, 5 ns,
    pre-registered rule) measured EC carbonyl O within 0.28 nm of Li⁺:
    - M0: 0.44 ± 0.01;
    - M1: 0.97 ± 0.01;
    - dielectric spectroscopy (upper bound): 2.2 ± 0.1.
  - Rule 1 applied: M1 is closer to the bound, the difference is resolved, and M1 stays below
    the bound.
- **Decision:**
  - EC in the working-horse set comes from the OPLS-AA atom types of Caleman et al., J. Chem.
    Theory Comput. 8, 61 (2012) (opls_771–777, with the bonded types of `oplsaaff.itp`).
  - EMC, DMC, PC, MP and FEC stay LigParGen (ADR 0009). PC with the Caleman types is a
    separate test, not part of this decision.
  - The two sources share the OPLS conventions: geometric mixing, 1-4 scales 0.5/0.5.
- **Consequences:**
  - Costs:
    - ΔH_vap of pure EC is worse (+5.6 % against +1.7 % for M0).
    - The 1 M density rises from +0.2 % to +1.1 % against the Landesfeind fit (one reading).
    - The set now has two parameter sources.
  - Conductivity does not change at our precision (κ_NE 0.50 against 0.52 S/m).
  - The Li⁺ first shell still has about 1.2 EC fewer than the bound, and EMC makes up about
    77 % of it. Trial T6 (Li⁺–carbonyl O correction, strategy M3 step 3) takes this up.
  - Still open (forcefield-strategy.md §4):
    - The primary citation of the atom types has to be checked.
    - The parameters come from a local explicit itp (`studies/2026-11-20_ec-opls-test`, not in
      git). Before the library set can carry them, they have to be transcribed into the library
      format with their citation, as ADR 0009 requires for every source.
  - Until then, recipes use the `gromacs-top` source as in T2.
