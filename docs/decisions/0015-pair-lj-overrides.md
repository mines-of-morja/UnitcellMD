# 0015 — Per-pair Lennard-Jones overrides in the system package (spec 0.1.2)

- **Status:** proposed 2026-11-22, awaiting the author.
  - The author asked that trial T6 option B not be held up ("B should not be held up once the
    clusters are done").
  - The spec change itself needs the author's approval (CLAUDE.md).
- **Context:**
  - Spec 0.1 derives every LJ pair from the atom types through one combination rule.
  - T6 option B needs its own σ and ε for two pairs (Li⁺–O carbonyl of EC and of EMC).
  - ADR 0008 §3 names this as the case that needs a spec extension.
- **Decision (proposed):**
  - `forcefield.pair_overrides` is a list of `{types: [a, b], sigma_nm, epsilon_kjmol,
    description?}`.
  - For every LJ-interacting pair of those types, including 1-4 pairs before their scaling, it
    replaces the combination rule. The tail correction uses it too.
  - Spec 0.1.2 is backwards compatible. Old readers reject such packages, so they fail closed.
  - The builder applies overrides as a recorded transform with a mandatory citation.
  - Details, files and acceptance tests: `docs/design/S0.1.2-pair-lj-overrides.md`.
- **Consequences:**
  - NBFIX-type ion corrections become ordinary packages. They run in the CPU engine and the
    OpenMM bridge alike, not only as an external provider (ADR 0008 §7).
  - Every reader changes together (spec §9). Packages without overrides behave exactly as
    before.
  - Mixing force-field families is expressible but not automated. That would be a separate
    decision.
