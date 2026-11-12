# UnitcellMD — implementation plan

Version 1.3 · 2026-11-12 · Status: Gate 0 approved (spec v0.1.0); E1 complete and awaiting
Gate E1 (docs/gates/gate-e1.md); B1 in design.
Executed by: a coding agent following [CLAUDE.md](CLAUDE.md). Approved by: the author, at every gate.
Task IDs (P0.3, E1.5, …) are stable. Reference them in commits, `docs/STATUS.md` and ADRs.

---

## 1. Goal and scope

UnitcellMD is a set of independent tools that together run molecular dynamics of large periodic
systems (10³–10⁵ atoms) with forces from any source — analytic force fields computed in-process,
or external programs (ML potentials, quantum chemistry, QM/MM) — without the integrator knowing
which. It succeeds the author's MSc code NeNePo_builder (on-the-fly Ag₄ dynamics: Python velocity
Verlet with Gaussian/ORCA adapters). What exists there, and what to learn from it, is in
[docs/nenepo-audit.md](docs/nenepo-audit.md).

**First scientific target:** reproduce the MD part of Lehnert et al. 2025, J. Electrochem. Soc. 172,
050523 (`../Lit/`): LiPF₆ in EC:EMC (3:7 w:w), OPLS-AA with scaled ion charges (ζ), Nosé–Hoover
thermostat, conductivity κ and transference number t⁺ from Onsager coefficients computed in the
centre-of-mass frame. The simulation parameters are in the paper's supplementary information
(`../Lit/…_SI.pdf`), summarized in [docs/lehnert2025-si-notes.md](docs/lehnert2025-si-notes.md).

**Not in v1** (the design must not block them): matching GROMACS/OpenMM speed for classical MD;
GPU kernels inside the engine; MPI/distributed runs; general automatic atom typing; slab/interface
electrostatics; enhanced sampling and free-energy methods.

---

## 2. Architecture

### 2.1 Components

| Component | Where | Language | Owns | Must not |
|---|---|---|---|---|
| Spec | this repo, `spec/` | docs + JSON Schema; Python reference validator | formats, units, provider contract, fixtures | contain component code |
| Builder | repo `ucmd-builder` | Python (RDKit, ASE, PySide6) | molecules, crystals, packing, force-field assignment, initial conditions, GUI, run campaigns | run MD |
| Engine | repo `ucmd-engine` | Rust, plus a small Python bridge for external providers | state, integrators, thermostats, barostats, constraints, providers, I/O, checkpoints | depend on builder internals; name a force method inside the integrator |
| Analysis | repo `ucmd-analysis` | Python (NumPy, h5py, MDAnalysis) | RDF, MSD, Onsager coefficients, κ, t⁺, error bars | import engine or builder code |
| Oracle | this repo, `tools/oracle/` | Python (OpenMM) | reference energies, forces and trajectories for validation | become a runtime dependency |
| Launcher | repo `ucmd-launch` (from A2.2) | Python | running many jobs through executors: `local` first, `slurm` later | contain physics; be needed for a single run |

### 2.2 Data flow

```
 build.toml ──► ucmd-builder ──► system package ───────────┐
 (recipe; the GUI edits it)      (spec/system-package.md)   │
                                                            ▼
 run.toml ──────────────────────────────────────────► ucmd-engine ──► trajectory.h5 ──► ucmd-analysis
 (integrator, ensemble, provider choice, outputs)        │   │        (H5MD profile)    κ, t⁺, L_ij, RDF, MSD
                                                         │   │
                      ForceProvider trait (in-process)   │   │   i-PI socket (out-of-process)
                      harmonic, LJ, OPLS terms, PME  ◄───┘   └──►  ucmd-bridge: any ASE calculator,
                                                                   ML potentials, ORCA/Gaussian adapters
                                                                   (ported from NeNePo), OpenMM
```

### 2.3 Design decisions (with reasons)

- **D1 Repositories.** This repo holds the plan and the spec. Three component repos
  (`ucmd-engine`, `ucmd-builder`, `ucmd-analysis`) live as subfolders with their own `.git`,
  ignored by this repo. Force-field parameter data starts inside the builder
  (`ucmd_builder/forcefields/`) and moves to its own repo once a second consumer appears.
  *Why:* independence where it matters (no shared code, separate release cycles) without five
  CI setups before anything runs.
- **D2 Contract first.** Spec v0.1, fixtures and a validator exist before component code. Every
  component runs the spec fixtures as contract tests.
- **D3 Units: nm, ps, amu, kJ/mol, e, K.** This set is self-consistent:
  1 amu·nm²·ps⁻² = 1 kJ/mol, so F = m·a needs no conversion factor. It is also what GROMACS and
  OpenMM (our validation oracle) use. Å appears only in importers and the GUI.
  *(Needs the author's confirmation, §10.)*
- **D4 Formats.**
  - System package: a directory with `manifest.json`, topology per molecule type (JSON), and NPY
    arrays (positions, optional velocities).
  - Human-written configs (`run.toml`, `build.toml`): TOML.
  - Trajectories: H5MD (an HDF5 layout standard for MD data, readable by h5py and MDAnalysis).
  - Checkpoints: engine-private, but documented.

  No YAML in machine-written formats: implicit typing causes silent errors, and Rust's YAML crates
  are in flux.
- **D5 Topology as molecule type × count**, like GROMACS `[moleculetype]` and `[molecules]`, plus
  explicit-atom components for crystals. *Why:* compact and readable, and it carries the
  molecule identity that the Onsager analysis needs.
- **D6 System and run are separate.** The package says *what* the system is (atoms, topology,
  optional force-field parameters). `run.toml` says *how* to run it (integrator, ensemble,
  provider). The same package runs with classical, ML or QM forces by editing `run.toml` only.
- **D7 Two provider tiers.**
  - In-process Rust providers, for speed: classical force-field terms.
  - Out-of-process providers over the **i-PI socket protocol**, for everything else. The Rust
    engine implements the i-PI *server*. ASE's `SocketClient` then turns any ASE calculator into
    a provider: ML potentials, xTB, ASE's QC calculators.

  The NeNePo Gaussian/ORCA adapters are ported as hardened Python calculators, not rewritten in
  Rust.
- **D8 The integrator is a composition of splitting operators** (§2.5). Thermostats, barostats
  and constraints are operators, not code inside velocity Verlet. The NeNePo integrator is the
  special case B·A·F·B.
- **D9 Builder headless first.** First a library, a CLI and a declarative recipe; the GUI comes
  later, edits recipes and calls the library. *Why:* an agent can test it; recipe + seed always
  gives the same package; it works on clusters without a display.
- **D10 Validation by oracle.**
  - Every provider passes generic finite-difference tests for forces and for the strain-derivative
    virial.
  - Every classical term is compared with OpenMM on the identical package (converter in
    `tools/oracle/`).
  - Analysis is validated on synthetic data and on OpenMM trajectories, so it can progress
    without waiting for the engine.
- **D11 Unwrapped positions.** The engine stores positions unwrapped, in f64, and wraps only
  inside PBC kernels. Molecules therefore stay whole for external providers, and trajectories
  need no image flags.
- **D12 Capabilities and virial are in the provider contract from day one.** They are cheap now
  and expensive to retrofit. Checkpointable provider state is added in E3.4.
- **D13 Local-first, cluster-capable** ([ADR 0002](docs/decisions/0002-local-first-execution.md),
  the author's requirement).
  - A classical run needs only `ucmd`, a system package and `run.toml`: no scheduler, MPI,
    network, external programs or Python.
  - Everything heavier is opt-in and built from the same pieces: external providers (bridge
    processes, also on other nodes over TCP), GPU-backed providers, campaigns.
  - Running many jobs is a separate thin layer, `ucmd-launch` (A2.2), with pluggable
    executors: `local` first, `slurm` later. Scheduler code lives nowhere else.
  - Packages and `run.toml` are location-independent. Machine-specific settings (executable
    paths, scratch directories, core counts) live in a per-machine profile.

### 2.4 Force-provider contract (sketch — finalize in `docs/design/E1.md`)

```rust
// crate ucmd-force. Vec3/Mat3 = f64 types from ucmd-core (glam::DVec3/DMat3 recommended).
pub struct Capabilities {
    pub periodic: bool,       // accepts a periodic cell
    pub virial: bool,         // can return W (needed for pressure and NPT)
    pub energy_terms: bool,   // returns an energy decomposition
    pub deterministic: bool,  // same input → bitwise same output (false for SCF codes)
}

pub struct EvalRequest { pub step: u64, pub time_ps: f64, pub need_energy: bool, pub need_virial: bool }

#[derive(Default)]
pub struct ForceResult {
    pub energy: f64,                            // kJ/mol
    pub forces: Vec<Vec3>,                      // kJ mol⁻¹ nm⁻¹, canonical atom order, F = −∂E/∂r
    pub virial: Option<Mat3>,                   // kJ/mol, W = −∂E/∂ε (spec/units.md)
    pub energy_terms: Vec<(String, f64)>,       // optional; must sum to `energy`
    pub observables: Vec<(String, Observable)>, // dipole, state energies, charges … (NeNePo "getens")
}

pub trait ForceProvider: Send {               // object-safe: Box<dyn ForceProvider>
    fn name(&self) -> &str;
    fn capabilities(&self) -> Capabilities;
    fn initialize(&mut self, system: &System) -> Result<(), ForceError>; // immutable topology etc.
    /// Overwrites `out` (caller-owned buffer, reused every step). Positions are unwrapped.
    fn evaluate(&mut self, positions: &[Vec3], cell: Option<&Cell>,
                req: &EvalRequest, out: &mut ForceResult) -> Result<(), ForceError>;
    fn finalize(&mut self) -> Result<(), ForceError> { Ok(()) }
    // E3.4 adds save_state / restore_state for providers with memory (SCF guess files, …)
}

#[derive(thiserror::Error, Debug)]
pub enum ForceError {
    Unsupported(String),   // e.g. periodic cell given to a gas-phase provider
    InvalidInput(String),  // NaN coordinates, overlapping atoms
    NotConverged(String),  // SCF and other iterative solvers
    External { program: String, status: Option<i32>, stderr_tail: String },
    Protocol(String),      // socket / i-PI
    Parse { file: String, detail: String },
}
```

The engine wraps the provider in two layers:

- `Guarded<P>` checks every result before use: `forces.len() == N`; all values finite; virial
  present when requested and supported.
- `Composite` sums child providers. Each child has its own buffer, and energy terms are prefixed
  with the child's name. This is how a classical force field (bonds + angles + dihedrals + LJ +
  PME) and, later, QM/MM are assembled.

**Out-of-process profile (i-PI).**

- Messages are in atomic units (bohr, hartree). The bridge converts at the boundary.
- The `extras` field carries JSON, which becomes `observables`.
- Limitation: the protocol carries no point charges. Electrostatic-embedding QM/MM therefore needs
  an extension (E3.8).

### 2.5 Integrator = composition of operators

The operators are: A = drift (x += v·Δt), B = kick (v += F/m·Δt), F = force evaluation,
O = stochastic/velocity-rescaling thermostat, N = Nosé–Hoover chain update.

| Scheme | Step (fractions of Δt) |
|---|---|
| Velocity Verlet (NVE) | B(½) A(1) F B(½) — identical to NeNePo `VV_8_12.py:72-76` written in position form |
| CSVR thermostat (Bussi 2007) | O(½) B(½) A(1) F B(½) O(½) |
| Langevin BAOAB (Leimkuhler–Matthews) | B(½) A(½) O(1) A(½) F B(½) |
| Nosé–Hoover chains (Martyna–Klein–Tuckerman) | N(½) B(½) A(1) F B(½) N(½) |
| + RATTLE constraints | position correction after every A, velocity correction after every B/O |
| + C-rescale barostat (Bernetti–Bussi 2020) | cell and coordinate scaling operator, once every n steps |

Each thermostat and barostat accumulates the energy it exchanges and reports a **conserved
quantity**, so thermostatted runs can be checked for drift. (The NeNePo note that "Ekin+Epot
diverges with Berendsen" describes expected behaviour, not a bug; see the audit.)

Degrees of freedom: N_dof = 3N − N_constraints − 3 (if COM momentum is removed) − 3 (if angular
momentum is removed, only allowed for non-periodic systems). They are computed in exactly one
place.

### 2.6 Units and conventions

| Quantity | Unit (internal and in files) | Note |
|---|---|---|
| length | nm | Å only in importers and the GUI display |
| time | ps | timestep is written `timestep_fs` in configs |
| mass | amu (= g/mol) | from the system package only |
| energy | kJ/mol | 1 amu·nm²·ps⁻² = 1 kJ/mol |
| force | kJ mol⁻¹ nm⁻¹ | |
| charge | e | |
| temperature | K | |
| pressure | bar in configs and logs | internally kJ mol⁻¹ nm⁻³ (1 kJ mol⁻¹ nm⁻³ = 16.6054 bar) |
| k_B | 0.00831446261815324 kJ mol⁻¹ K⁻¹ | |
| Coulomb constant | ≈ 138.935458 kJ mol⁻¹ nm e⁻² | derive from CODATA 2018 in code; never type the rounded literal |

Conventions to fix in `spec/units.md`:

- **Cell.** A 3×3 matrix whose rows are the lattice vectors a, b, c (ASE convention), restricted
  to the reduced lower-triangular form used by GROMACS: a along x, b in the xy-plane,
  |b_x| ≤ a_x/2, |c_x| ≤ a_x/2, |c_y| ≤ b_y/2. The builder reduces cells on export.
- **Forces.** F = −∂E/∂r.
- **Virial.** W_ab = −∂E/∂ε_ab under the homogeneous strain h → (1+ε)h. For pair potentials this
  equals Σ_{i<j} r_ij ⊗ F_ij. Pressure tensor P = (Σ_i m_i v_i ⊗ v_i + W)/V. Every provider is
  checked against this definition by finite differences.
- **Config keys carry their unit in the name:** `timestep_fs`, `cutoff_nm`, `temperature_K`,
  `pressure_bar`, `tau_ps`.

### 2.7 Engine crate layout (`ucmd-engine/`, Cargo workspace)

```
crates/
  ucmd-core/                 units, Vec3/Mat3, Cell, System (immutable), State, ids
  ucmd-force/                ForceProvider trait, ForceResult, Guarded, Composite, test kit (feature "testkit")
  ucmd-providers-classical/  harmonic, LJ, bonded terms, Coulomb/Ewald/PME, neighbour lists
  ucmd-providers-ipi/        (E3) i-PI socket server provider
  ucmd-md/                   operators, integrators, thermostats, barostats, constraints, minimizer, run loop
  ucmd-io/                   system-package reader, run.toml, H5MD writer/reader, checkpoints, XYZ debug
  ucmd-cli/                  binary `ucmd`; provider registry (name → constructor); composition root
bridge/                      (E3) Python package `ucmd-bridge`
validation/                  long physics validation cases, each with REPORT.md
```

**Dependency rule, enforced by Cargo:** `ucmd-md` depends on `ucmd-core` and `ucmd-force` only,
never on any `ucmd-providers-*` crate. Only `ucmd-cli` knows the concrete providers.

---

## 3. Phases, milestones, order

| ID | Track | Deliverable | Exit evidence (gate) | Needs |
|---|---|---|---|---|
| P0 | all | spec v0.1, fixtures, validator, repo skeletons, four spikes, E1 design | author approves (Gate 0) | — |
| E1 | engine | NVE/NVT engine, LJ, PBC, H5MD, checkpoints, CLI | argon matches OpenMM; restart is bitwise identical | P0 |
| B1 | builder | headless builder + CLI + force-field template library | recipe → valid package → OpenMM runs it | P0 |
| E2 | engine | bonded terms, PME, constraints, NHC/Langevin, barostat, minimizer, performance | electrolyte box matches OpenMM (energies, density, RDF) | E1, B1 |
| B2a | builder | frontend preview: build, view, short local runs | author builds and runs a small electrolyte box in the GUI only | B1, E2 core |
| B2b | builder | complete PySide6 GUI over the builder library | author builds electrolyte + crystal in the GUI only | B2a |
| A1 | analysis | RDF, MSD, Onsager L_ij, κ, t⁺, error bars | synthetic tests + OpenMM-trajectory cross-checks | P0 (B1 for real systems) |
| E3 | engine | i-PI providers, ported NeNePo adapters, ML providers | one package runs with three provider kinds; thesis Ag₄ regression | E1 |
| A2 | analysis | Lehnert 2025 reproduction | κ and t⁺ within uncertainty of the paper | E2, A1, B1 |

**Milestones.**

- **M1 "first light"** (after E1): spec fixture → engine → H5MD → MDAnalysis RDF.
- **M2a "core stands"** (after B1 + E2 core): a builder-made LiPF₆/EC:EMC package runs NVT with
  PME in our engine, and its single-point energies and forces match OpenMM.
- **M2 "electrolyte box"** (after B1 + E2): a builder-made LiPF₆/EC:EMC package gives the same
  density and RDFs in our engine and in OpenMM.
- **M3 "any force"** (after E3): the same package runs with classical, socket-LJ and ML providers
  by editing `run.toml` only.
- **M4 "paper"** (after A2).

**Order with one agent:** P0 → E1 → B1 → E2 core (E2.0–E2.4, E2.6) → **B2a frontend
preview** → rest of E2 → A1, E3 and B2b in any order → A2.

- E2 is the largest block.
- **The frontend comes early, at the author's request (2026-11-12).** As soon as the core stands
  (M2a), B2a gives the author a GUI to build systems, look at them, start short local runs and
  watch the results, so that feedback arrives early. The rest of the GUI (B2b) follows later.

**With two agents:** run one engine agent (E1 → E2 → E3) and one builder+analysis agent
(B1 → A1 → B2 → A2). They meet only through `spec/`, which is the point of the design.

---

## 4. Phase P0 — Foundations (no physics code yet)

**P0.1 Bootstrap the workspace.**
- Run `git init` in this repo. Add a `.gitignore` covering `ucmd-*/`, `_reference/`, `**/.venv/`
  and `**/target/`.
- Create `ucmd-engine` (Cargo workspace with the empty crates from §2.7), `ucmd-builder` and
  `ucmd-analysis` (src layout, `pyproject.toml`, pytest). Each is its own git repo with README,
  LICENSE (§10), a `CLAUDE.md` stub with its commands, and a CI workflow file for fmt, lint and
  test. Do not push.
- Clone NeNePo_builder read-only into `_reference/NeNePo_builder`.
- ✓ `cargo test` / `pytest` pass in all three repos. The Commands table in the root `CLAUDE.md`
  is filled in.

**P0.2 Review the audit.**
- Check `docs/nenepo-audit.md` against `_reference/NeNePo_builder` and amend it.
- List the files usable as fixtures for parser tests (E3.3) and Wigner tests (B1.7).
- ✓ STATUS.md records the audit as confirmed or amended.

**P0.3 Spec v0.1 documents + JSON Schemas.** Write `spec/units.md`, `system-package.md`,
`run-config.md`, `trajectory-h5md.md`, `checkpoint.md`, `force-provider.md`,
`schemas/*.schema.json` and `CHANGELOG.md`. They must cover:
- Canonical atom order: components in manifest order → instances → template atom order.
- Component kinds: molecular template × count, and explicit atoms (crystals).
- Per-type topology: atoms (name, element, mass, charge, type); bonds; angles, dihedrals and
  impropers (listed explicitly or generated from bonds); exclusions and 1-4 pairs; constraints.
- Optional force-field section with an enumerated set of functional forms: harmonic bond and
  angle; OPLS/RB/periodic dihedral; periodic/harmonic improper; LJ 12-6 with combination rule and
  1-4 scaling; Coulomb.
- Cell and periodicity flags.
- Initial-state arrays: shapes, dtypes, units.
- Provenance: builder version, recipe, seeds, parameter sources, ζ.
- H5MD profile:
  - unwrapped positions; optional velocities and forces;
  - per-frame box, time and step;
  - observables: potential energy, energy terms, kinetic energy, temperature, pressure tensor,
    volume, conserved quantity;
  - per-atom species, mass, charge, molecule index;
  - provenance;
  - unit attributes on every dataset.
- Versioning: semver; readers reject an unknown major version. In v0.x breaking changes are
  allowed, but each bump updates fixtures and all readers together.
- ✓ Author approval at Gate 0.

**P0.4 Fixtures + reference validator.**
- `spec/fixtures/valid/`:
  - `harmonic-3d`: 3 particles.
  - `argon-864`: FCC lattice at the Rahman 1964 state point.
  - `water-2`: two flexible SPC/Fw molecules in vacuum, which exercises the topology section.
  - `nacl-crystal`: 2×2×2 conventional cells, for the Ewald tests.

  Rahman's argon and SPC/Fw (Wu, Tepper, Voth 2006) are pre-approved parameter sources; cite
  them.
- `spec/fixtures/invalid/`: one violation each: net charge, atom-count mismatch, bond index out
  of range, unknown unit, NaN coordinate, degenerate cell, unknown major version.
- Deterministic generators in `spec/fixtures/_generators/`.
- Python package `ucmd-spec` providing `ucmd-spec validate <pkg>`: JSON Schema plus semantic
  checks, with stable error codes.
- Molecular fixtures (EC, electrolyte) arrive later from B1.
- ✓ Valid fixtures pass. Each invalid fixture fails with its expected error code.

**P0.5 Spikes.** Time-boxed, throwaway code in `spikes/`, one ADR each in `docs/decisions/`.
- **S1 H5MD from Rust.** Use `hdf5-metno` (maintained fork of the `hdf5` crate; check its
  current status) with either the system libhdf5 or its bundled static build (cmake is
  installed). The system route needs `libhdf5-dev`, which is not installed — ask the author.
  Write 1000 frames × 10k atoms and read them back with h5py and MDAnalysis. Document a fallback.
- **S2 OpenMM oracle.** Use a venv in `tools/oracle/`; if Python 3.13 wheels are missing, use a
  Miniforge environment. Write a minimal package→OpenMM converter and compute a single point for
  `argon-864`.
- **S3 GUI viewer.** PySide6 + pyvistaqt showing 10k atoms (spheres, bonds, cell) interactively
  on this machine. Capture screenshots with `QWidget.grab()`. Fallback: QWebEngineView with
  3Dmol.js or NGL.
- **S4 i-PI handshake.** A ~100-line Rust socket server talking to ASE's `SocketClient` driving
  ASE's `LennardJones` calculator. Energies and forces must equal analytic LJ to 1e-10 after unit
  conversion. This also settles the cell-matrix orientation and the virial convention on the wire.
- ✓ Four ADRs, each with the result and the decision.

**P0.6 E1 design.**
- Write `docs/design/E1.md`: crate APIs, data types, operator design, error policy, output
  observers, and the test list mapped to the E1 acceptance criteria.

**Gate 0.** The author approves spec v0.1 (then tag `spec-v0.1.0`), the decisions in §10, the
spike ADRs and the E1 design.

---

## 5. Track E — Engine (`ucmd-engine`)

### E1 Minimal engine: NVE/NVT, PBC, Lennard-Jones

- **E1.1 Core types** (`ucmd-core`).
  - Cell: reduced triclinic; wrap; minimum image; volume; reciprocal vectors.
  - System (immutable): masses, charges, species, molecule index, topology.
  - State: unwrapped positions, velocities, step, time.
  - ✓ Minimum image equals a brute-force 27-image search on random reduced triclinic cells
    (proptest). Wrap/unwrap round-trips.
- **E1.2 Provider contract** (`ucmd-force`).
  - The trait from §2.4, plus `Guarded` and `Composite`.
  - A **test kit**, reused for every provider: `fd_force_check`, `fd_virial_check` (strain
    derivative), and a check that energy terms sum to the energy.
  - ✓ The test kit itself fails on deliberately broken providers: sign flip, missing factor 2,
    an off-by-one atom index.
- **E1.3 Analytic providers:** harmonic tether and harmonic pair spring (also periodic).
  ✓ They pass the test kit.
- **E1.4 Input** (`ucmd-io`).
  - System-package reader; `run.toml` parser that dumps the fully resolved config; `ucmd check`.
  - ✓ Every spec fixture loads. Invalid fixtures are rejected with the same error codes as the
    Python validator (contract test reading `UCMD_SPEC_DIR`, default `../spec`).
- **E1.5 Velocity Verlet** as operators A, B, F.
  - DOF accounting; COM-momentum removal (angular only if non-periodic); kinetic energy and
    tensor; seeded Maxwell–Boltzmann velocity generation.
  - ✓ (a) A 1D harmonic oscillator started at q = 0 gives max|E−E₀|/E₀ = (ωΔt)²/4 within 5 %
    (the VV shadow-energy result), with no secular drift over 10⁶ steps.
  - ✓ (b) Halving Δt reduces that error by a factor of 4.0 ± 0.2.
  - ✓ (c) Reversibility on the harmonic system: N steps, negate v, N steps → the start is
    recovered to 1e-10 relative.
  - ✓ (d) **NeNePo golden test:** a 3-particle harmonic system propagated by a NumPy
    transcription of `VV_8_12.py:72-76` (atomic units) agrees, after unit conversion, to 1e-10
    relative over 1000 steps.
- **E1.6 CSVR thermostat** (Bussi, Donadio, Parrinello 2007), the first O operator. It proves
  design D8.
  - ✓ On argon NVT, ⟨K⟩ = N_dof·k_BT/2 and Var(K) = N_dof·(k_BT)²/2, each within 3σ of its
    estimate. Conserved-quantity drift is comparable to the NVE drift.
- **E1.7 Lennard-Jones, brute force.**
  - Minimum image; cutoff modes truncate, potential-shift and force-switch; dispersion correction
    for energy and pressure; virial; per-type parameters with geometric or Lorentz–Berthelot
    combination.
  - ✓ Passes the test kit.
  - ✓ OpenMM single point on `argon-864` with identical settings: energy to 1e-8 relative,
    max|ΔF|/rms(F) ≤ 1e-6, pressure to 1e-6 relative.
- **E1.8 Neighbour search:** cell list plus Verlet list with skin; rebuild when the maximum
  displacement exceeds skin/2.
  - ✓ Forces identical to brute force (≤ 1e-12 relative) on random dense configurations,
    including triclinic ones.
  - ✓ criterion benchmark recorded for 864, 8k and 64k atoms.
- **E1.9 Outputs:** observer interface in the run loop; H5MD writer (spec profile); thermo table
  (TSV); extended-XYZ debug writer.
  - ✓ Output passes the spec validator and loads in MDAnalysis. MDAnalysis's RDF matches ours.
- **E1.10 Checkpoint/restart and the failure path.**
  - ✓ Running 2N steps equals running N + restart + N, bitwise (single thread).
  - ✓ A test provider that fails at step k produces a non-zero exit code, an error report, and a
    checkpoint of step k−1 that restarts cleanly.
- **E1.11 CLI and provenance.**
  - `ucmd run | check | singlepoint | rerun`. `rerun` evaluates a provider on every frame of a
    trajectory and writes H5MD observables; it replaces NeNePo's cation recalculation scripts.
  - Provider registry by name; provenance in every output.
  - ✓ End-to-end CLI tests on fixtures.
- **E1.12 Argon validation.**
  - Rahman 1964 state point: 864 atoms, 94.4 K, 1.374 g cm⁻³, σ = 0.34 nm, ε/k_B = 120 K.
  - CSVR equilibration, then NVE production. Compare with an OpenMM run of the identical setup:
    ⟨E_pot⟩, pressure, g(r), D. Rahman's D ≈ 2.43×10⁻⁵ cm² s⁻¹ serves as a sanity check.
  - ✓ Energy drift, in kT·ns⁻¹ per DOF, is no worse than OpenMM's Reference platform.
  - ✓ Results in `validation/argon/REPORT.md`.

**Gate E1 = M1.**

### E2 Molecular force field (OPLS-AA class) — the largest block

- **E2.0 FIRE minimizer.** Provider-agnostic; needed after packing.
  - ✓ Reaches known LJ-cluster minima. Brings max|F| below threshold on a packed electrolyte.
- **E2.1 Bonded terms:** harmonic bond, harmonic angle, OPLS/RB/periodic dihedrals, impropers.
  - ✓ Test kit per term.
  - ✓ Single molecules (EC, EMC, PF₆⁻) vs OpenMM: each energy term to 1e-8 relative.
- **E2.2 Exclusions and 1-4 pairs.** Exclusions come from the bond graph per the spec. 1-4 LJ and
  Coulomb are scaled by the package's factors (OPLS: 0.5/0.5). Both combination rules of the
  spec are supported: **geometric** for σ and ε (OPLS) and Lorentz–Berthelot (AMBER, OpenFF),
  so that every parameter source of ADR 0008 runs.
  - ✓ EC/EMC energy decomposition matches OpenMM term by term.
- **E2.3 Electrostatics reference:** plain Coulomb (non-periodic) and classic Ewald summation,
  with excluded-pair and self corrections and a neutrality check.
  - ✓ NaCl Madelung constant 1.747565 to 1e-8. Passes the test kit (forces, virial).
- **E2.4 Smooth PME:** B-spline order 4–6, grid from a tolerance, `rustfft`, triclinic cells,
  virial; direct-space part through the neighbour list.
  - ✓ vs converged Ewald: rms relative force error ≤ 1e-5 at default settings, converging with
    grid and order.
  - ✓ vs OpenMM PME with explicitly matched α, grid and order on the electrolyte package: energy
    to 1e-6, forces to 1e-5.
- **E2.5 Constraints:** SHAKE/RATTLE in the operator scheme for bonds to H, with rigid water as a
  test; DOF reduction; relative tolerance 1e-10.
  - ✓ SPC/E water at 2 fs drifts no worse than OpenMM with the same settings.
- **E2.6 Thermostats:** Nosé–Hoover chains (Lehnert used Nosé–Hoover) and Langevin BAOAB, each
  with its conserved quantity.
  - ✓ Canonical ⟨K⟩ and Var(K) as in E1.6. Conserved-quantity drift reported.
- **E2.7 Barostat:** stochastic cell rescaling (C-rescale), isotropic. Then the anisotropic
  variant for crystals.
  - ✓ Water and argon densities match OpenMM's MonteCarloBarostat within the combined
    uncertainty.
- **E2.8 Performance.**
  - rayon-parallel non-bonded and PME with deterministic reduction; profiling (perf/flamegraph).
  - Measure the ≈7.5k-atom electrolyte on 16 cores against OpenMM's CPU platform. **Agree a
    target with the author before optimizing.**
  - ✓ Benchmark report. Results independent of thread count to 1e-12 relative, or a documented
    reason why not.
- **E2.9 Molecular validation ladder.** Needs B1 packages and the oracle converter.
  - Steps: water → pure EC at 313 K (EC melts at ≈ 36 °C, so it is solid at room temperature)
    → LiPF₆ in EC → 1 M LiPF₆ in EC:EMC 3:7.
  - Compare with OpenMM on identical packages: NPT density; RDFs (Li–O carbonyl, Li–F, Li–P);
    energy terms; diffusion.
  - ✓ Reports in `validation/*/REPORT.md`.

**Gate E2 = M2.**

### E3 External force providers

- **E3.1 i-PI server provider** (grown from spike S4).
  - Unix and TCP sockets; handshake; POSDATA/GETFORCE; conversion to and from atomic units; JSON
    extras → observables; timeouts and detection of a dead client → `ForceError`.
  - Optionally the engine starts and stops the client process from `run.toml`.
  - ✓ ASE `LennardJones` over the socket equals in-process LJ (forces to 1e-10 relative).
  - ✓ Killing the client mid-run gives a clean error and a checkpoint.
- **E3.2 `ucmd-bridge`** (Python, in `ucmd-engine/bridge/`).
  - `ucmd-bridge serve --calculator <entry point> --config <file>` runs any ASE calculator as an
    i-PI client. Plugin entry points for our own calculators.
  - ✓ An example (EMT, xTB, or whatever installs cleanly) runs end-to-end.
- **E3.3 Hardened QC calculators** — the port of NeNePo `VV_8_gaussian`/`VV_8_orca` and
  `parse_gau`/`parse_orca`. Fix every issue in audit §5:
  - user input templates, as in the thesis;
  - absolute executable path, with a version probe at initialization;
  - fresh outputs on every call (clean scratch directory or deletion of stale files);
  - exit-status check;
  - geometry echo check: coordinates in the fchk/engrad file must match the requested ones to
    1e-6 bohr;
  - SCF-guess reuse (chk/gbw) as provider state;
  - explicit unit conversion;
  - observables (dipole moment, state energies).
  - ✓ Parser tests pass on the thesis files (`_reference/NeNePo_builder/ws_rhombus/**`).
  - ✓ Failure-injection tests raise in every case: non-zero exit, missing file, stale file,
    wrong geometry.
- **E3.4 Provider state in checkpoints.** A trait extension, recorded in an ADR. A restarted QM
  run reuses its SCF guess.
- **E3.5 Rerun with external providers.** NeNePo's vertical cation energies along the neutral
  trajectory become `ucmd rerun` with a second provider.
- **E3.6 ML potentials** through ASE calculators; the author picks the model.
  - ✓ The LiPF₆/EC:EMC package runs with only `run.toml` changed (= M3).
- **E3.7 (optional) OpenMM as a provider** through the bridge. Its OpenCL platform runs on the
  AMD GPUs, giving fast classical forces through the same interface; it is also a production
  fallback.
- **E3.8 (optional, last) QM/MM.**
  - Mechanical embedding: `Composite` + region selection + link atoms.
  - Electrostatic embedding needs point charges on the wire → protocol-extension ADR.
- **E3.9 Thesis regression.** The author runs QC on the cluster. Take one Ag₄ trajectory from a
  thesis initial condition (`ws_rhombus/dynamics_XXXX.in`) at the thesis level of theory and
  compare energies and positions with the thesis run for about 50 steps.

**Gate E3 = M3.**

---

## 6. Track B — Builder (`ucmd-builder`)

### B1 Builder core (headless library + CLI)

- **B1.1 Package and data model.**
  - Recipe (`build.toml`), Component, MoleculeTemplate, BuiltSystem; CLI `ucmd-build`; exporter
    to system packages, checked with the `ucmd-spec` validator.
  - ✓ A minimal recipe produces a valid package.
- **B1.2 Molecule input.**
  - XYZ/MOL/SDF/PDB via RDKit (bond perception, SMILES); ASE for XYZ, CIF and other formats.
  - Angles and dihedrals generated from the bond graph. Canonical atom order = template order.
  - ✓ Round-trip tests. EC, EMC and PF₆⁻ graphs are correct.
- **B1.3 Force-field sources** ([ADR 0008](docs/decisions/0008-pluggable-force-field-sources.md)).
  - **Interface:** a `ForceFieldSource` takes a molecule graph (canonical atom order, formal
    charge, optional coordinates). It returns explicit parameters in spec units, the
    conventions (combination rule, 1-4 scales) and citations.
  - **Plug-ins** register through the entry-point group `ucmd_builder.forcefield_sources`. The
    built-in sources use the same mechanism.
  - **Built in:**
    - `library`: curated, cited parameter sets as data files in `ucmd_builder/forcefields/`,
      assigned by graph-isomorphism match;
    - `gromacs-top`: an importer for GROMACS `.top`/`.itp` files, e.g. LigParGen output.
  - **Transforms after parameterization** are recorded in provenance, e.g. the ion charge
    scaling ζ per species. The builder refuses to mix sources whose conventions differ in one
    package.
  - **Library content for B1:**
    - argon (Rahman 1964) and SPC/Fw water (pre-approved);
    - the electrolyte working horse, once the author confirms its sources (B1 design).
      Candidates: Li⁺ (Jensen & Jorgensen 2006), PF₆⁻ (CL&P 2004), EC and EMC (later DMC, PC,
      MP); ζ = 0.75 for EC:EMC as in Lehnert 2025.
  - **Values come from sources the author approves.** Never fill gaps by guessing.
  - ✓ A test kit for every source checks:
    - net charge = formal charge (× ζ for ions);
    - every interaction is parameterized;
    - units are converted and the canonical order is preserved;
    - provenance is complete.
  - ✓ Tests reproduce each source table after unit conversion.
  - ✓ The same parameters reach the same package through `library` and through `gromacs-top`.
- **B1.4 Composition calculator.**
  - Inputs: salt and concentration (molarity or molality); solvent ratio (w:w or v:v); size
    target (ion pairs, atoms, or box length); density.
  - Outputs: molecule counts and box. Reports the concentration actually achieved after
    rounding.
  - ✓ Test: 1 M LiPF₆ in EC:EMC 3:7 w:w with 50 ion pairs and ρ = 1.2 g cm⁻³ (placeholder; take
    the real density from Landesfeind 2019 or Logan 2018) gives ≈ 178 EC, ≈ 352 EMC, ≈ 7.5k
    atoms, L ≈ 4.36 nm.
- **B1.5 Packing.**
  - Packmol driver: absolute path; seed; tolerance; use its periodic-boundary support if the
    installed version has it, otherwise pack into a box shrunk by the tolerance.
  - A built-in random-insertion packer for tests.
  - Minimum-distance check under PBC. Molecules are exported whole (unwrapped).
  - ✓ Deterministic per seed. No pair closer than the tolerance across periodic boundaries.
- **B1.6 Crystals.**
  - CIF import (ASE; spglib for symmetry); conventional/primitive cell; supercell from an integer
    matrix; reduction to the spec cell form; site-based type and charge assignment.
  - ✓ NaCl, LiF and graphite examples. Cell reduction preserves all interatomic distances.
- **B1.7 Initial conditions.**
  - Maxwell–Boltzmann velocities (seeded, COM removed).
  - **Wigner sampling** of harmonic normal modes, reimplemented from the equations in
    `WignerBase.py:22-31` and `HarmonicBase.py`, with the Hessian taken from a Gaussian fchk.
    Writes one package per sample.
  - ✓ Per-mode sample variances match the Wigner widths used in `WignerBase.py`
    (⟨Q²⟩ = 1/(2ω·tanh(ω/2k_BT)), ⟨P²⟩ = ω/(2·tanh(ω/2k_BT)), mass-weighted, atomic units) within
    statistical error.
  - ✓ The thesis fchk (`ws_rhombus/TPSSh_tzvpU/force.fchk`) yields the thesis frequencies.
- **B1.8 Determinism and provenance.** Recipe + seed → byte-identical package (timestamps
  excluded). Provenance stores recipe, versions, seeds and sources.
- **B1.9 Interoperability exporters:** LAMMPS data and extended XYZ. OpenMM export is the single
  converter in `tools/oracle/`, extended here to all force-field terms.
  - ✓ An exported EC box gives the same single point in OpenMM and in our engine (closes the
    loop with E2.9).

**Gate B1.**

### B2 GUI (PySide6, thin layer over B1)

The GUI comes in two steps (the author's request, 2026-11-12):

- **B2a, frontend preview**, right after M2a: B2.1, B2.2, the liquid part of B2.3 with library
  molecules, the export part of B2.5, and B2.6. The goal is that the author tries the tools and
  gives feedback early.
- **B2b, complete GUI:** everything else (SMILES and file input, crystals, validator
  highlighting, …).

- **B2.1 App shell.** Left panel: components and counts. Centre: 3D view. Right panel:
  properties of the selection. Bottom panel: validation and log.
  - The recipe model is the single source of truth. Every edit is a recipe change through
    `QUndoStack`.
  - ✓ pytest-qt round-trip: open, edit, save a recipe.
- **B2.2 3D view** (technology per spike S3): element colours and radii, bonds, cell and periodic
  images, picking feeds the properties panel; 10k–50k atoms stay interactive.
  - ✓ Screenshot tests via `QWidget.grab()`, reviewed by the agent (as images) and the author.
- **B2.3 Liquid workflow:** add molecules (file or SMILES), composition-calculator dialog,
  force-field template and ζ, density or box, packing in a background thread with progress and
  cancel.
- **B2.4 Crystal workflow:** CIF import; supercell dialog; a/b/c/α/β/γ display; site
  substitution and vacancies.
- **B2.5 Validate and export:** validator messages in the bottom panel (click → highlight
  atoms); export package + recipe; open an existing package read-only.
- **B2.6 Run preview.**
  - Starts a short local run of the exported package. The GUI calls the `ucmd` binary as an
    external program; its path comes from the machine profile, and `run.toml` from a template.
  - Shows temperature and energies live from the thermo file and plays the H5MD trajectory
    in the 3D view.
  - Talks to the engine only through its CLI and the spec'd files (invariant 2). The builder
    library itself still never runs MD.
  - ✓ pytest-qt test with a fake `ucmd` executable: start, progress, cancel, error display.

**Gate B2a:** the author builds a small LiPF₆/EC:EMC box in the GUI, runs it for a few
picoseconds and watches temperature, energy and the trajectory, without touching files.

**Gate B2:** the author builds 1 M LiPF₆ in EC:EMC and a LiF supercell in the GUI without
touching files, and both pass `ucmd check`.

---

## 7. Track A — Analysis (`ucmd-analysis`)

### A1 Analysis core

- **A1.1 Readers:** system package (masses, charges, molecule index, species) and H5MD;
  construction of an MDAnalysis Universe for standard tools; converter for external trajectories
  (OpenMM, GROMACS) into our H5MD profile.
- **A1.2 Frames:** molecular centres of mass per species and the barycentric frame (system COM
  subtracted), from unwrapped positions.
- **A1.3 Structure:** RDFs; coordination numbers (Li–O carbonyl per solvent, Li–F);
  solvation-shell composition; ion association (free ions, pairs, triple ions — Lehnert's
  FI/NTI/PTI definitions).
- **A1.4 Self-diffusion:** FFT-based MSD, automatic detection of the linear regime, Yeh–Hummer
  finite-size correction (viscosity as an input).
- **A1.5 Onsager coefficients.**
  - Einstein form of L_ij (Lehnert Eq. 3, after Fong et al. 2020) in the barycentric frame →
    κ and t⁺ (COM frame).
  - Transformation to the VOL frame (Lehnert Eqs. 7–9; partial molar volumes and mass fractions
    as inputs).
  - Green–Kubo variant from velocities as a cross-check.
- **A1.6 Uncertainty:** block averaging, replica statistics, fit-window sensitivity. Every
  reported number has an error bar.
- ✓ Synthetic tests with known answers: for uncorrelated random walkers, L₊₋ → 0 and κ equals the
  Nernst–Einstein value; ballistic and harmonic cases for the MSD.
- ✓ RDF and MSD agree with MDAnalysis's built-ins. Units are checked against hand calculations.

**Gate A1.**

### A2 Lehnert 2025 reproduction

- **A2.1** The Lehnert SI is in `../Lit`, and its protocol is summarized in
  `docs/lehnert2025-si-notes.md`: box sizes, run lengths, cutoffs, ζ, temperatures, force-field
  sources. Freeze the values actually used in `validation/lehnert2025/PARAMS.md`.
- **A2.2 Campaign tool `ucmd-launch`** (D13; generalizes the thesis `builder.py` +
  `dynstart.bash`): N replicas with different seeds, run directories, executors `local` and
  `slurm` (array template), resumable from checkpoints, status overview. Cluster specifics
  (modules, partitions, scratch) are settled here.
- **A2.3 Production** with our engine. Cross-check one state point with OpenMM.
- **A2.4 Report:** κ(c), t⁺_VOL(c) and ion association, compared with Lehnert's MD and eNMR data
  and with the Landesfeind 2019 experiments.

**Gate A2 = M4.**

---

## 8. Validation ladder

| # | System | What it checks | Reference | Task |
|---|---|---|---|---|
| 1 | 1D/3D harmonic | VV order and shadow energy, reversibility, DOF, NeNePo golden trajectory | analytic; NumPy transcription of `VV_8_12.py` | E1.5 |
| 2 | Argon 864 (Rahman 1964) | LJ, PBC, neighbour list, CSVR, pressure, D, drift | OpenMM, identical setup; Rahman D | E1.12 |
| 3 | NaCl crystal | Ewald, PME, virial | Madelung constant 1.747565 | E2.3–E2.4 |
| 4 | Water: SPC/Fw (flexible), SPC/E (rigid) | bonded terms, PME, RATTLE, NHC, barostat | OpenMM | E2.5–E2.9 |
| 5 | Pure EC at 313 K | OPLS dihedrals, 1-4 scaling, density | OpenMM | E2.9 |
| 6 | LiPF₆ in EC (small) | ion–solvent terms, ζ scaling | OpenMM | E2.9 |
| 7 | 1 M LiPF₆ in EC:EMC 3:7 w:w | full electrolyte, performance | OpenMM; Lehnert 2025; Landesfeind 2019 | E2.9, A2 |
| 8 | Argon via ASE LJ over the socket | external transport, units on the wire | in-process LJ | E3.1 |
| 9 | Ag₄ (thesis) | QC adapters, provider state | thesis trajectories | E3.9 |

Generic checks for **every** provider, at any rung: the finite-difference force test, the
finite-difference strain-virial test, energy terms summing to the total, and NVE drift no worse
than the oracle's.

---

## 9. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Scope: an engine with PME, constraints and a barostat is a large project | small tasks and gates; analysis proceeds on OpenMM trajectories; OpenMM-as-provider (E3.7) as production fallback |
| Speed far below GROMACS/OpenMM | the value is modularity; measure before optimizing (E2.8) |
| HDF5 build friction (locally and on the cluster) | spike S1 with a documented fallback |
| Unit and sign errors hidden by modular boundaries | one unit system; finite-difference force and virial tests for every provider; oracle comparisons |
| Spec churn across repos | contract tests on fixtures; semver; a spec change = ADR + one coordinated update |
| Unsourced or wrong force-field parameters | pluggable parameter sources (ADR 0008) with citations in provenance; the author approves every source; a test kit for sources; tests against source tables |
| Agent drift over many sessions | STATUS.md, ADRs, design docs, one task per session, gates |
| QC programs not installed locally | parser tests on recorded thesis outputs; a mock executable for failure injection; real runs on the cluster |
| Statistical noise in Onsager cross terms | replicas and error bars (A1.6); run lengths taken from the paper |
| Production cost: Lehnert uses 3 replicas × up to 170 ns at 1 fs per state point (≈ 5×10⁸ steps, 7k atoms, PME) | agree a performance target in E2.8; OpenMM-as-provider on the GPU (E3.7) as the production fallback |

---

## 10. Decisions for the author (confirm at Gate 0)

1. **Units:** ✅ decided 2026-11-11: nm/ps/amu/kJ mol⁻¹ ([ADR 0001](docs/decisions/0001-units.md)).
2. **Repos:** ✅ public on GitHub in the organization
   [`mines-of-morja`](https://github.com/mines-of-morja), with the names proposed in D1.
   Licence ✅ Apache-2.0 for all repos. Commits use the organization email (repo-local git
   config). Decided 2026-11-11/12.
3. **Formats:** JSON + NPY package, TOML configs, H5MD trajectories (D4).
4. **GUI stack:** ✅ decided 2026-11-11: PySide6 + pyvistaqt, pending spike S3. A web-based
   viewer or a Rust front end may be added later on top of the same builder library.
5. **Benchmark:** 1 M LiPF₆ in EC:EMC 3:7 w:w at 20 °C (the system Lehnert validated with eNMR),
   plus the paper's SI.
6. **Force-field sources:** ✅ direction decided 2026-11-12. Sources are open and pluggable
   ([ADR 0008](docs/decisions/0008-pluggable-force-field-sources.md)), with an open-source
   working horse and our own force field as a fallback.
   - The concrete working-horse parameter set is proposed in the B1 design and needs the
     author's confirmation.
   - Ringsby 2021 is no alternative: it used Maestro/MacroModel parameters as well.
7. **Installs:** `libhdf5-dev` (needs sudo), `uv`, OpenMM, Packmol.
8. **Agent setup:** Claude Code reads `CLAUDE.md`; for another agent, copy or symlink it to
   `AGENTS.md`. One agent sequentially, or two in parallel (§3).
9. **Cluster:** ⏸ deferred to A2.2. The constraint that applies now: everything stays
   local-first and cluster-capable (D13, ADR 0002).
10. **Early frontend** (the author's idea, 2026-11-12): B2a after M2a (§3), with the run
    preview B2.6, in which the GUI starts `ucmd` as an external program. To confirm with the
    B1 design.

---

## 11. Kickoff prompts

Start of P0:
> Read CLAUDE.md, PLAN.md and docs/nenepo-audit.md. Do tasks P0.1 and P0.2 only — no physics
> code. Then update docs/STATUS.md and give me a summary, including what you need from me.

Spec:
> Do P0.3 and P0.4: draft spec v0.1 with schemas, fixtures and the validator. Present the spec
> decisions as a list I can approve or change. Don't tag the spec.

Spikes and design:
> Do spikes S1–S4 from P0.5. Time-box each and ask before installing system packages. Write one
> ADR per spike, then write docs/design/E1.md. Stop at Gate 0 and report.

Each task after Gate 0:
> Next task: E1.<n>. Re-read its acceptance criteria in PLAN.md, write the tests first,
> implement, run fmt/clippy/tests, update STATUS.md, commit. Stop after this task.

Each gate:
> We're at Gate E1. Write the gate report: what was built, evidence for each acceptance criterion
> (numbers and test names), deviations, open questions, proposed changes to PLAN.md.
