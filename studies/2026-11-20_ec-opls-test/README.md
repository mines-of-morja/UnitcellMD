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

## Result (2026-11-21)

Both liquids ran 2 ns on HIP (mixed precision, bridge of `e37-identity`; conformance 2.7·10⁻⁷).
Averages over 0.5–2 ns, errors from 10 blocks; ΔH_vap = ⟨U_gas⟩ − ⟨U_liq⟩/N + RT (Caleman's
definition), with the gas-phase error included.

| Set | ρ (g/L) | ΔH_vap (kJ/mol) | ⟨T⟩ (K) | ⟨P⟩ (bar) |
|---|---|---|---|---|
| OPLS-AA (Caleman's parameters) | 1319.2 ± 0.3 | 64.36 ± 0.05 | 312.19 | 6 ± 4 |
| LigParGen (our working horse) | 1280.1 ± 0.3 | 62.00 ± 0.05 | 312.32 | 7 ± 4 |
| Caleman 2012 (OPLS-AA, SI) | 1320.7 | 64.90 | 312.15 | 1 |

- **OPLS-AA:** the engine reproduces Caleman's density to −0.1 % and ΔH_vap to −0.54 kJ/mol
  (−0.8 %). Part of the ΔH_vap gap may come from the bonds: Caleman constrained all of them,
  ours are flexible at 1 fs.
- **LigParGen:** 3.1 % less dense and 2.4 kJ/mol less cohesive than the OPLS-AA set under
  identical settings. This is a property of the parameters, not of the engine.
- **Identity tracking on HIP:** HIP reorders identical molecules too. In the OPLS-AA run the
  tracker corrected 964 labels; the worst match ratio was 0.41 (limit 0.5).
- **Tail convention:** these runs use OpenMM's own count of the LJ tail (fixed in the bridge
  later, `e25-constraints` afbc3b2). For EC it differs from the engine's by 2.7·10⁻⁷ of the
  conformance energy, far below the errors above.
- **Pressure:** the bridge writes the pressure only at barostat evaluations (every 500 steps);
  the other rows are nan.
