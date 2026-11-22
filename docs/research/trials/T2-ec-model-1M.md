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

## Result (2026-11-22)

All six runs finished 5 ns (queue 8, 2026-11-22 04:02Z). Engine `ucmd 0.0.0 (c9098de83592)`, HIP mixed
precision; analysis ucmd-analysis `a1` at bacb32c. Mean ± SE over the three seeds, last 4 ns.

| per Li⁺ | M0 (LigParGen EC) | M1 (Caleman EC) |
|---|---|---|
| EC carbonyl O within 0.28 nm | **0.444 ± 0.012** (seeds 0.466, 0.440, 0.425) | **0.973 ± 0.010** (0.977, 0.954, 0.989) |
| EMC carbonyl O within 0.28 nm | 3.58 ± 0.02 | 3.29 ± 0.03 |
| PF₆⁻ (P) within 0.28 nm | 0.001 | 0.001 |
| EC carbonyl O within 0.516 nm | 0.95 ± 0.01 | 1.37 ± 0.01 |
| EMC carbonyl O within 0.516 nm | 3.81 ± 0.02 | 3.57 ± 0.02 |
| PF₆⁻ (P) within 0.516 nm | 0.37 ± 0.01 | 0.25 ± 0.02 |
| density, g/cm³ | 1.184 | 1.195 |

**Decision by the rule:** M1 is closer to the DRS bound (2.2 ± 0.1), lies far below it (rule 2
not triggered), and differs from M0 by 0.53 ± 0.02 (about 34 SE; rule 3 not triggered).
**Rule 1: M1 replaces M0 as the EC model.** Awaiting the author's confirmation.

What it does not settle: with M1, Li⁺ still has 1.2 fewer first-shell EC than the bound, and EMC
still makes up about three quarters of the first shell. The deficit stays open for the M2 (RESP2)
and M3 (pair-specific Li⁺–O) steps. The gas-phase QM points the same way: EC − EMC binding is
−6.24 kcal/mol in MP2, against −1.24 for M1.

Density (rule 4, consistency only): Landesfeind's fit (one reading, flagged) gives 1.182 g/cm³ at
1 M and 20 °C; M0 +0.2 %, M1 +1.1 %. The box concentrations are 0.985 (M0) and 0.994 mol/L (M1).

Reported only, not used: κ_NE 0.52 ± 0.04 S/m (M0) and 0.50 ± 0.03 S/m (M1); D(Li⁺) 5.2 and
5.4 × 10⁻¹¹ m²/s. M1 does not change transport at this precision.

### Run length (trials rule 6)

**The pre-registered diagnostic did not work as written.** It required every later 250 ps window
to stay within ±10 % of the final mean. That gave equilibration times of 0, 3.5, 4.5 and 4.5 ns for
four runs and none for two. The ±10 % band sits inside the window noise: after 2 ns, the 500 ps
windows still scatter by 3–18 % (relative SD), and at M0's count of about 0.44 the band is only
±0.044. So the numbers measure noise, not equilibration. For later trials the tolerance should be
set from the window noise, fixed before the runs.

Two **post-hoc** checks, labelled as such (`T2/t2_posthoc.py`, `T2/t2_short.py`, outputs next to
them):

- **Drift.** The count falls from the packed start, about 1.0 (M0) and 1.2 (M1), and levels off
  after 1–1.5 ns. The mean hardly depends on the skip: with 1, 2 or 3 ns skipped it is 0.444,
  0.432 and 0.436 for M0, and 0.973, 0.970 and 0.982 for M1.
- **Shorter runs under the same rule:**

| run from packing | M0 | M1 | verdict |
|---|---|---|---|
| 50 ps | 1.09 ± 0.04 | 1.11 ± 0.04 | rule 3 (wrong) |
| 250 ps | 0.97 ± 0.04 | 1.13 ± 0.09 | rule 3 (wrong) |
| 2 ns, last 1 ns analysed | 0.48 ± 0.03 | 0.98 ± 0.04 | rule 1 |
| 3 ns, last 1.5 ns analysed | 0.44 ± 0.01 | 0.96 ± 0.03 | rule 1 |
| 5 ns, last 4 ns analysed | 0.44 ± 0.01 | 0.97 ± 0.01 | rule 1 |

A 50 ps run from packing would have kept M0 for the wrong reason: the shell had not formed yet.
After equilibration, though, even 250 ps windows separate the models, because M0 ranges over
0.33–0.58 and M1 over 0.78–1.08.

**Length for later 1 M shell runs of this kind:** 3 ns from packing (1.5 ns equilibration,
1.5 ns analysed), or 1.5 ns from an equilibrated state. 5 ns was about 1.7× more than needed.

Commands (workspace root, `HDF5_USE_FILE_LOCKING=FALSE`, ucmd-analysis venv):
`python docs/research/trials/T2/t2_analyze.py T2/t2_result.json`, then the same for `t2_posthoc.py`
and `t2_short.py`.

**Author's decision (2026-11-22):** rule 1 confirmed ("that sounds reasonable, continue with
that"). M1 is the EC model ([ADR 0014](../../decisions/0014-ec-model-m1.md)). The first-shell
deficit goes to trial T6 (Li⁺–carbonyl O correction).
