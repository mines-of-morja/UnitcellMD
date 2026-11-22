# 2026-11-20 — SPC/Fw water, rung W of the validation ladder (CPU part)

- **Purpose:** design E2.9, rung W. Reproduce a published force field with the CPU reference
  engine: SPC/Fw water (Wu, Tepper, Voth, J. Chem. Phys. 124, 024503 (2006)), pre-approved for
  fixtures.
- **Liquid:** 500 molecules from the builder's `water-box` example. NPT at 298.15 K, 1 atm,
  0.25 ns at 0.5 fs, cutoff 0.9 nm, PME 10⁻⁵, LJ tail correction on (`study.toml`). Run with
  `python3 tools/study/ucmd_study.py run studies/2026-11-20_water-spcfw-cpu`.
- **Gas phase:** `gas/`, for ΔH_vap.
  - `make_gas_package.py` takes the first molecule of the minimized liquid package, with the
    same force field, non-periodic.
  - `run.toml`: 1 ns, Langevin BAOAB, 298.15 K.
  - `run_dt*.toml` repeat it at 0.25 and 1.0 fs.
- **Gas phase, first result (2026-11-20):** ⟨U_gas⟩ agrees with equipartition (3/2 k_BT for
  SPC/Fw's three harmonic coordinates) at every timestep:

  | timestep | ⟨U_gas⟩ (kJ/mol) | kinetic T |
  |---|---|---|
  | 0.25 fs | 3.722 ± 0.068 | 298.3 ± 2.6 K |
  | 0.5 fs | 3.695 ± 0.046 | 293.5 ± 1.0 K |
  | 1.0 fs | 3.737 ± 0.045 | 290.4 ± 1.3 K |

  The kinetic temperature falls with the timestep. That is the known property of BAOAB's
  full-step velocities for fast vibrations, a deficit of about (hω/2)² in the O–H stretch.
  Positions sample correctly, so ΔH_vap is unaffected.
- **Not compared yet:** density, ΔH_vap, ε and D against Wu 2006. That needs the paper in
  `../Lit` for its tables and settings (design E2.9, question 2).
