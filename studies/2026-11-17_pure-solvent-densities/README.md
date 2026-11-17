# Pure-solvent densities (2026-11-17), research plan level 1

- **Question:** which density does `opls-aa-carbonates` give for pure EC, EMC, DMC, PC and MP
  at 1 atm? Compared with the manufacturer densities of Lehnert 2025 SI Table S2: EC 1.321
  (liquid), EMC 1.006, DMC 1.069, PC 1.204, MP 0.915 g/cm³. The table gives no temperature;
  25 °C is assumed (about ±0.5 %), and EC is compared at 40 °C (it melts at 36 °C).
- **Why:** the 1 M EC:EMC box at Lehnert's density still shows several hundred bar after 77 ps
  (`2026-11-17_pressure-at-reference-density`). Pure solvents tell whether the solvent parameters
  or the ions cause it. The plan's level 1 asks for densities within 1–2 %.
- **Protocol:**
  - 500 molecules, packed at the Table S2 density, one minimization on the CPU;
  - 500 ps NPT at 1 atm on the GPU backend (E3.7): Nosé–Hoover τ = 0.1 ps, MonteCarloBarostat,
    1 fs, 1.4 nm cutoff, PME to 10⁻⁵, no LJ tail correction;
  - density = average over the last half (INDEX.md).
- **Run:** `UCMD_MACHINE_PROFILE=~/.config/ucmd/machine-gpu.toml python3 tools/study/ucmd_study.py
  run studies/2026-11-17_pure-solvent-densities`
- **Caveat:** the LJ tail correction is off, as recorded for Lehnert's setup (decision D2 is
  open). Switching it on would raise the densities by roughly 1 %.
