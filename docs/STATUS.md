# Status

Last update: 2026-11-13.

- **Gate 0 is approved.** Spec v0.1.0 is tagged `spec-v0.1.0`, and `phase-0` is merged into
  `main` ([gates/gate-0.md §7](gates/gate-0.md)).
- **Gate E1 is approved** (2026-11-12, after the author's hands-on tests). `e1` is merged into
  `main` of ucmd-engine ([gates/gate-e1.md §7](gates/gate-e1.md)).
- **B1 design approved** ([design/B1.md](design/B1.md)); working horse in
  [ADR 0009](decisions/0009-working-horse-force-field.md).
- **Gate E2 core is approved** (2026-11-13, "take the recommendations";
  [gates/gate-e2-core.md §7](gates/gate-e2-core.md)). `e2` is merged into `main` of
  ucmd-engine and of this repo.
  - Milestone M2a: the builder's 1 M LiPF₆ EC:EMC box is minimized and runs NVT with PME and
    Nosé–Hoover chains; single points match OpenMM to 10⁻¹³ (`validation/m2a/REPORT.md`).
  - [ADR 0010](decisions/0010-swappable-hardware.md): bitwise identical on every machine and
    for any thread count.
- **B2a, the GUI preview, is in implementation** (design approved 2026-11-13,
  [design/B2a.md](design/B2a.md)): branch `b2a` of ucmd-builder (from `b1`) and of
  ucmd-engine (graceful stop).
- **After B2a** (PLAN.md §3): the barostat E2.7, then OpenMM on the GPU (E3.7), A1, and the
  first state point.
- **B1a is complete and awaits Gate B1a** ([gates/gate-b1a.md](gates/gate-b1a.md)).
  - The builder makes Lehnert's 1 M LiPF₆ EC:EMC box (7036 atoms) from a recipe; OpenMM runs
    it.
  - EC and EMC agree with OpenMM's reading of the LigParGen originals to 10⁻¹².
  - Branches: `b1` of ucmd-builder, `b1a` of this repo (oracle v1).

## Current

- **Repos:** all four are public in the organization `mines-of-morja`, with CI green.
  - `main` holds what the author has seen or decided.
  - Review branches: `b1` (ucmd-builder, Gate B1a); `b2a` (ucmd-builder and ucmd-engine, the
    GUI preview).
- **Engine CI** tests every branch against the umbrella at a pinned commit (`UMBRELLA_REF` in
  its workflow, now `da27ef7`, which holds the oracle references). New references move this
  pin in the same coordinated update.
- **Waiting for the author:**
  1. Hands-on tests: E2 ([testing.md](testing.md) §8, §8a) and the builder (§7), then Gate
     B1a.
  2. The SI of Landesfeind 2019 (density fit, Table S1 / Eq. S1) in `../Lit`. Until then,
     densities are marked placeholders. It is also the density reference for the transport
     study (PLAN.md §10.12).
  3. Approval to fix the validator's packaging (gate-b1a.md §4.1): its schemas are not in the
     wheel.

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
- **2026-11-12, B1 design:**
  - the working horse is accepted: OPLS-AA with LigParGen EC/EMC, JJ06 Li⁺, CL&P PF₆⁻ and
    ζ = 0.75 (ADR 0009);
  - every other recommendation of §14 is accepted;
  - the author tests hands-on first ("let me run first tests").

- **2026-11-13, Gate E2 core** (gate-e2-core.md §7): approved, "take the recommendations":
  - production throughput from OpenMM on the GPU (E3.7), checked against the reference
    backend; E2.8 later (PLAN.md §10 item 13);
  - the barostat E2.7 first after B2a; forced restarts recorded in the H5MD provenance;
  - the B2a design with every recommendation, including a graceful stop of `ucmd run`.

## Decisions taken by the agent (to review)

- The E2 core implementation choices are in [gate-e2-core.md §4](gates/gate-e2-core.md).
- The thermo column `conserved_kjmol` is renamed to the spec's `conserved_energy_kjmol`.

## Done

- 2026-11-13 — **E2 core (branch `e2` of ucmd-engine)**:
  - E2.R machine-independent arithmetic and the golden-hash test;
  - E2.1 bonded terms with the pair topology; E2.2 LJ with exclusions and 1-4 pairs; E2.3
    Ewald; E2.4 smooth PME;
  - E2.0 `force-field` provider, FIRE and `ucmd minimize`;
  - E2.6 Nosé–Hoover chains, Langevin BAOAB, checkpoint format v2;
  - deterministic threads (design §9); the electrolyte example; milestone M2a.

  Evidence: [gates/gate-e2-core.md](gates/gate-e2-core.md), `validation/m2a/REPORT.md`.
- 2026-11-13 — **B2a design** ([design/B2a.md](design/B2a.md)), for approval.
- 2026-11-12 — **E2 design approved**; ADR 0010 (swappable hardware); study scope (PLAN.md
  §10.12).
- 2026-11-12 — **Gate E1 approved**; `e1` merged into `main` of ucmd-engine.

- 2026-11-12 — **B1a (branch `b1` of ucmd-builder)**:
  - recipe, molecules (RDKit), pluggable force-field sources (`library`, `gromacs-top`, test
    kit);
  - working-horse data (ADR 0009);
  - composition, packing (Packmol wheel, insertion), deterministic packages, CLI, XYZ export.

  Plus oracle v1 (branch `b1a`). Evidence: [gates/gate-b1a.md](gates/gate-b1a.md).

- 2026-11-12 — **B1 design approved**; ADR 0009.
  - Parameters obtained: LigParGen 3.0.1 run for EC and EMC; JJ06 Li⁺ checked against two
    copies; CL&P `il.ff` 2026/10/09 for PF₆⁻.
  - Hands-on guide `docs/testing.md` and the engine example `examples/argon-quickstart`, both
    checked by running them.

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

1. Gate B1a, after the hands-on tests of the builder ([testing.md](testing.md) §7).
2. The Landesfeind 2019 SI for the densities.
3. The validator packaging fix (gate-b1a.md §4.1).
4. PLAN.md §10:
   - item 5: benchmark 1 M LiPF₆ in EC:EMC 3:7 at 20 °C;
   - item 8: agent setup.

## Log

<!-- Newest first. One entry per task:
YYYY-MM-DD — <task ID> — <what changed> — evidence: <tests / report> — next: <task ID> -->

- 2026-11-13 — Gate E2 core — approved; engine `e2` merged (`cbe5f8c`); PLAN v1.5 (priorities
  after B2a) — next: B2a
- 2026-11-13 — M2a — `validation/m2a` (build → single points vs OpenMM → minimize → 10 ps NHC
  → restart → threads → NVE check) — evidence: REPORT.md PASS, engine `6106ba7` — next: Gate
  E2 core, B2a
- 2026-11-13 — fixes found by M2a — pair chunks from the atom count (bitwise restarts),
  exact float parsing of JSON (`float_roundtrip`), XYZ frames flushed; the thermo column
  `conserved_energy_kjmol` — evidence: new tests fail without each fix — next: M2a rerun
- 2026-11-13 — threads — rayon with fixed chunks and fixed-order sums; PME by planes — evidence:
  1/4/16 threads bitwise identical (unit test; LP57 box, 100 NHC steps); 7.5× on 16 threads —
  next: M2a
- 2026-11-13 — E2.6 — Nosé–Hoover chains, Langevin BAOAB, checkpoint v2 — evidence: canonical
  moments within statistics (1 ns; 10 ns `--ignored`), BAOAB harmonic positions exact, bitwise
  CLI restarts — next: threads
- 2026-11-12 — E2.0 — `force-field` provider, FIRE, `ucmd minimize` — evidence: LJ₇/LJ₁₃
  minima; 424-atom box minimized — next: E2.6
- 2026-11-12 — E2.1–E2.4 — bonded terms, nonbonded with exclusions, Ewald, PME — evidence:
  molecules vs OpenMM ≤ 3×10⁻¹⁴, Madelung 9×10⁻¹⁶, LP57 PME box 1.6×10⁻¹³ — next: E2.0
- 2026-11-12 — E2.R — libm, own samplers, scalar FFT, golden hash — evidence: CI reproduces the
  workstation hash — next: E2.1
- 2026-11-12 — E2 design — `docs/design/E2.md` (E2 core → M2a; no spec change; FIRE as
  `ucmd minimize`; NHC, BAOAB; deterministic threads proposed) — next: author approval, then
  E2 core, M2a, B2a
- 2026-11-12 — B1a — builder B1.1–B1.5, B1.8, XYZ export; oracle v1 — evidence: 83 tests, CI
  green; EC/EMC vs OpenMM-GROMACS to 1.5e-12; LP57 box runs in OpenMM — next: Gate B1a; E2
  design
- 2026-11-12 — B1 design approved — ADR 0009; testing guide — next: B1.1
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
