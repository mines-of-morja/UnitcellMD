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
- **B2a, the GUI preview, is complete and awaits its gate** ([gates/gate-b2a.md](gates/gate-b2a.md)):
  branches `b2a` of ucmd-builder (from `b1`), ucmd-engine (graceful stop) and this repo.
  - `ucmd-build gui`: build a box, look at it, run it with the engine, watch T and E live,
    play the trajectory. Hands-on: [testing.md](testing.md) §9.
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
  - Review branches: `b1` (ucmd-builder, Gate B1a); `b2a` (ucmd-builder, ucmd-engine and this
    repo, Gate B2a).
- **Engine CI** tests every branch against the umbrella at a pinned commit (`UMBRELLA_REF` in
  its workflow, now `da27ef7`, which holds the oracle references). New references move this
  pin in the same coordinated update.
- **Waiting for the author:**
  1. Hands-on tests of the GUI ([testing.md](testing.md) §9), then Gates B2a and B1a together
     (`b2a` contains `b1`). E2 hands-on: §8, §8a.
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

- 2026-11-13 — **B2a, the GUI preview** (branches `b2a`): app shell with undoable recipe edits,
  3D view, components and composition, background build, export, run preview with live plots,
  playback and a graceful stop; engine: graceful stop on SIGINT/SIGTERM, every restart in the
  H5MD provenance. Evidence: [gates/gate-b2a.md](gates/gate-b2a.md).
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

1. Gates B2a and B1a, after the hands-on tests ([testing.md](testing.md) §9 and §7), and
   [gate-b2a.md §5](gates/gate-b2a.md): spec v0.1.1 for the new engine behaviour, live frames.
2. The Landesfeind 2019 SI for the densities.
3. The validator packaging fix (gate-b1a.md §4.1).
4. PLAN.md §10:
   - item 5: benchmark 1 M LiPF₆ in EC:EMC 3:7 at 20 °C;
   - item 8: agent setup.
5. **Decision D1, the solvent parameters** (calculation plan stage B;
   `docs/research/forcefield-survey.md`): stay with LigParGen, test the OPLS-AA atom-type set
   (EC, PC) first, fit QM charges (needs psi4 in a container), or license Maestro.
6. Experimental sources for ΔH_vap and ε (A5, A7). The Caleman 2012 SI compiles them with
   their primary references. For the Li⁺ shell, Lehnert SI Fig. S10 is now the **model**
   reference (1 M, 20 °C, within rs = 5.16 Å: EC ≈ 2.3, EMC ≈ 2.6, PF₆⁻ ≈ 0.7; EC ≈ 47 % of
   the carbonyl O; ours 20 %). An experimental source is still open; stage B counts both ways
   (report §3.4, calculation plan).
7. **Gate E3.7 again:** the molecule-identity fix (ucmd-engine branch `e37-identity`,
   `validation/e37-identity`) passes on the CPU. A short GPU check follows when A4 is done;
   then merge into `e37-openmm`. A4 itself (running since 2026-11-20) uses the old bridge, so its
   trajectories need the repair tool.
8. **The GPU hangs** (11 so far; bridge stuck in `kfd_wait_on_events`). The 10:54Z hang on
   2026-11-20 came at normal temperatures (junction 54–61 °C, 80–92 W). That points to the
   ROCm driver or firmware rather than cooling. The kernel log needs root:
   `sudo dmesg -T | grep -i amdgpu`. Proposals for the study driver: stall timeout 5 min
   instead of 30, checkpoints every 0.1 ns.
9. **κ comparison — answered, to confirm:** Landesfeind 2019 (Eq. 15, Table II) gives
   0.84 S/m at 1 M, 20 °C; Lehnert's Eq. 4 uses formal charges, so our 0.42 ± 0.09 S/m is
   the comparable value: a factor 2 low. κ_NE (0.48 S/m) is low too, so the ions are too slow,
   not too associated (report §3.5).
11. **Force-field strategy** ([forcefield-strategy.md](research/forcefield-strategy.md)):
    levels M1–M4, what is left out on purpose, steps S1–S7. To approve: M1 (OPLS-AA EC types)
    as a test set (S2), and the aim of a ζ from the refractive index (ECC) instead of a κ fit
    (M3).
10. CLAUDE.md lists the GPUs as "RX 580, Radeon VII". The compute card is an MI50 (gfx906);
    correct the text?

## Log

<!-- Newest first. One entry per task:
YYYY-MM-DD — <task ID> — <what changed> — evidence: <tests / report> — next: <task ID> -->

2026-11-20 — research (stage B strategy) — Li⁺ shell compared with Lehnert at his radius
(rs = 5.16 Å, SI Fig. S10): EC 0.98 / EMC 3.91 / PF₆⁻ 0.28 per Li⁺ (EC 20 % of the carbonyl O;
Lehnert ≈ 47 %, same ζ). κ_exp = 0.84 S/m (Landesfeind 2019, Eq. 15) against our 0.42 S/m;
Lehnert's κ uses formal charges. Strategy draft `docs/research/forcefield-strategy.md`
(M1 EC types → M2 QM charges + small LJ refit → M3 ζ from n_D (ECC) → M4 Drude only if needed).
A4: pure EC ended at 1.76 ns (exit −9 after a stall); the 1:1 run continues — evidence: report
§3.4, §3.5 — next: A4 analysis, S1 sources, S2 after approval.

2026-11-20 — E2.9 started (design draft `docs/design/E2.9.md`: problems P1–P8, each with a
check that can fail) — ucmd-analysis `a1`: `dielectric` (A7) and `hvap` (A5), tested against
exact answers (random dipoles; synthetic thermo tables). Rung W, SPC/Fw water: CPU NPT running
(`studies/2026-11-20_water-spcfw-cpu`). Gas phase reproduces equipartition, ⟨U_gas⟩ = 3/2 k_BT
at 0.25/0.5/1 fs. The BAOAB kinetic temperature falls with the timestep (O–H stretch), as
expected. GPU hangs: 3 more in A4 (`kfd_wait_on_events`, normal temperatures). The local
telemetry logger now ends a confirmed hang after 6 min (logged in resume.log), until the
driver fix (P2) can go in after A4 — evidence: analysis tests 23/23 — next: water density vs
the GPU backend, then ε and D on the GPU, Wu 2006 targets once the paper is in ../Lit.

2026-11-20 — A3 pilot done; E3.7 identity defect found and fixed — 20 ns at 20 °C on the GPU
(10 hangs, all recovered; bridge threads stuck in `kfd_wait_on_events`). The OpenMM output
exchanged identical molecules every 84 000 steps (237 events); collective κ, t₊, L_ij were
right, self-diffusion 3.5× wrong. Fix on ucmd-engine branch `e37-identity` (tracker every 250
steps, permutation in checkpoints, emergency checkpoint now keeps its own step) plus
`python -m ucmd_bridge.repair`; the pilot repaired. Results: κ 0.42 ± 0.09 S/m, t₊ 0.29 ± 0.11,
D_Li 4.74 ± 0.20·10⁻¹¹ m²/s, ionicity 0.90 ± 0.19, EMC residence at Li⁺ ≈ 0.6 ns (report §3.5)
— evidence: `ucmd-engine/validation/e37-identity/REPORT.md`, bridge tests 23/23 — next: GPU
check of the fix after A4 (A4 runs on the old bridge and needs the repair), then the gate.

2026-11-20 — A1 done; association corrected — all ten pure-solvent densities: DMC, PC, MP
within 2 % of Table S2; EMC +2.9 % (25 °C) and EC −3.5 % (40 °C, where Table S2's liquid value
applies) fail (report §3.2). The automatic g(r) cutoff stopped at a noise dip inside the Li–P
peak; fixed (ucmd-analysis 6c1e368, test with the real shapes). Corrected: 77 ± 1 % of Li⁺ free
(not 93.5 %), 19.5 ± 0.9 % in contact pairs, 0.25 PF₆⁻ per Li⁺ (report §3.4) — evidence:
analysis tests 17/17 — next: pilot A3 (GPU, until about 06:10Z), then A4.

2026-11-19 — research plan, stage A (A1–A4, B1; D1, D4, D5 tools) — calculation plan and report
draft (`docs/research/calculation-plan.md`, `report/report.md`). Electrolyte NPT to 3 ns:
ρ = 1.1850 ± 0.0008 g/cm³ (−1.4 % vs Lehnert's model); the Li⁺ shell holds 3.7 EMC, 0.4 EC and
0.07 PF₆⁻, with 93.5 % of Li⁺ free. The B1 survey (`docs/research/forcefield-survey.md`) finds
no open copy of Lehnert's Maestro charges; the GROMACS OPLS-AA EC types are the closest open
candidate. ucmd-analysis `a1`: κ self/distinct split, clusters, shell, residence times — evidence:
analysis tests 14/14 (exact Markov-chain and pair-walk cases) — next: transport pilot A3 (GPU,
running), then A4 (queued), decision D1.

2026-11-18 — E3.7 / ADR 0012 / ADR 0011 — mixed precision admitted for thermostatted runs
(`ucmd-engine/validation/e37-precision`: PASS); study driver with watchdog, retry and ready
packages; LJ tail correction on (ADR 0009 amendment) — evidence: REPORT.md files, study tests
10/10 — next: overnight densities and the electrolyte NPT.

2026-11-17 — E3.7 (research plan, GPU first) — OpenMM backend on the Radeon VII through the
machine profile (`ucmd-engine/bridge`, branch `e37-openmm`; design/E3.7.md) — evidence:
conformance 1.3e-8 / 8.7e-8; same-state NVE identical for 0.5 ps; NVT T = 293.0 K after
replacing OpenMM's half-step integrators by the engine's; 22–34 ns/day; bridge tests in CI —
next: pure-solvent densities on the GPU (running), A1 analysis.

2026-11-17 — E2.7 (at the author's request) — C-rescale barostat, isotropic, on engine branch
`e27-barostat` (design/E2.7.md, decisions open for review); NPT study
`studies/2026-11-17_ec-npt-first-look` running (5 mixtures at 1.0 M × −10/20/50 °C, 20 ps) —
evidence: argon density vs OpenMM MonteCarloBarostat −0.15 % (1.0 σ), ideal-gas ⟨V⟩ and Var V,
bitwise NPT restart; engine 97 tests — next: the NPT study's densities; water validation.

2026-11-17 — B1.3 + B2.6 (Gate B2a feedback) — force-field templates DMC, PC, MP, FEC
(LigParGen 3.0.1, as EC/EMC; ADR 0009 amendment, approved by the author); all 35 test boxes in
ucmd-builder `examples/EC` build (8–49 s), pass `ucmd check` and give finite single points.
GUI: **Run…** right after Build (asks where to export the package); **Open run…** and
`start-gui.sh RUN` show any finished run again (plots, playback), also runs from `ucmd run`,
with the output paths taken from its run.toml. — evidence: builder 171 passed, 1 skipped;
headless real-engine check on the 5886-atom EC:DMC:PC 0.5 M box (minimize 41 s, 0.3 ps in 19 s,
reopened run plays 16 frames) — next: the author's hands-on test, testing.md §9 steps 5, 10, 11.

- 2026-11-13 — B2a — GUI preview (B2.1, B2.2, liquid B2.3, export B2.5, B2.6) and the engine's
  graceful stop and restart records — evidence: builder 110 tests (GUI job under Xvfb), engine
  91 tests, real-engine runs through the GUI code, screenshots checked; found and fixed a locale
  bug that zeroed RDKit XYZ coordinates under Qt — next: Gate B2a (hands-on), then E2.7
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
