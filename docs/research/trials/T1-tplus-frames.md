# T1 — t₊ frames: ion-volume convention, per-solvent frames, Eq. (2)

Open points 1 and 2 of `docs/design/A1.5.md` §8 (Jo, ucmd-analysis#1), plus a check of the note's
own derivation.

## Plan (fixed 2026-11-21, before the analysis)

- **Data:** the transport pilot, M0, 1 M LiPF₆ in EC:EMC 3:7 (w:w), 20 °C, 20 ns NVT, the last 9500
  frames (from 1 ns on), as in `transport.repaired.json` (`studies/2026-11-19_transport-pilot`,
  `trajectory.repaired.h5`). Five blocks and the fit window
  of `transport()`, formal charges.
- **Computed per block:** t₊ in the COM frame (as `transport()`); t₊ with the reference velocity of
  (i) the solvent centre of mass, EC + EMC together (SOL), (ii) EC alone, (iii) EMC alone; and t₊^VOL
  from Eq. (3) of the note, t₊^VOL = (1 − c_e ν_e) t₊^SOL + c_e (ν_e − ν₊), with
  - convention A: ν₊ = −9 cm³/mol (Marcus & Hefter, TPTB scale, PC);
  - convention B: ν₊ = 1.1 cm³/mol (intrinsic volume);
  - ν_e = 55.7 cm³/mol at 20 °C from the Landesfeind density fit (ledger; one reading, flagged).
  c_e is the box's own concentration, block by block.

**Decision rules:**

| question | test | rule |
|---|---|---|
| (a) convention A or B | Δ_AB = mean \|t₊^VOL(A) − t₊^VOL(B)\| | Δ_AB < 0.015 (half the production target, ±10 % of t₊ ≈ ±0.03): the convention does not matter at our precision; A is central (the published single-ion scale, with electrostriction), B the stated band. Δ_AB ≥ 0.015: no MD test can pick a convention; the author decides from the literature. |
| (b) per-solvent frames now or later | t₊^EC − t₊^EMC against its block standard error | resolved (> 2 SE): per-solvent frames go into the first implementation step. Not resolved: the first step implements COM, SOL and VOL; per-solvent frames follow with the production runs, which have about 3× smaller errors. |
| (c) is Eq. (2) right | t₊^SOL computed directly from displacements against (t₊^COM − ω₋)/ω₀, block by block | Eq. (2) is linear, so the two must agree to round-off (< 1e-9). If not, the derivation in §2.1 of the note is wrong and the note goes back to Jo before approval. |

## Result (2026-11-21)

Setup check: with frames 501–10 000 the script reproduces the pilot's published
t₊^COM = 0.2859 ± 0.1103 exactly (`transport.repaired.json`), so blocks, window and estimator are
the pilot's. Mass fractions ω₋ = 0.1206, ω₀ = 0.8736; box concentration 0.987 mol/L.

| frame | t₊ (mean ± SE over 5 blocks) |
|---|---|
| COM | 0.286 ± 0.110 |
| SOL (EC + EMC centre of mass) | 0.189 ± 0.126 |
| SOL from Eq. (2) | 0.189 ± 0.126 |
| EC | 0.51 ± 0.35 |
| EMC | 0.05 ± 0.12 |
| VOL, convention A (ν₊ = −9) | 0.243 ± 0.119 |
| VOL, convention B (ν₊ = 1.1) | 0.233 ± 0.119 |

**Decisions by the rules above:**

- **(a)** Δ_AB = 0.0100 < 0.015. The convention does not matter at our precision: **A is central,
  B the stated band** (Jo's proposal stands).
- **(b)** t₊^EC − t₊^EMC = 0.45 ± 0.38 (1.2 SE): **not resolved.** The first implementation step
  is COM, SOL and VOL; per-solvent frames follow with the production runs. This differs from the
  note's proposal (§8.2). The EC frame is the noisiest: 168 EC molecules carry the reference for
  47 ions, and the block values range from −0.27 to 1.74.
- **(c)** Largest block difference between SOL computed directly and from Eq. (2): 2 × 10⁻¹³.
  **The note's derivation is correct.**

Transport values, reported and not used for any decision: t₊^SOL is the frame of Landesfeind's
cell-model parameters (0.16 measured, 0.22 fit at 1 M, 20 °C); t₊^VOL that of Lehnert (0.373 MD,
0.343 eNMR). With 20 ns, our errors (±0.12) cannot separate any of them.

Command: `HDF5_USE_FILE_LOCKING=FALSE ucmd-analysis/.venv/bin/python
docs/research/trials/T1/t1_frames.py <pilot>/out/trajectory.repaired.h5 OUT.json 501`
(ucmd-analysis `a1` at bacb32c; output `T1/t1_result.json`).

**Addendum (2026-11-22, not pre-registered):** the SOL frame weighted by moles of solvent
instead of mass (EC weight 0.336 instead of 0.300). t₊^SOL 0.206 ± 0.134 instead of
0.189 ± 0.126; difference 0.016 ± 0.014, eight times below the error. Only the mass weighting
satisfies Eq. (2) exactly. Script `T1/t1_sol_weighting.py`, output `T1/t1_sol_weighting.json`.

**Author's decision (2026-11-22):** the author delegated the choice ("make the best decision
for the project with existing conventions that make sense"). Decisions (a)–(c) stand. The
frame convention is recorded in [ADR 0013](../../decisions/0013-transference-frames.md):
- SOL, weighted by mass, is the headline against experiment;
- VOL, convention A with B as the band, is compared with eNMR;
- COM is compared with other MD.
