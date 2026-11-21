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
