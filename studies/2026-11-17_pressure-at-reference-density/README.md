# Pressure at the reference density (2026-11-17)

- **Question:** is `opls-aa-carbonates` right at the reference density? If it were as good as
  Lehnert's force field, the equilibrium pressure at that density would be about 1 bar.
- **Why:** the 10 ps NVT runs showed 800–1500 bar, but still falling (6500 → 800 bar over
  10 ps). The start (~8000 bar) is an artefact of starting from a minimized structure: all bonds
  at their rest length, so the atomic kinetic pressure (~+3500 bar) is not yet balanced by bond
  tension. The slow fall is the liquid's structure relaxing. Only the plateau says something
  about the force field.

## Systems (recipes/ in this folder)

| system | reference density | source |
|---|---|---|
| `ec-emc_3-7w_1.0M`: 47 Li, 47 PF6, 168 EC, 332 EMC, L = 4.27 nm | 1.205 g/cm³ at 20 °C | Lehnert 2025: ion counts tuned at 20 °C until the simulated concentration was 1.0 M, i.e. V = 78.05 nm³ (their force field's density) |
| `emc_pure`: 500 EMC, L = 4.4126 nm | 1.006 g/cm³ | Lehnert 2025 SI Table S2 (manufacturer density; its temperature is not stated, likely 20–25 °C, ±0.5 %) |

## Protocol

100 ps NVT at 20 °C from the minimized box; settings of Lehnert's SI S1.1 (1 fs, Nosé–Hoover
τ = 0.1 ps, 1.4 nm cutoff, PME to 10⁻⁵), no LJ tail correction in the run. The tail
correction's pressure (about −160 bar for the electrolyte) is evaluated separately.

## Reading the result

- Plateau ⟨P⟩ near 0 (within ±150 bar): the force field's density is right.
- ⟨P⟩ of several hundred bar: the force field's density is too low by about κ_T·⟨P⟩ (a few
  percent for κ_T of order 10⁻⁴ bar⁻¹).
- **Attribution:**
  - pure EMC high as well → the solvent parameters (LigParGen) are off;
  - only the electrolyte high → the ion side is off (Li⁺, PF₆⁻, ζ).
