# Gate 0 report — Phase P0 (foundations)

- **Date:** 2026-11-12. Prepared by the agent while the author was away.
- **Where:** branch `phase-0` of the UnitcellMD repo. `main` holds only what the author has
  seen or decided. After `tools/publish-github.sh --prs` this becomes a pull request.
- **Asked of the author:** approve, or change, the decisions in §3. Then `phase-0` is merged
  and the spec is tagged `spec-v0.1.0`.

## 1. Summary

1. **Spec v0.1 is complete:** units, system package, run configuration with machine profile,
   H5MD profile, checkpoint content, force-provider contract with i-PI conventions. JSON
   Schemas are included.
2. **A reference validator enforces the spec,** with 15 error codes, each demonstrated by its
   own invalid fixture.
3. **All four spikes succeeded:**
   - S1: H5MD trajectories from Rust without any system HDF5.
   - S2: a validated OpenMM oracle.
   - S3: PySide6/pyvistaqt at 60 fps for 50k atoms on native Wayland.
   - S4: the Rust ↔ ASE socket link, exact to machine precision.
4. **The core modularity claim is demonstrated:** a Rust i-PI server can drive any ASE
   calculator with 0.8 ms overhead per step and no loss of precision.
5. **The E1 engine design is written.** Every acceptance criterion maps to a named test.

## 2. What was built, with evidence

| Task | Result | Evidence |
|---|---|---|
| P0.1 | umbrella repo + three component skeletons; dependency guard; CI | engine: fmt, clippy -D warnings, tests, `check-architecture.sh` (7 crates) green, and the guard rejects both kinds of injected violation; builder/analysis: ruff + 3 tests each |
| P0.2 | audit confirmed and extended (13 issues, fixture inventory) | reference-check script 46/46 |
| P0.3 | spec documents + 2 JSON Schemas | `spec/`, ADR 0003 |
| P0.4 | `ucmd-spec` validator, generator, 4 valid + 19 invalid packages, valid and invalid run configs | 53 tests incl. "committed fixtures equal the generator output" and physics sanity (argon density 1.374 g/cm³ to 10⁻⁵, SPC/Fw geometry, NaCl lattice) |
| P0.5 S1 | `hdf5-metno` + bundled static HDF5 | 61 s one-time build; 1000 × 10k atoms written in 0.25 s; passes `ucmd-spec`, h5py (exact values), MDAnalysis 2.11; box rows confirmed as lattice vectors (ADR 0004) |
| P0.5 S2 | OpenMM 8.6.1 oracle from PyPI | OpenMM vs NumPy: energy 10⁻¹⁰, forces 10⁻⁹, FD-strain virial 10⁻⁵, dispersion correction 10⁻⁹; argon references committed (ADR 0005) |
| P0.5 S3 | PySide6 6.12 + pyvistaqt | 10k/50k atoms at the 60 Hz vsync cap, native Wayland, RX 580; screenshots capture 3D (ADR 0006) |
| P0.5 S4 | Rust i-PI server ↔ ASE `SocketClient` | with spec constants: energy 2×10⁻¹⁶, forces 2×10⁻¹³ (max/rms), virial 4×10⁻¹⁶ vs direct ASE and OpenMM; triclinic verified; transposed cell off by 5.6×10⁶; 0.8 ms per round trip (ADR 0007) |
| P0.6 | E1 design | `docs/design/E1.md` |
| extra | Lehnert 2025 SI in `../Lit`; protocol summary | `docs/lehnert2025-si-notes.md` |

## 3. Decisions to review

| # | Decision | Where | Agent's recommendation |
|---|---|---|---|
| 1 | One `system.json` per package (not a manifest plus per-type files) | ADR 0003 ★1 | keep |
| 2 | Everything is molecule type × count; crystals use single-atom types | ADR 0003 ★2 | keep |
| 3 | Mass unit = g/mol (labelled amu), so the unit system is exactly consistent | ADR 0003 ★3, units.md | keep |
| 4 | Bonded parameters explicit per interaction; atom types only for LJ | ADR 0003 ★5 | keep |
| 5 | Exclusions by shortest bond path (like LAMMPS/OpenMM) | ADR 0003 #7 | keep |
| 6 | H5MD via `hdf5-metno` with bundled static HDF5; feature-gated | ADR 0004 | keep. `libhdf5-dev` is **no longer needed** |
| 7 | OpenMM oracle from PyPI (no OpenCL in that build) | ADR 0005 | keep; decide OpenCL at E3.7 |
| 8 | GUI as optional extra `ucmd-builder[gui]` (the stack is 1.5 GB); 3D view behind a `Viewer` interface | ADR 0006 | keep |
| 9 | i-PI conventions; `ucmd-bridge` pins ASE to the spec constants | ADR 0007 | keep |
| 10 | E1 design questions (double buffering, velocity rescaling, tether provider) | design/E1.md §10 | see the doc |
| 11 | Commit identity morja@mailbox.org (repo-local); NOTICE "The UnitcellMD Authors" | STATUS.md | change if you prefer your name |
| 12 | Review via branches/PRs: `main` = approved, `phase-0`, `e1`, … = pending | STATUS.md | keep |

## 4. Deviations from PLAN.md

- **P0.3:** single `system.json` instead of a manifest plus per-type files (decision 1).
- **P0.5 S1:** compared two crates instead of one. The new pure-Rust `hdf5-pure` turned up and
  was rejected for now: it cannot append to N-dimensional datasets.
- **P0.4:** fixtures are generated reproducibly from the raw PCG64 bit stream, and CI checks
  them byte for byte. That is more than PLAN.md asked for.
- **Partly done:** GitHub. The author pushed `phase-0` of this repo (private); everything else
  is still local (STATUS.md).

## 5. Needed from the author

1. GitHub: choose the owner (organization or personal account) and create the three missing
   repos, either empty in the web UI or with `gh auth login`. Then `tools/publish-github.sh
   --owner <owner>` pushes everything over SSH (`--dry-run` shows what it will do; `--prs`
   opens the review PRs and needs gh). New repos are private.
2. **Force-field source** for the solvents (PLAN.md §10.6). The Lehnert SI uses Schrödinger
   Maestro OPLS, which is commercial. Options: (a) a licence, (b) Ringsby 2021 SI files,
   (c) an open OPLS-AA parameterization.
3. The decisions in §3. Silence on an item means "keep".

## 6. Proposed next steps

- **E1** (engine) as designed. It is started provisionally on branch `e1` of `ucmd-engine`,
  so it can be reviewed or discarded independently of Gate 0.
- **B1** (headless builder) can then run in parallel. It is the next item that needs the
  force-field source decision (§5.2).
