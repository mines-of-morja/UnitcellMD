# 2026-11-20 — rung W: SPC/Fw water as in Wu, Tepper, Voth 2006 (GPU)

- **Purpose:** design E2.9, P1/P3/P4. Reproduce Table II of Wu et al., J. Chem. Phys. 124,
  024503 (2006): ρ 1.012 g/cm³, ΔH_vap 10.72 kcal/mol, D 2.32·10⁻⁵ cm²/s, ε 79.63,
  ⟨r_OH⟩ 1.0310 Å, ⟨θ⟩ 107.69°, ⟨μ⟩ 2.39 D. Their bracketed values are standard deviations.
- **Their settings (§II B), reproduced:** 298.16 K, 1 atm, 9 Å LJ cutoff with
  long-range corrections, PME 10⁻⁶, 1 fs, 6.5 ns, frames every 0.5 ps, first 0.5 ns skipped.
- **Box size:** 512 molecules instead of their 216. The 1.86 nm box of 216 molecules is smaller
  than twice the engine's cutoff plus neighbour-list skin (2 × 1.1 nm). D therefore depends on
  the box size: both values are compared after the Yeh–Hummer correction with Wu's η (0.75 cP).
- **Definitions:**
  - Wu's ΔH_vap is −⟨E⟩/N + RT, without a gas-phase term (`hvap` with a zero gas energy).
  - ε from the total dipole with conducting boundaries (their Eq. 3).
- **Parameters:** checked against Table I on 2026-11-20 (in spec units: k_b 443153.3808,
  k_a 317.5656, σ 0.3165492 nm, ε 0.6502995 kJ/mol, q ∓0.82/0.41).
- **Also the GPU check of the identity fix (P1):** runs with the bridge of branch
  `e25-constraints`, profile `machine-gpu-double-identity.toml` (HIP, double precision; the
  mixed-precision profile was refused at start-up, see Result).

## Result (2026-11-21)

One run, 6.5 ns in 2 h 10 min (72 ns/day, alone on the MI50), HIP double precision, bridge
`e25-constraints` 2ea7e82; conformance with the engine 6.5·10⁻⁸ (energy), 7.4·10⁻⁸ (forces);
**0 label corrections, no hang**. Averages over 0.5–6.5 ns; errors from blocks.

| Property | Ours | Wu 2006, SPC/Fw | |
|---|---|---|---|
| ρ (g/cm³) | 1.0072 ± 0.0002 (10 blocks) | 1.012 | −0.5 %; see below |
| ΔH_vap (kcal/mol) | 10.72 (44.83 kJ/mol; ⟨U⟩/N = −42.355 ± 0.014 kJ/mol, RT = 2.479) | 10.72 ± 0.12 | equal |
| D, 512 molecules (10⁻⁵ cm²/s) | 2.42–2.46 ± 0.04 | — | box differs |
| D∞, Yeh–Hummer, η = 0.75 cP | 2.76–2.79 ± 0.04 | — | |
| D expected for Wu's 216-molecule box | 2.77 − 0.445 ≈ 2.32 | 2.32 ± 0.05 | equal, if Wu's D is uncorrected |
| ε | 80.7 (blocks: 77.6 ± 2.7) | 79.63 ± 1.62 | within errors |
| ⟨r_OH⟩ (Å) | 1.0310 | 1.0310 | equal |
| ⟨θ⟩ (deg) | 107.70 | 107.69 | equal |
| ⟨μ⟩ (D) | 2.394 | 2.39 | equal |

- **Equal to four digits:** the intramolecular geometry and the dipole, which tests the
  parameters and the flexible-bond integration.
- **ΔH_vap** uses Wu's definition (−⟨U⟩/N + RT). With Caleman's definition (gas-phase
  U = 3.684 kJ/mol added) it is 48.52 kJ/mol = 11.60 kcal/mol; the two are not comparable.
- **D:** the 216-molecule value of Wu is compared through the Yeh–Hummer correction for their
  box (L = 1.855 nm: +0.445·10⁻⁵ cm²/s with η = 0.75 cP). That assumes their D is uncorrected;
  I found no correction mentioned in their text. The correction uses Wu's η; it is redone with
  our own η when the viscosity run is analysed (`2026-11-20_water-spcfw-viscosity-cpu`). The
  ratio of fit windows and block numbers changes D by ≤ 0.04.
- **ε:** the estimate from all frames (80.7) is above the block mean (77.6 ± 2.7); fluctuations
  slower than a block are lost in blocks, and ε converges slowly (Wu report relaxation up to
  2 ns). Within either, Wu's 79.63 is inside one standard error.
- **Density, not explained:** 1.0072 here, and 1.0079 ± 0.0012 (engine, 0.5 fs) and
  1.0089 ± 0.0011 (HIP, 0.5 fs) in the 500-molecule twin runs, all 0.4–0.5 % below Wu's 1.012.
  Wu's value is for 216 molecules; the difference is larger than our errors. Candidate
  causes not yet tested: system size, their barostat, their PME and long-range corrections.
  The potential energy depends on the time step as well: ⟨U⟩/N is −42.69 kJ/mol at 0.5 fs
  (twin) and −42.35 kJ/mol at 1 fs, so ΔH_vap would be 10.80 kcal/mol at 0.5 fs.
- **Pending:** Green–Kubo viscosity of the CPU run (η ≈ 0.75 cP expected at 300.2 K).
