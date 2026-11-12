# Lehnert et al. 2025 — MD protocol from the supplementary information

- **Sources:** L. Lehnert et al., J. Electrochem. Soc. 172, 050523 (2025),
  doi:10.1149/1945-7111/add381 (open access, CC BY 4.0), and its supplementary information.
  Local copies: `../Lit/Lehnert_2025_J._Electrochem._Soc._172_050523.pdf` and `…_SI.pdf`.
- **Purpose:** the reproduction target of track A2 and the force-field inputs of B1.3. Section
  numbers (S1.x) refer to the SI.
- Recorded 2026-11-12. Everything here is transcribed from the SI; verify against the PDF
  before using a number in production.

## Software and model (S1.1)

- **Engine:** LAMMPS, run on the bwForCluster JUSTUS 2. The set-up is adapted from Ringsby et
  al., J. Electrochem. Soc. 168, 080501 (2021).
- **Force field:** OPLS (Banks et al., J. Comput. Chem. 26, 1752 (2005)), non-polarizable.
  - **Solvent parameters and partial charges: Schrödinger Maestro, Release 2021-1.** This is
    commercial software, so the parameters are not openly available (see the decision at the end).
  - **Li⁺:** Jensen & Jorgensen, J. Chem. Theory Comput. 2, 1499 (2006).
  - **PF₆⁻:** Canongia Lopes & Pádua, J. Phys. Chem. B 108, 16893 (2004) (CL&P).
  - **Ion charge scaling ζ** (S1.4, Table S3): ζ = **0.75** for LiPF₆ in EC:EMC (3:7 w:w); 0.75
    for EC:DMC:PC; 0.73 for EC:EMC:MP. ζ is fitted to experimental conductivity at 1.0 M,
    averaged over −20 °C … 20 °C, and then used for all concentrations and temperatures.
- **Nonbonded interactions:** 12-6 Lennard-Jones and short-range Coulomb with a **1.4 nm
  cutoff**; **geometric mixing**; long-range Coulomb by **PPPM, accuracy 10⁻⁵**.

## Protocol (S1.1)

1. **Packing:** Packmol, random configuration in a cubic periodic box.
2. **Preparation:** energy minimization; random velocities at 25 °C.
3. **Equilibration:**
   - 3 ns NPT at 1 atm, 25 °C;
   - 3 ns of cooling to the target temperature;
   - 3.5 ns of further equilibration.
   - The box volume is the average over the last 0.5 ns.
4. **Production:** NVT at that volume for **50–170 ns**; the last **40–160 ns** are evaluated.
5. **Thermostat and barostat:** Nosé–Hoover, damping 100 fs (thermostat) and 1000 fs
   (barostat).
6. **Integrator:** velocity Verlet with a **1 fs** time step.
7. **Statistics:** **three independent simulations** per state point; the mean ± standard
   deviation is reported.
8. **Onsager analysis:** Fong et al.'s code (https://github.com/kdfong/transportcoefficients-MSD,
   Macromolecules 53, 9503 (2020)) with MDAnalysis. The Fickian regime is identified with
   β(t) = d ln MSD / d ln t ≈ 1 (S1.3).

## Particle numbers for LiPF₆ in EC:EMC (3:7 w:w) (S1.2, Table S1)

Each system has 500 solvent molecules; for 0.1 M all counts are doubled. The 1.0 M row is
taken from Ringsby et al.

| c (M) | Li⁺ | PF₆⁻ | EC | EMC | atoms |
|---|---|---|---|---|---|
| 0.1 | 9 | 9 | 336 | 664 | 13 392 |
| 0.5 | 23 | 23 | 168 | 332 | 6 844 |
| **1.0** | **47** | **47** | **168** | **332** | **7 036** |
| 1.5 | 74 | 74 | 168 | 332 | 7 252 |
| 2.0 | 103 | 103 | 168 | 332 | 7 484 |
| 2.5 | 134 | 134 | 168 | 332 | 7 732 |
| 3.0 | 168 | 168 | 168 | 332 | 8 004 |

- Atom counts are computed here: EC 10, EMC 15, Li⁺ 1 and PF₆⁻ 7 atoms per molecule.
- The solvent mass ratio comes from the manufacturers' densities (Table S2, g/ml): EC 1.321,
  EMC 1.006, DMC 1.069, PC 1.204, MP 0.915.
- Ion numbers were tuned at 20 °C until the simulated concentration matched the target.

## Consequences for UnitcellMD

- **Production cost (affects E2.8 and E3.7).** One state point is 3 replicas of up to 170 ns
  at 1 fs, i.e. up to 5×10⁸ MD steps for about 7k atoms with PME. That is a strong argument
  for a performance target, and for the OpenMM-as-provider path on the GPU as a production
  fallback.
- **B1.4 composition calculator:** reproduce Table S1 from the recipe "c M LiPF₆ in EC:EMC 3:7
  w:w, 500 solvent molecules" as a test case. Note that Lehnert tuned the ion counts by
  simulation; the calculator should report the concentration it achieves.
- **B1.3 force-field templates.** The solvent parameters come from commercial software, so the
  author must decide (STATUS.md):
  - (a) obtain the Maestro OPLS parameters via a Schrödinger licence; or
  - (b) take openly published parameters from Ringsby et al. 2021, if their SI contains them; or
  - (c) use an open OPLS-AA parameterization (e.g. LigParGen) and accept a deviation from the
    paper.

  Li⁺ (Jensen & Jorgensen 2006) and PF₆⁻ (CL&P 2004) are openly published.
