# 0001 — Units: nm, ps, amu, kJ/mol, e, K

- **Status:** accepted 2026-11-11 by the author (PLAN.md §10, item 1).
- **Context:** builder, engine, analysis and every file must share one unit system. The first
  architecture draft proposed Å/eV/fs. GROMACS and our validation oracle, OpenMM, use
  nm/ps/kJ mol⁻¹.
- **Decision:**
  - Internal and file units are nm, ps, amu, kJ/mol, e and K. Configs and logs give pressure
    in bar.
  - Å, eV, hartree and bohr appear only at boundaries (importers, GUI display, external
    providers), with explicit conversion.
  - Physical constants are derived from CODATA 2018 in one module per language.
- **Consequences:**
  - F = m·a needs no conversion factor, because 1 amu·nm²·ps⁻² = 1 kJ/mol.
  - Results compare directly with OpenMM and GROMACS.
  - QC adapters convert from hartree/bohr at the provider boundary.
  - Config keys carry their unit (`timestep_fs`, `cutoff_nm`), and the GUI may display Å.
