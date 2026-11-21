# T2 — EC model at 1 M: M0 (LigParGen) or M1 (OPLS-AA, Caleman 2012)

## Why it is contested

- For M1: pure EC density −0.17 % (M0 −3.1 %); gas-phase QM layer 0: EC − EMC binding −1.24
  kcal/mol, the right sign (QM −6.24; M0 +0.84); the one-ion shell moves to EC (30.4 ± 3.1 % of the
  first-shell carbonyl O against 17.7 ± 1.4 %, 4 runs each).
- For M0: ΔH_vap of EC +1.7 % (M1 +5.6 %); it is the working horse, consistent with LigParGen EMC.
- Open: whether M1 holds at 1 M, where Li⁺ competes for solvent and PF₆⁻ enters the shell.

## Plan (fixed 2026-11-21, before the runs)

- **Systems:** Lehnert's 1 M box, 47 LiPF₆ (ζ = 0.75), 168 EC, 332 EMC (3:7 w:w), 7036 atoms, start
  edge 4.27 nm. M0: all LigParGen as in the pilot. M1: EC from Caleman 2012 (as in the replica
  study), the rest unchanged.
- **Protocol:** that of `studies/2026-11-21_li-preference-replicas` (NPT 1 atm, 20 °C, 5 ns, 1 fs,
  Nosé–Hoover, C-rescale, PME 1e-5, 1.4 nm, LJ tail), HIP mixed precision. Three packing seeds per
  model (20261124–26). Last 4 ns analysed.
- **Measured:** carbonyl O of EC and EMC and PF₆⁻ (P) within 0.28 nm and within 0.516 nm of Li⁺, per
  run, averaged over the 47 ions; mean ± SE over the three runs. Density. Also reported, **not used
  for the decision:** D of each species, κ_NE.
- **Reference:** about 2.2 ± 0.1 bound EC per Li⁺ from dielectric spectroscopy (Self, Hahn, Persson
  2024, our reading; an upper bound: salt dilution and kinetic depolarization lower the free-EC
  amplitude too). The DRS "bound" EC is the slowed first-shell EC, so the comparison uses the
  first-shell count (0.28 nm).

**Decision rule:**

1. M1 replaces M0 as the EC model if its first-shell EC count is closer to 2.2 than M0's **and** does
   not exceed 2.2 by more than 2 combined standard errors (the reference is an upper bound).
2. If M1 exceeds the bound: neither passes; the next step is the pair-specific Li⁺–O term
   (strategy M3, step 3), not a choice between M0 and M1.
3. If both lie below and the difference M1 − M0 is within 2 SE: the EC charges do not matter at
   1 M; M0 stays (fewer sources), and the shell deficit is passed to the M2 and M3 steps.
4. Density is a consistency check, not a criterion here: M1's box density is reported against
   Landesfeind's fit (one reading, flagged).

**Amendment (2026-11-21, about 22:36Z, during the first 70 ps of the first run, before any result):**
writing the analysis showed that rules 1 and 3 can both apply (M1 closer to 2.2, but within 2 SE of
M0). Then rule 3 takes precedence: a difference that is not resolved does not replace the model.
Analysis script: `T2/t2_analyze.py`.

**Amendment 2 (2026-11-21, 22:40Z, run 1 at 164 ps, before any result):** the author
questioned the 5 ns length (50 ps proposed) and accepted 5 ns on the measured time scales: EMC
stays at a Li⁺ for 260–360 ps continuously and 1.7–1.9 ns with short excursions (replica study),
and the 1 M shell took about 2 ns to form from packing. As a reported diagnostic, not a decision
criterion, the analysis gives the EC first-shell count per Li⁺ in 250 ps windows from the first
frame, and the time after which every window stays within ±10 % of the final-4-ns mean. That time
sets the length of later 1 M shell runs (trials rule 6).

