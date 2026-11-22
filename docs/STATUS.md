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
  2. The SI of Landesfeind 2019 (density fit, Table S1 / Eq. S1) in `../Lit`. Jo's agent entered
     the fit from its own copy of the SI (ledger `landesfeind2019_density_fit_ec_emc_3_7`:
     ρ(1 M, 25 °C) = 1.176 g/cm³, our boxes 1.202); a second reading from the PDF in `../Lit` is
     still needed before the placeholders are replaced. It is also the density reference for
     the transport study (PLAN.md §10.12).

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
2. The Landesfeind 2019 SI for the densities (values entered from Jo's copy, 2026-11-21; the PDF
   itself is still wanted for a second reading).
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
   the carbonyl O; ours 20 %). **Experimental source found (2026-11-21):** dielectric
   spectroscopy, Self, Hahn, Persson, Energy Environ. Mater. 7, e12494 (2024, CC BY): the free-EC
   amplitude drops from 14.1 to 5.3 at 1 M, which we read as ≈ 2.2 bound EC per Li⁺ (an estimate,
   strategy §8). Stage B counts both ways (report §3.4, calculation plan). For ../Lit, if wanted:
   that paper (open) and Hall, Self, Dahn, J. Phys. Chem. C 119, 22322 (2015) (paywalled; neat
   EMC ε).
7. **Gate E3.7 again:** the molecule-identity fix (ucmd-engine branch `e37-identity`,
   `validation/e37-identity`) passes on the CPU. A short GPU check follows when A4 is done;
   then merge into `e37-openmm`. A4 itself (running since 2026-11-20) uses the old bridge, so its
   trajectories need the repair tool.
8. **The GPU hangs** (11 so far; bridge stuck in `kfd_wait_on_events`). The 10:54Z hang on
   2026-11-20 came at normal temperatures (junction 54–61 °C, 80–92 W). That points to the
   ROCm driver or firmware rather than cooling. The kernel log needs root:
   `sudo dmesg -T | grep -i amdgpu` (2026-11-20: the ring buffer had rotated, full of UFW messages). **Kernel journal
   since boot (2026-11-19 11:18):** not one amdgpu/kfd line after initialisation, despite about
   15 hangs: no ring timeout, no reset, no VM fault. The hangs are invisible to the driver. The
   card runs the **Radeon VII VBIOS 113-D3600200-106** (RAS EEPROM unreadable, I2C NAK, as usual
   for a flashed MI50), so its top states 1749–1801 MHz lie above the MI50's own peak clock. **Test since 14:31Z:** top sclk states locked out (manual, states
   0–5, max 1683 MHz; about 968 instead of 1068 mV, 75 instead of 85 W), after hangs every
   ~10 min at 1801 MHz and normal temperatures. **Result so far: not the cause.** Hangs at
   14:47Z (1546 MHz) and 15:22Z (1683 MHz). In all 9 hang snapshots the GPU drops from 60–90 %
   busy to 0 % within 5 s and stays idle while the bridge waits in `kfd_wait_on_events`: the
   work finishes, the completion event never reaches the host. That points to the ROCm OpenCL
   runtime or KFD (a lost signal), not to voltage margin. Options: a short stall timeout with
   frequent checkpoints (cheap), OpenMM's HIP platform instead of OpenCL, another ROCm version. Revert: `echo auto > power_dpm_force_performance_level`;
   lost on reboot. Proposals for the study driver: stall timeout 5 min
   instead of 30, checkpoints every 0.1 ns.
9. **κ comparison — answered, to confirm:** Landesfeind 2019 (Eq. 15, Table II) gives
   0.84 S/m at 1 M, 20 °C; Lehnert's Eq. 4 uses formal charges, so our 0.42 ± 0.09 S/m is
   the comparable value: a factor 2 low. κ_NE (0.48 S/m) is low too, so the ions are too slow,
   not too associated (report §3.5).
11. **Force-field strategy** ([forcefield-strategy.md](research/forcefield-strategy.md) §8):
    M1 and the M3 trial approved (2026-11-20); QM method delegated (Psi4 container, RESP2,
    cluster references). To confirm before S6: the pass criteria for ζ_ECC (κ ±15 %, κ maximum
    ±0.2 M).
12. **Parked (author, 2026-11-21: not the edge of the project; later):** structured failure
    records. The engine writes a clear text error, but the study driver cannot tell a lasting
    failure from a transient one: it retried the Wu water run 40 times overnight on an
    identical conformance failure, and it leaves a stale `reason` in status.json after a
    successful fresh restart (EC rung runs: done, exit 0, "engine exit 1"). Proposal when
    resumed: `out/failure.json` (category, step, diagnostics, last checkpoint, provider) with
    per-category exit codes; the driver skips lasting failures. Related: the SPC/Fw water
    conformance failure (4.1–4.7e-6 against 1e-6) is resolved without loosening the
    tolerance; see the log entry of 2026-11-21 (LJ tail count; water runs in double
    precision).
10. CLAUDE.md lists the GPUs as "RX 580, Radeon VII". The compute card is an MI50 (gfx906)
    flashed with the Radeon VII VBIOS, hence the name; correct the text?

## Log

<!-- Newest first. One entry per task:
YYYY-MM-DD — <task ID> — <what changed> — evidence: <tests / report> — next: <task ID> -->

2026-11-23 — spec 0.1.2 per-pair LJ overrides implemented — **ADR 0015** accepted (the author
delegated Q1–Q3: own version 0.1.2, overrides include 1-4 pairs, recipes name package types).
Spec, validator, oracle (umbrella main); engine and bridge (branch `s012-pair-overrides`, from
`e37-openmm`); builder (branch `s012-pair-overrides`, from `b2a`). — evidence: acceptance tests
A1–A9 in `docs/design/S0.1.2-pair-lj-overrides.md` §8 (kob-andersen-500 against OpenMM at 1e-15;
T6 clusters, spec path = fit to 6e-13 kJ/mol). Finding: OpenMM's tail correction counts pairs
differently from the engine for several atom types (O(1/N)). — next: T6 functional choice and
clusters; author: tag spec 0.1.1/0.1.2 (the builder's validator pin), merge order of the branches.

2026-11-22 — T6 stage 1 amended; spec 0.1.2 proposed — Psi4 1.9.1 has no analytic gradients
for VV10 functionals, so ωB97M-V enters as single points on ωB97X-D geometries (T6 Amendment 3;
`cluster_dft.py --geometries`). The author asked that option B not wait: per-pair LJ overrides
are proposed as spec 0.1.2. — evidence: `docs/design/S0.1.2-pair-lj-overrides.md`, ADR 0015
(proposed) — next: functional choice, then the five clusters; author: Q1–Q3 of the design.

2026-11-22 — T2 decided, T6 planned — **ADR 0014** (author: "that sounds reasonable"): EC
from the OPLS-AA types of Caleman 2012 (M1) replaces LigParGen EC in the working horse. Trial
T6 (#11), first-shell correction: one Li⁺ σ (A, ECC-R) or a Li⁺–O(carbonyl) pair term (B),
fitted to DFT Li⁺(EC)ₙ(EMC)₄₋ₙ clusters, tested in the liquid at 3 ns. — evidence:
`docs/decisions/0014-ec-model-m1.md`, `docs/research/trials/T6-li-carbonyl-correction.md` —
next: T6 stage 1 (DFT protocol check on the single complexes); author: spec per-pair LJ
overrides before B's liquid runs.

2026-11-22 — trial T1 decided — **ADR 0013** (the author delegated the choice): t₊ is
reported in SOL (headline against experiment, Newman's t₊⁰), VOL (eNMR; convention A, B as the
band) and COM (other MD). SOL is the mass-weighted EC + EMC velocity: Eq. (2) holds exactly, and
mole weighting changes t₊ by 0.016 ± 0.014. Per-solvent frames come with the production runs. —
evidence: `docs/research/trials/T1-tplus-frames.md`, `T1/t1_sol_weighting.json` — next: Jo
implements COM/SOL/VOL in ucmd-analysis#1.

2026-11-22 — rung W done (SPC/Fw water against Wu 2006); results folder — one 6.5 ns NPT run on the
GPU (HIP double, 512 molecules) against Table II: ⟨r_OH⟩ 1.0310 Å, ⟨θ⟩ 107.70°, ⟨μ⟩ 2.394 D,
ΔH_vap 10.72 kcal/mol (Wu's definition) all equal; ε 80.7 (blocks 77.6 ± 2.7) against 79.63; D in
Wu's box 2.31 (2.31–2.35) against 2.32 after Yeh–Hummer with our own Green–Kubo η = 0.768 ± 0.015
mPa·s (Wu 0.75). **Density 1.0072 ± 0.0002 against 1.012 (−0.47 %), unexplained.** New home for
finished comparisons: `docs/research/results/<name>/` (summary PDF, derived data, analysis and
build scripts, literature ledger; README there). First entry: `wu2006-spcfw-water`, label
exploration, with `Wu_et_al_water_summary.pdf`. Evidence: that folder's `data/results.json`.

2026-11-22 — trial T2 (EC model at 1 M) — **done, awaiting the author:** by the pre-registered
rule 1, M1 (Caleman EC) replaces M0. EC carbonyl O within 0.28 nm of Li⁺: 0.97 ± 0.01 (M1)
against 0.44 ± 0.01 (M0), DRS bound 2.2 ± 0.1. The deficit of 1.2 EC goes to M2/M3. Density
+1.1 % (M1) and +0.2 % (M0) against the Landesfeind fit (one reading); κ unchanged (reported
only). Run length: the pre-registered ±10 % diagnostic is noise-limited (reported as such);
post hoc, the shell settles after 1–1.5 ns, and 50 ps or 250 ps runs would have given the wrong
verdict, while 3 ns reproduces 5 ns. Later 1 M shell runs: 3 ns from packing, 1.5 ns from an
equilibrated state. — evidence: `docs/research/trials/T2-ec-model-1M.md`, `T2/*.json` —
next: author confirms T1 and T2; then T3 (Landesfeind SI) or M2.

2026-11-21 — contributions of Jo and Copilot reviewed — **merged into b2a** (drafts, not
approved): A1.5 design notes for t₊ in the SOL and VOL frames and for the Green–Kubo cross-check
(`docs/design/A1.5.md`, `A1.5-green-kubo.md`) with five ledger entries; the Lehnert SI values and
the COM→SOL conversion (0.3315 against their fit 0.331) re-checked here, the entries from papers
not in `../Lit` flagged for a second reading. **Not merged:** the Copilot i-PI provider
(ucmd-engine PR #2). Against ASE's real `SocketClient` it times out in `initialize`: the server
waits for the client to speak first, where i-PI has the server ask (STATUS, POSDATA, GETFORCE,
FORCEREADY, as in the S4 spike and ADR 0007). Its test passes only against a mock written in the
same inverted order. Also: extras read as a fixed 1024 bytes (ADR: i32 length + bytes); the cell
goes out untransposed (sheared cell: sent `[2,0,0,0.5,2,0,…]`, ADR `[2,0.5,0,0,2,0,…]`); the
virial is not transposed; `accept()` has no timeout; a stale-socket cleanup deletes any file at
the path; malformed extras are dropped silently. The issue was `needs-design` and no design
doc was written. The branch is based on `main`, not on the engine stack. No engine change, so no
recompile. UnitcellMD PR #5 (Copilot, ΔH_vap and ε sources) has no commits yet (+0/−0) though its
text describes ledger entries. **CI:** `spec` was red since `b2a` was first pushed, from one
over-long line in `spec/fixtures/_generators/generate.py` (32c6def); formatted with the
validator's ruff config, fixtures byte-identical, 58 validator tests pass —
evidence: ucmd-engine PR #2 probe against ASE (scratch), `docs/design/A1.5.md` §10 — next: review
comments for Jo; the author approves or changes the two design notes

2026-11-21 — gate-b1a §4.1 fixed: validator 0.1.1 ships its schemas — the first outside
contribution (branch jo/validator-schema-packaging, merged into b2a by the author's request).
The wheel bundles spec/schemas; lookup order UCMD_SPEC_DIR, bundled copy, checkout. Spec stays
0.1.0. Review: hatchling added to the dev extras, otherwise the new packaging test skipped in CI —
evidence: 58 validator tests, none skipped; a non-editable 0.1.1 install validates the fixtures
without UCMD_SPEC_DIR, 0.1.0 fails with FileNotFoundError — next: the builder's UCMD_SPEC_DIR
workaround can go once it pins validator 0.1.1

2026-11-21 — research S2: Li⁺ preference replicas analysed — 4 runs per model, one Li⁺ in
EC:EMC 1:1: EC share of the first shell M0 17.7 ± 1.4 %, M1 30.4 ± 3.1 % (+12.7 ± 3.4); within
0.516 nm 29.3 ± 0.5 % against 39.2 ± 2.1 %; EC residence 21 → 40 ps. Every M1 run lies above
every M0 run, the criterion set before the runs. m1_r2 continued from its checkpoint after the
GPU hang; trajectories gap-free. Error found: the M1 study's first-shell command lacked
`--r-cut-nm 0.28` (the CLI then uses per-pair minima, EC 0.3175 nm); corrected, the replicas
reanalysed. Summary PDF rebuilt with all runs and the aug-cc-pVTZ QM, nothing pending —
evidence: studies/2026-11-21_li-preference-replicas/README.md, analysis/replicas.json — next:
M1 at 1 M against the DRS estimate (≈ 2.2 EC per Li⁺)

2026-11-21 — research: QM layer 0 at the default level; results summary — **Psi4 frozen
core:** bare Li⁺ was correlated (Psi4 unfreezes the core when no valence electrons remain), Li 1s
in the complex was not, so every E_bind was too weak by the Li⁺ 1s² correlation (0.3 kcal/mol at
6-31+G(d,p), 6.9 at aug-cc-pVTZ). Fixed in `tools/qm/li_binding_qm.py` (SCF for species without
active electrons, counterpoise by hand). **MP2/aug-cc-pVTZ after the fix:** EC −48.15, DMC
−41.27 kcal/mol against Olguin's −47.8, −41.3; EMC −41.92, PC −49.86 (ours, not in Olguin).
EC − EMC −6.24 kcal/mol against M0 +0.84 and M1 −1.24; Li–O 1.75–1.76 Å against 1.94–2.04 Å in
the force fields. **Summary PDF** for the JMU contacts (`docs/research/summary/`, rules in
docs/research/publication.md): built by script, every number computed, from the ledger, or
checked verbatim against a report. **Replicas (queue 6):** m1_r2 was ended at 3340 ps by the
GPU-hang telemetry (bridge in kfd_wait_on_events); the queue resumes it from its checkpoint —
evidence: tools/qm/README.md, tools/qm/results/, tools/ffcheck/README.md — next: replicas
analysed; summary rebuilt

2026-11-21 — E2.9 rung EC done; bridge LJ tail fixed — **rung EC** (2 ns NPT on HIP, 0.5–2 ns):
OPLS-AA EC ρ = 1319.2 ± 0.3 g/L, ΔH_vap = 64.36 ± 0.05 kJ/mol against Caleman 2012's 1320.7 and
64.90; LigParGen EC 1280.1 g/L (−3.1 %) and 62.00 kJ/mol under identical settings. **Water on
the GPU:** the conformance failure was not precision (double: energy 6.3e-6 off, forces
7.6e-8). OpenMM's LJ long-range correction averages over N(N+1)/2 pairs of all atoms, including
H without LJ; the engine's is 2π/V Σ n_a n_b I_ab. For 500 waters the two differ by 0.1668
kJ/mol, the whole gap. The bridge now weights OpenMM's tail integral per class pair (engine
`e25-constraints` afbc3b2, test-first; bridge 30 tests): water agrees to 1.4e-9 on the
Reference platform and 4.1e-8 on HIP double. HIP mixed stays at 2.1e-6 (single-precision
rounding), so rung W runs in double precision (author, 2026-11-21): queue 7 after queue 6,
profile `machine-gpu-double-identity.toml`. HIP so far: no hang in about 2.3 GPU hours (EC test,
M1) — evidence: studies/2026-11-20_ec-opls-test/README.md, bridge tests — next: twin and Wu
water (queue 7), CPU viscosity (≈ 23:00Z), then the rung W report.

2026-11-21 — research S2 (M1 Li⁺ preference) done — one LiPF₆ in EC:EMC 1:1 with OPLS-AA EC,
5 ns NPT on HIP (58 min, no hang). Last 4 ns: EC 31 ± 7 % of the first-shell carbonyl O (M0
19 ± 4 %), 39 % within 0.516 nm (M0 29 %; Lehnert ≈ 47 %); EC residence 42 ps (M0 24 ps). Trend
towards EC as layer 0 predicts, 1.4 SEM from one ion; not yet significant and below the 50 %
share — evidence: studies/2026-11-20_li-preference-m1/README.md — next: more statistics
(several independent Li⁺ or longer runs) before deciding on the pair-specific Li⁺–O term.

2026-11-20 — A4 done (20:06Z, OpenCL with hang restarts; 0 label swaps) — one Li⁺, last 4 ns:
pure EC 4.8 EC O=C (free); pure EMC 3.4 EMC O=C + 0.88 PF₆⁻ (contact pair); EC:EMC 1:1 first
shell EC 0.89 / EMC 3.65 = EC 20 % at 50 % of the molecules (29 % within 0.516 nm); residence EC
24 ps, EMC 250 ps — evidence: calculation plan A4 row — next: M1 (queue 4, HIP) against this.

2026-11-20 — research layer 0 — `tools/ffcheck/li_binding.py` (gas-phase Li⁺–solvent binding,
flexible, OpenMM via the oracle; 5 tests incl. an exact 1D case). Against G4 (Olguin, Borodin et
al. 2016, Table 1): QM puts EC 6.2 kcal/mol below DMC; M0 +0.1, M1 −2.0. Both under-bind by
12–18 kcal/mol (no induction). The carbonyl charges explain part of the EC depletion, not all
of it — evidence: tools/ffcheck/README.md, results JSON — next: M1 liquid run (queue 4); if EC
stays depleted, a pair-specific Li⁺–O term (needs spec per-pair overrides).

2026-11-20 — research S2 prepared; A4 preliminary — author approved M1 (test set) and the ECC
trial (M3) with a caution on refractive indices; strategy §8 now places ECC's failure in the
first Li⁺ shell and adds cluster QM there (Leontyev & Stuchebrukhov 2011, Kirby & Jungwirth
2019, both in ../Lit). A4 1:1, first 2 ns: EC 21 % of the first-shell carbonyl O at 50 % of
the molecules; Li⁺ in pure EC binds 4.9 EC, so the depletion is parametric, not crowding. The
identity repair stops on these NPT trajectories (molecule moves 0.96 / 1.14 nm after
relabelling); shell counts do not need it. New study `studies/2026-11-20_li-preference-m1`
(OPLS-AA EC + LigParGen EMC; trial build 6258 atoms, `ucmd-build check` OK, Caleman charges in
the package), GPU queue 4 after queue 3 — evidence: strategy §8, calculation plan A4 — next:
M1 vs M0 shells when queue 4 is done; S1 sources (n_D, ε of EMC).

2026-11-20 — research (stage B strategy) — Li⁺ shell compared with Lehnert at his radius
(rs = 5.16 Å, SI Fig. S10): EC 0.98 / EMC 3.91 / PF₆⁻ 0.28 per Li⁺ (EC 20 % of the carbonyl O;
Lehnert ≈ 47 %, same ζ). κ_exp = 0.84 S/m (Landesfeind 2019, Eq. 15) against our 0.42 S/m;
Lehnert's κ uses formal charges. Strategy draft `docs/research/forcefield-strategy.md`
(M1 EC types → M2 QM charges + small LJ refit → M3 ζ from n_D (ECC) → M4 Drude only if needed).
A4: pure EC ended at 1.76 ns (exit −9 after a stall); the 1:1 run continues — evidence: report
§3.4, §3.5 — next: A4 analysis, S1 sources, S2 after approval.

2026-11-20 — GPU hang test on HIP (author approved) — image `ucmd-openmm:gfx906-hip`
(Dockerfile.hip on `e25-constraints`: OpenMM 8.5 + OpenMM-HIP-7 from PyPI).
- **Short test (pilot electrolyte, 100k steps):** conformance 1.6·10⁻⁸; 92.6 ns/day while
  sharing the GPU with A4 (OpenCL alone ≈ 80); T and U consistent with OpenCL.
- **Queue switch:** queue 3 (and queue 4, same profile) runs on HIP via
  `machine-gpu-mixed-identity.toml` (OpenCL backup `.opencl.toml.bak`). The hang rate per GPU
  hour is the test.
- **Found on the way:** the strict identity tracker without the afternoon's relaxation stopped
  a run because methyl rotation moved an EMC by 0.21 nm in 0.25 ps. `e25-constraints` now merges
  `e37-identity`.

2026-11-20 — E2.5 complete (engine branch `e25-constraints`) — constraints in every mode of
the engine and the bridge.
- **Modes:** VV, NHC, Langevin BAOAB (constrained BAOAB), C-rescale (molecular scaling for
  constrained molecules), FIRE (projected forces), and the OpenMM CustomIntegrators.
- **Evidence:**
  - rigid dimers: atomic + constraint virial = molecular pressure at every step to 1.5·10⁻¹⁵;
  - constrained Langevin: T 299.4 ± 0.5 K, P 98.25 ± 0.23 bar (exact 98.18);
  - NPT: H holds to 0.012 kJ/mol against 0.16 for a stiff bond;
  - FIRE reaches the analytic constrained minimum;
  - CPU and OpenMM agree to 3.8·10⁻⁷ kJ/mol over 200 fs;
  - engine 113 tests, bridge 26.
- **Found on the way:**
  - the end-of-step constraint virial was wrong in BAOAB (now exact instantaneous constraint
    forces);
  - atomic scaling + SHAKE broke NPT energy bookkeeping;
  - OpenMM holds constraint lengths in float32 (≤ 6·10⁻⁸).
- **Also:**
  - identity tracker: accepts fast unambiguous moves; repair `--skip-ps`. A4 has 0 swaps.
  - Water rung: 512 molecules (216 too small for cutoff + skin). First CPU result: ρ 1.0060 ±
    0.0017 (Wu 1.012), ΔH_vap 10.80 kcal/mol (Wu 10.72).
  - GPU hangs continue under the clock cap: a lost completion event, per session unitcellmd-3f.
    The logger now ends a hang after 3 min; the HIP platform would need a new image (question
    for the author).
- **Next:** GPU queue results; merge order of the branches (e37-identity → e29-pressure-tensor
  → e25-constraints).

2026-11-20 — E2.9 continued (author: order approved, Wu 2006 added, pressure tensor yes, EC
test yes, "best decision" on performance) —
- **Spec 0.1.1:** `[output.thermo] pressure_tensor` (umbrella 32c6def); engine and bridge
  refusal on branch `e29-pressure-tensor`.
- **Analysis:** `viscosity` (Green–Kubo, tested on OU processes).
- **Engine (found and fixed):** constraints were counted in N_dof but not enforced, now refused
  until E2.5 (d9a6b19). E2.5 first step (RATTLE) on `e25-constraints`.
- **Rung W:** parameters verified against Wu Table I. Wu-matched GPU study and GPU twin queued
  after A4 (queue 3, identity-fixed bridge). CPU viscosity run queued after the CPU density run.
- **Rung EC:** OPLS-AA EC from Caleman's files reproduces OpenMM on the originals to 1.2·10⁻¹⁵.
  Gas phases done; liquids queued.
- **Performance decision:** GPU for production; CPU at most 8 threads, nice 10.
- **Evidence:** engine 111 tests; bridge 24; analysis 26; validator 57.
- **Next:** GPU queue results (P1, rung W, rung EC), CPU viscosity, E2.5 second step.

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
