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
  `e37-identity`, profile `machine-gpu-mixed-identity.toml`.
