# 2026-11-20 — rung EC: pure EC with the OPLS-AA atom types (a test, not decision D1)

- **Purpose:** design E2.9, P6.
  - Does pure EC at 39 °C reach Caleman 2012's OPLS-AA results (ρ = 1320.7 g/L, ΔH_vap =
    64.90 kJ/mol, SI) with our engine?
  - How far is the current LigParGen set from them under identical settings?
  - Approved as a test by the author on 2026-11-20.
- **Parameters:** virtualchemistry.org `ff/OPLS.zip`: `96-49-1.top` with `oplsaaff.itp`. The
  download has no stated licence, so the files stay in `external/` (git-ignored).
  - `make_explicit_itp.py`: OpenMM's GROMACS reader does the type lookup and writes every
    parameter explicitly, so the builder's `gromacs-top` source can read it.
  - `compare_original.py`: our built package (`checks/ec_oplsaa_1.toml`) against OpenMM on the
    **original** files, term by term in vacuum. PASS, worst relative difference 1.2·10⁻¹⁵
    (2026-11-20).
- **Liquid:** `study.toml`, both sets, 1000 molecules, NPT 1 bar, 312.15 K, 2 ns on the GPU.
  Settings follow Caleman §2.3 (1.1 nm LJ cutoff with tail correction, PME, τ_T 1 ps, τ_p 5 ps,
  compressibility 5·10⁻⁵ bar⁻¹).
  - Our engine has no constraints yet; Caleman constrained all bonds (LINCS).
- **Gas phase:** `gas/`, one molecule, Langevin, 10 ns, 312.15 K.
  - ⟨U_gas⟩ = 13.10 ± 0.05 kJ/mol (OPLS-AA), 73.97 ± 0.03 kJ/mol (LigParGen). Absolute values
    differ between the sets; only ΔH_vap compares.
