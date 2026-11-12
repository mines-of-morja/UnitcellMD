# Status

Last update: 2026-11-12.

- **Gate 0 is approved.** Spec v0.1.0 is tagged `spec-v0.1.0`, and `phase-0` is merged into
  `main` ([gates/gate-0.md §7](gates/gate-0.md)).
- **E1 is complete and awaits Gate E1** ([gates/gate-e1.md](gates/gate-e1.md)): branch `e1` of
  `ucmd-engine`, 48 tests, argon validated against OpenMM.
- **The B1 (builder) design is ready for review:** [design/B1.md](design/B1.md) on branch `b1`
  of this repo. Its questions are in §14.

## Current

- **Repos:** all four are public in the organization `mines-of-morja`, with CI green.
  - `main` holds what the author has seen or decided.
  - Review branches: `e1` (ucmd-engine, Gate E1) and `b1` (this repo, B1 design).
- **Engine CI** tests every branch against the umbrella at tag `spec-v0.1.0`. A spec change moves
  this pin in the same coordinated update.
- **Waiting for the author:**
  1. Gate E1 ([gates/gate-e1.md](gates/gate-e1.md)). After approval, `e1` is merged into `main`.
  2. The B1 design ([design/B1.md](design/B1.md) §14), in particular:
     - the working-horse force field (§5);
     - LigParGen;
     - densities;
     - the B1a/B1b split that brings the frontend sooner.

## Decisions by the author

- **2026-11-11:**
  - units nm/ps/amu/kJ mol⁻¹ (ADR 0001);
  - GitHub hosting;
  - GUI stack PySide6 + pyvistaqt;
  - cluster deferred, with the rule "local-first, cluster-capable" (ADR 0002).
- **2026-11-12:**
  - organization `mines-of-morja` (commit email morja@mailbox.org) and licence Apache-2.0;
  - the Lehnert 2025 SI goes to `../Lit`.
- **2026-11-12, Gate 0** (gate-0.md §7):
  - every recommendation is accepted (ADRs 0003–0007, the E1 design, the commit identity,
    review branches);
  - the repos are public in `mines-of-morja`;
  - **force-field parameters and forces come from pluggable sources**, with an open-source
    working horse and our own force field as the fallback
    ([ADR 0008](decisions/0008-pluggable-force-field-sources.md));
  - **a frontend early**, once the core stands (PLAN.md §3: M2a, then B2a).

## Decisions taken by the agent (to review)

- The E1 implementation choices are in [gate-e1.md §5](gates/gate-e1.md), for review with
  Gate E1.

## Done

- 2026-11-12 — **Gate 0** — approved by the author.
  - `phase-0` merged into `main`; spec tagged `spec-v0.1.0`; ADRs 0003–0007 accepted.
  - ADR 0008 (pluggable sources).
  - PLAN.md v1.3: B1.3 force-field sources, B2a frontend preview, milestone M2a, E2.2 with both
    combination rules.
- 2026-11-12 — **hosting** — repos public in `mines-of-morja`.
  - `tools/publish-github.sh`: SSH remotes, `--owner`, `--dry-run`.
  - Engine CI reads the umbrella at `spec-v0.1.0`.
- 2026-11-12 — **E1 (branch `e1`)** — the minimal engine, E1.1–E1.12:
  - core types, the provider contract with test kit, harmonic and Lennard-Jones providers,
    neighbour list;
  - velocity Verlet with CSVR;
  - readers with the contract test;
  - thermo/XYZ/H5MD writers;
  - checkpoints with bitwise restarts;
  - `ucmd check|run|singlepoint|export|rerun`;
  - argon validation PASS 8/8 against OpenMM.

  Evidence: [gates/gate-e1.md](gates/gate-e1.md).
- 2026-11-12 — **P0.6** — E1 design (`docs/design/E1.md`).
- 2026-11-12 — **P0.5** — spikes S1–S4 with ADRs 0004–0007 (gate-0.md §2).
- 2026-11-12 — **P0.4** — `ucmd-spec` validator, fixtures, generator, spec CI; 53 tests.
- 2026-11-12 — **P0.3** — spec v0.1 documents and JSON Schemas; ADR 0003.
- 2026-11-12 — Lehnert 2025 SI downloaded to `../Lit`; protocol summarized in
  `docs/lehnert2025-si-notes.md`.
- 2026-11-12 — housekeeping on `main` in all repos: Apache-2.0 + NOTICE, CI on all branches.
- 2026-11-11 — **P0.2** — audit reviewed and extended.
- 2026-11-11 — **P0.1** — workspace and component skeletons.

## Open questions for the author

1. Gate E1 ([gates/gate-e1.md](gates/gate-e1.md)).
2. PLAN.md §10:
   - item 5: benchmark 1 M LiPF₆ in EC:EMC 3:7 at 20 °C;
   - item 7: installs. `libhdf5-dev` is no longer needed; Packmol is still to decide;
   - item 8: agent setup;
   - item 10: placement of the early frontend.

## Log

<!-- Newest first. One entry per task:
YYYY-MM-DD — <task ID> — <what changed> — evidence: <tests / report> — next: <task ID> -->

- 2026-11-12 — B1 design — `docs/design/B1.md`:
  - force-field sources with registry, `library` and `gromacs-top`, and a source test kit;
  - working-horse proposal;
  - composition, packing with the Packmol PyPI wheel, export;
  - B1a/B1b split.

  Evidence: research notes in ADR 0008. Next: author approval, then B1a.

- 2026-11-12 — Gate 0 — approved; `phase-0` merged; `spec-v0.1.0` tagged; ADR 0008; PLAN v1.3
  — evidence: gate-0.md §7; CI green in all four repos — next: B1 design; Gate E1
- 2026-11-12 — E1 — engine E1.1–E1.12 on branch `e1` — evidence: gates/gate-e1.md
  (48 tests; LJ vs OpenMM to 1e-15; bitwise restart; argon 8/8) — next: Gate E1
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
