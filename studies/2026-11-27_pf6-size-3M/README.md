# How much of the salt's excess volume is the anion's size? (PF₆⁻ size map, 3 M)

- **Label:** exploration, a map, not a fit. No parameter is chosen from it. Plan, reading rule and `analyze.py` are committed
  before the runs.
- **Why:** SC-4 failed on the concentration slope. Read as an apparent molar volume
  (`docs/research/density-c-T/apparent_volume.py`), the model's LiPF₆ takes **71.9 cm³/mol against 55.7** (Landesfeind 2019,
  20 °C), 16.2 cm³/mol too much, while its solvent is 3.2 % too dense. The Li⁺ size does not move the density (1 M scan), so the
  anion is the next candidate: PF₆⁻ is the larger ion and most of the salt's own volume.
- **Requested by:** the author, 2026-11-27 noon ("yes, continue with your work as u suggested"), after the proposal of a PF₆⁻
  size map with probe values only.
- **Submitted only after** the 3 M ζ map (`studies/2026-11-27_density-slope-3M`) has been read, as proposed.

## Runs

The minimized 3 M M1 box of SC-4 (8004 atoms) with the σ of both PF₆⁻ atom types (P and F, CL&P) **× 0.95 and × 1.05**
(`make_packages.py`, the change of the scan's `change_sigma_li` applied to PF₆⁻). With the geometric rule PF₆⁻–PF₆⁻ pairs scale by
the factor, PF₆⁻–other pairs by its square root. The unchanged run is SC-4's 3 M point. Protocol of SC-4 (0.5 fs, so that the
baseline is the same protocol, ADR 0017 item 3): 3 ns, first 1 ns skipped, 20 °C. Two runs, about 3.5 h of GPU.

## Reading rule (fixed before the runs)

1. **ΔV_φ** of each probe against SC-4's 3 M point, each at its own concentration, with the model's solvent density (the PF₆⁻ size
   does not change the solvent). The × 0.95 probe removes the fraction −ΔV_φ / 16.2 of the excess: at least 0.75 **carries most of
   the excess**, 0.25 to 0.75 **carries part of it**, less **carries little**. × 1.05 is reported for the sign and the curvature.
2. A run counts only if it settled (SC-4's criterion: halves within 0.3 %).
3. **Not judged:** whether a size "fixes" SC-4, and transport. A smaller anion also changes D and κ; those are test data
   (trials rule 2) and are not looked at here.

**Prediction (before the runs):** a rough hard-sphere estimate of PF₆⁻ (P–F 0.16 nm plus half the F σ) gives about 75 cm³/mol;
5 % smaller F and P σ shrink it by about 7 %, and the PF₆⁻–solvent contacts shrink by only half as much, so ΔV_φ(× 0.95) ≈ −3 to
−6 cm³/mol: **part of the excess** (20–35 %). If so, the anion size alone is not the answer, and the excess is mainly weak
ion–solvent attraction (ζ), which the 3 M map tests.
