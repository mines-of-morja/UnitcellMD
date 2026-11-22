# 0013 — Reference frames for t₊

- **Status:** accepted 2026-11-22 by the author ("make the best decision for the project with
  existing conventions that make sense"), on the result of trial T1.
- **Context:**
  - t₊ depends on the reference velocity; κ does not.
  - The experiments and papers we compare with use different frames:
    - Landesfeind & Gasteiger 2019 give Newman's t₊⁰, relative to the solvent velocity;
    - eNMR measures in a cell of fixed volume, so its frame is the volume-average one (Lehnert
      2025, eNMR 0.343 and MD 0.373 at 1 M);
    - MD papers report the barycentric frame (Lehnert SI Table S5) and the solvent frame
      (Table S6).
  - Trial T1 (`docs/research/trials/T1-tplus-frames.md`) ran on the 20 ns pilot:
    - the ion-volume convention changes t₊^VOL by 0.010;
    - the EC and EMC frames differ by 0.45 ± 0.38, which is not resolved;
    - Eq. (2) of `docs/design/A1.5.md` holds to 2e-13.
- **Decision:**
  1. **ucmd-analysis reports t₊ in three frames.** Each is compared only with data in the same
     frame:
     - **SOL** is the headline value against experiment (Newman's t₊⁰, Landesfeind 2019).
     - **VOL** is the value against eNMR.
     - **COM** is the native MD frame. It is compared like for like with other MD (Lehnert Table
       S5), and SOL follows from it.
  2. **SOL** is the velocity of EC + EMC taken as one solvent, **weighted by mass**. Reasons:
     - With this weighting, t₊^SOL = (t₊^COM − ω₋)/ω₀ holds exactly (Eq. 2), so the COM and SOL
       values of any paper convert into each other.
     - Eq. (2) applied to Lehnert's COM fit gives their SOL fit (0.3315 against 0.331).
     - Weighting by moles changes t₊^SOL by 0.016 ± 0.014 on the pilot (T1 addendum). That is
       eight times below the error of a 20 ns run. The production runs report it again.
  3. **VOL** uses the partial molar volume of the salt, ν_e, from the density fit, split by
     convention A: ν₊ = −9 cm³/mol, the published single-ion scale of Marcus & Hefter 2004 (TPTB
     assumption), which includes electrostriction. Convention B (intrinsic volume, ν₊ = 1.1) is
     the stated band.
  4. **Per-solvent frames** (EC, EMC) come with the production runs, not in the first
     implementation step.
  5. **Eq. (2) is a test** in ucmd-analysis. SOL computed from displacements must equal
     (t₊^COM − ω₋)/ω₀ to 1e-9, block by block.
- **Consequences:**
  - A t₊ is never quoted without its frame. A comparison across frames goes through Eq. (2) or
    Eq. (3) of the note.
  - ν_e rests on one reading of the Landesfeind SI. A second reading is still open (STATUS).
