# Status

Last update: 2026-11-12. **Phase 0 is complete and awaiting Gate 0**
([gates/gate-0.md](gates/gate-0.md)). **E1 is complete, provisionally**, on branch `e1` of
`ucmd-engine` ([gates/gate-e1.md](gates/gate-e1.md)): 48 tests, argon validated against OpenMM.

## Current

- **Branches:**
  - `main` holds only what the author has already seen or decided.
  - `phase-0` (umbrella repo) holds P0.3–P0.6 and is pending Gate 0.
  - `e1` (ucmd-engine, 14 commits) holds the complete E1 engine, pending review together with Gate 0.
- **The author's answers** to gate-0.md §3 and §5 are needed. Silence on an item means "keep".
- **GitHub (private for now):**
  - SSH access works as `PyProgMo`.
  - The author pushed branch `phase-0` of this repo to `PyProgMo/UnitcellMD`. On GitHub it is
    the default branch, and `main` is missing.
  - `ucmd-engine`, `ucmd-builder` and `ucmd-analysis` are local only.
  - Next: choose the owner, create the three repos, run `tools/publish-github.sh --owner
    <owner>`, set `main` as default branch.
  - Engine CI reads the private umbrella repo only with a `UMBRELLA_TOKEN` secret; without it,
    the contract and reference tests are skipped with a warning.

## Decisions by the author

- 2026-11-11: units nm/ps/amu/kJ mol⁻¹ (ADR 0001); public GitHub hosting; GUI stack PySide6 +
  pyvistaqt, pending spike S3; cluster deferred, with the rule "local-first, cluster-capable"
  (ADR 0002).
- 2026-11-12: GitHub organization `mines-of-morja` (email morja@mailbox.org); licence
  Apache-2.0; add the Lehnert 2025 SI to `../Lit`; the agent continues autonomously until the
  author returns.
- 2026-11-12: repos private at first, public once there is enough progress; SSH key for
  GitHub.

## Decisions taken by the agent (to review)

All of these are listed in [gate-0.md §3](gates/gate-0.md). In short:

- Spec formats (ADR 0003).
- H5MD writer (ADR 0004).
- OpenMM oracle (ADR 0005).
- GUI viewer (ADR 0006).
- i-PI conventions (ADR 0007).
- E1 design (docs/design/E1.md).
- Commit identity `Moritz Limbacher <morja@mailbox.org>` (repo-local; the five unpublished
  commits were re-authored, so the personal address never reaches GitHub).
- NOTICE "Copyright 2026 The UnitcellMD Authors".
- Review via branches/PRs.

## Done

- 2026-11-12 — **E1 (provisional, branch `e1`)** — the minimal engine, E1.1–E1.12:
  - core types, the provider contract with test kit, harmonic and Lennard-Jones providers,
    neighbour list;
  - velocity Verlet with CSVR;
  - readers with the contract test;
  - thermo/XYZ/H5MD writers;
  - checkpoints with bitwise restarts;
  - `ucmd check|run|singlepoint|export|rerun`;
  - argon validation PASS 8/8 against OpenMM.

  Evidence: [gates/gate-e1.md](gates/gate-e1.md). Spec corrections found along the way (virial
  strain convention, element enum, E_TOML, author_name) are on `phase-0`.
- 2026-11-12 — **P0.6** — E1 design (`docs/design/E1.md`).
- 2026-11-12 — **P0.5** — spikes S1–S4 with ADRs 0004–0007 (gate-0.md §2).
- 2026-11-12 — **P0.4** — `ucmd-spec` validator, fixtures, generator, spec CI; 53 tests.
- 2026-11-12 — **P0.3** — spec v0.1 documents and JSON Schemas; ADR 0003.
- 2026-11-12 — Lehnert 2025 SI downloaded to `../Lit`; protocol summarized in
  `docs/lehnert2025-si-notes.md`; PLAN updated (force-field sources, production cost risk).
- 2026-11-12 — housekeeping on `main` in all repos: Apache-2.0 + NOTICE, CI on all branches,
  links to `mines-of-morja`, `tools/publish-github.sh`.
- 2026-11-11 — **P0.2** — audit reviewed and extended.
- 2026-11-11 — **P0.1** — workspace and component skeletons.

## Open questions for the author

1. The decisions and requests in [gate-0.md](gates/gate-0.md) §3 and §5. Most important: the
   GitHub owner (organization or personal account), and the force-field source for the
   solvents.
2. PLAN.md §10 items 5 (benchmark), 7 (installs: `libhdf5-dev` is no longer needed; uv
   optional) and 8 (agent setup).

## Log

<!-- Newest first. One entry per task:
YYYY-MM-DD — <task ID> — <what changed> — evidence: <tests / report> — next: <task ID> -->

- 2026-11-12 — E1 (provisional) — engine E1.1–E1.12 on branch `e1` — evidence: gates/gate-e1.md
  (48 tests; LJ vs OpenMM to 1e-15; bitwise restart; argon 8/8) — next: author review of
  Gate 0 + E1, then E2 or B1

- 2026-11-12 — P0.6 — E1 design — next: Gate 0 (E1 provisionally on branch `e1`)
- 2026-11-12 — P0.5 — four spikes — evidence: ADRs 0004–0007 with measured numbers — next: P0.6
- 2026-11-12 — P0.4 — validator + fixtures — evidence: 53 tests green, all 15 error codes
  covered, fixtures reproducible byte for byte — next: P0.5
- 2026-11-12 — P0.3 — spec v0.1 — evidence: ADR 0003; schemas valid Draft 2020-12 — next: P0.4
- 2026-11-12 — housekeeping — licence, CI triggers, URLs, commit identity, publish script —
  evidence: all checks re-run green — next: P0.3
- 2026-11-11 — P0.2 — audit confirmed and amended — evidence: reference-check 46/46 — next: P0.3
- 2026-11-11 — P0.1 — workspace and component skeletons — evidence: all checks green; guard
  rejects injected violations — next: P0.2
