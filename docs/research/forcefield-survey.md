# B1: survey of open carbonate force-field parameters (decision D1)

- **Status:** first pass, 2026-11-19. Research only, no compute. Input for decision D1 in
  [calculation-plan.md](calculation-plan.md); the decision is the author's.
- **Why:** the current set (LigParGen 1.14·CM1A-LBCC, ADR 0009) gives EMC +2.9 % too dense, EC
  about −1.8 % too light, and keeps EC out of the Li⁺ shell (report §3.2–3.4).

## The model to reproduce is not open

- Lehnert 2025 (SI S1.1) took the solvent parameters and charges from **Schrödinger Maestro
  2021-1, OPLS** (Banks et al. 2005). Ions: Li⁺ from Jensen & Jorgensen 2006, PF₆⁻ from CL&P
  2004.
- Ringsby et al., J. Electrochem. Soc. 168, 080501 (2021), whose set-up Lehnert adapted, also
  assigned "charges and atom types … using values from MacroModel and the Maestro graphical
  interface (Schrödinger)", with ions scaled by 0.8. The paper does not tabulate them.
- So option (b) of the SI notes ("parameters from Ringsby 2021") gives no open parameters. Only
  a Schrödinger licence reproduces Lehnert's solvent model exactly.

## Candidates

| # | Set | Covers | Published validation | Licence / availability | Notes |
|---|---|---|---|---|---|
| 1 | **LigParGen**, 1.14·CM1A-LBCC (current) | all six | our A1: EC −1.8 %, EMC +2.9 % | server output, cited (ADR 0009) | EC carbonyl O −0.393 e |
| 2 | **OPLS-AA atom types** (Jorgensen et al. 1996 and later), as distributed with GROMACS (`oplsaa.ff`, types opls_771–779 "propylene carbonate") | EC, PC; DEC via the Caleman topology | Caleman et al., J. Chem. Theory Comput. 8, 61 (2012), SI: EC ρ = 1320.7 g/L vs 1321.4 (exp., 312.15 K); ΔH_vap 64.90 vs 60.96 kJ/mol (+6.5 %). DEC ρ 998.6 vs 969.1 (+3.0 %), ΔH_vap 52.66 vs 41.10 kJ/mol | GROMACS is LGPL-2.1; topologies at virtualchemistry.org (no licence stated on the download page; to be checked) | EC carbonyl O −0.50, C=O 0.86, ring O −0.45, CH₂ 0.21, H 0.03. The source note in GROMACS is only "Luciennes param.", so a primary citation is still missing. No DMC, EMC, MP, FEC |
| 3 | **Differentiable OPLS** (Huang et al., arXiv 2607.04633, 2026) | 67 solvents, 15 Li salts (list not checked) | LJ fitted to density; conductivity as an independent test | release of parameters not stated | worth reading in full; a preprint |
| 4 | **TraPPE extension for battery solvents** (PMC10026065) | EC, PC, DMC, DEC, DME | density, permittivity, viscosity, diffusion | journal SI | united-atom: a different model class, no EMC |
| 5 | **QM charges** (RESP or similar), our own fit (B2) | any | to be done | ours | needs a QC program (psi4 in a container) and an approved method |
| 6 | **Maestro OPLS** | all | Lehnert 2025 | commercial licence | the only exact reproduction |

## What the comparison of 1 and 2 shows already (EC)

- Same geometry (LigParGen's), point charges only:
  - LigParGen: molecular dipole **5.81 D**;
  - OPLS-AA types: **5.28 D**.
- So LigParGen's EC is not less polar overall. It places its positive charge on the hydrogens
  (+0.134 e each) instead of the carbonyl carbon. That is why its carbonyl oxygen is weak
  (−0.393 vs −0.50 e).
- A Li⁺ sees the local field at the carbonyl O. This is the most likely reason that EC is
  excluded from the shell with set 1. It is a hypothesis; A4 tests it.
- The Lennard-Jones parameters differ too (ring O: σ 0.290 vs 0.300 nm, ε 0.586 vs
  0.711 kJ/mol). Set 2 is a whole set, not a charge swap.
- The experimental dipole of EC needs a cited source before it can decide between the two.

## Experimental reference data found on the way (for A5, A7, A8)

- **Caleman 2012 SI** compiles experimental density, ΔH_vap and ε(0), each with its source:
  - CRC Handbook (90th ed.);
  - DIPPR project 801;
  - Marcus, *The Properties of Solvents* (1998);
  - Yaws.
- For EC at 312.15 K: ΔH_vap = 60.96 kJ/mol (DIPPR) and ε(0) = 89.91.
- These are candidates for the "experimental ΔH_vap / ε source" decisions (A5, A7). The
  primary references would be cited, not the SI.
- **Gruber et al., J. Electrochem. Soc. 173, 120518 (2026), CC BY 4.0** (in `../Lit`): ρ, η and σ
  of LiPF₆ in EC:DMC:EMC, 0.25–3.0 M, −20 to 45 °C. A citable source for the viscosity (A6) and
  the thermal expansion (A8) of a closely related electrolyte.

## Proposal for D1 (to decide)

1. Test set 2 on EC and PC first. It costs A1 (4 runs, about 1 h of GPU) and A4.
   - EC at 39 °C has a published OPLS-AA result: 1320.7 g/L.
   - Reproducing it checks our engine against GROMACS as well as the set.
2. For EMC and DMC, set 2 needs typing from the ester types (opls_465–470). That is a choice we
   would make, not a published topology, so it needs a source or the author's approval.
   - Alternatives: set 3, if its parameters are released;
   - or set 5 for the linear carbonates, with one method for all.
3. A licence check of the virtualchemistry.org files, and the primary source of the GROMACS PC
   types, come before anything enters `ucmd-builder`.

## Sources

- Caleman et al. 2012, paper and SI: <https://virtualchemistry.org/papers/caleman2012a-with-supp-inf.pdf>;
  topologies: <https://virtualchemistry.org/ff.php>.
- GROMACS `oplsaa.ff/ffnonbonded.itp`: <https://github.com/gromacs/gromacs/tree/main/share/top/oplsaa.ff>.
- Ringsby et al. 2021: <https://perssongroup.lbl.gov/papers/ringsby_transport_phenoma_2021.pdf>.
- You, Chaudhari, Rempe, Rick, Pratt, SAND2015-5532C (OPLS-AA ε of EC and PC):
  <https://www.osti.gov/servlets/purl/1262940>.
- Huang et al., arXiv 2607.04633: <https://arxiv.org/abs/2607.04633>.
- TraPPE battery solvents: <https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10026065/>.
