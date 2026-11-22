# NPT first look (2026-11-17)

- **Question:** with the new C-rescale barostat (engine branch `e27-barostat`, E2.7), which
  density does `opls-aa-carbonates` give for the five 1.0 M mixtures at −10, 20 and 50 °C and
  1 atm? How fast does the box settle from the table's approximate edge?
- **Why:** the NVT scan (`2026-11-17_ec-temperature-scan`) showed 760–2400 bar at the table's
  box edges. The density must come from the force field, at constant pressure, as in Lehnert's
  protocol.
- **Plan:** [study.toml](study.toml). **Contents and progress:** `INDEX.md` (generated; the
  table shows ⟨ρ⟩ over 10–20 ps).

## Protocol

- 5 systems (ucmd-builder `examples/EC/recipes/*_1.0M.toml`) × 3 temperatures = 15 runs.
- Per system: build, one FIRE minimization (NVT box).
- Per run: 20 ps NPT from the minimized box, 1 atm (1.01325 bar). Nosé–Hoover chain
  (τ = 0.1 ps) and C-rescale (τ_p = 1 ps, every 10 steps); 1 fs, no constraints, 1.4 nm cutoff,
  PME to 10⁻⁵.

## Caveats

1. **20 ps is a first look,** not an equilibrated density. The box relaxes within a few τ_p, but
   the slow structural relaxation of the electrolyte takes longer. Lehnert used 3 ns NPT.
2. **No experimental comparison yet.** The Landesfeind 2019 SI densities are not in `../Lit`.
3. **ζ is unset for EC:DMC and EMC:FEC** (unscaled ions), as in the NVT scan.
4. **The barostat is on a review branch:** argon validation against OpenMM in
   `ucmd-engine/validation/npt-argon`.

## Drive it

```sh
python3 tools/study/ucmd_study.py run studies/2026-11-17_ec-npt-first-look --ucmd <engine with E2.7>
python3 tools/study/ucmd_study.py status studies/2026-11-17_ec-npt-first-look
```
