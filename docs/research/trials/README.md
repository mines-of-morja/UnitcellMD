# Trials: contested choices decided by a test

A trial settles a choice that is not a clear improvement: two (or more) ways are defensible and
the literature does not decide between them. Both ways are run, and a test fixed in advance picks
one. Author's request, 2026-11-21.

## Rules

1. **Written before the runs.** Question, options, test, metric and decision rule go into
   `T<n>-<name>.md` and are committed before any run starts. The commit time is the record.
2. **The test never uses transport agreement.** κ, t₊ and D are our test data (publication.md,
   rule 1). Choosing the option that matches them is fitting by another name. A decision may use:
   - whether the difference matters at our precision (if not, the simpler or standard option
     wins and the other becomes a stated band);
   - internal consistency (an identity that must hold, a sum rule, frame invariance);
   - data on the fit side of the ladder: QM, pure-liquid density and ΔH_vap, structure (shell
     composition against dielectric, Raman, NMR).
   Transport numbers from the runs are reported, never used to choose.
3. **Both options run under the same protocol**, with replicas where the noise needs them.
4. **Results go into the same file**, below the plan, with commands and versions; the losing
   option stays documented (rule 5 of publication.md).
5. **The author confirms the decision.** A convention that sticks becomes an ADR.
6. **Discussion:** each trial has a GitHub issue labelled `discussion` in UnitcellMD, where
   anyone, Jo and his agents included, can argue for another option or another test before the
   runs. After the runs, the issue gets the result and is closed when the author confirms.

## Trials

| ID | question | needs | state |
|---|---|---|---|
| [T1](T1-tplus-frames.md) | t₊ frames: ion-volume convention; per-solvent frames; is the note's Eq. (2) right? | pilot trajectory (CPU) | planned |
| [T2](T2-ec-model-1M.md) | EC model M0 (LigParGen) or M1 (OPLS-AA, Caleman) at 1 M | 6 GPU runs | planned |
| [T3](T3-density-protocol.md) | transport at the model's own density (NPT) or at the measured density (NVT) | second reading of the Landesfeind SI | planned |
| [T4](T4-slow-ions.md) | slow ions: solvent too viscous, or Li⁺ bound too strongly | spec 0.1.1 (pressure tensor), author | planned |
| [T5](T5-charge-scaling.md) | ion-charge scaling ζ fitted to κ, or from the refractive index | n_D sources (UnitcellMD#3) | planned |
