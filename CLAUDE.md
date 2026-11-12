# UnitcellMD — instructions for coding agents

UnitcellMD is a modular molecular-dynamics ecosystem for large periodic systems. The first target
is Li-ion battery electrolytes, e.g. LiPF₆ in EC:EMC. It succeeds the author's MSc code
NeNePo_builder (on-the-fly Ag₄ dynamics; see `docs/nenepo-audit.md`).

- Roadmap and acceptance criteria: `PLAN.md`.
- Progress: `docs/STATUS.md`. **Read it at the start of every session.**

## The one rule

The engine owns the dynamics, force providers own the physics, the builder owns the initial
system, analysis owns the interpretation. Nothing crosses these lines except through the formats
and protocols defined in `spec/`.

## Workspace layout

```
UnitcellMD/            this git repo: plan, spec, fixtures, cross-repo tools
├── CLAUDE.md  PLAN.md
├── docs/              STATUS.md, nenepo-audit.md, decisions/ (ADRs), design/ (one per phase)
├── spec/              formats, units, provider contract, JSON Schemas, fixtures, validator
├── tools/oracle/      OpenMM reference calculations (validation only)
├── _reference/        read-only clone of NeNePo_builder (gitignored)
├── ucmd-engine/       own git repo: Rust Cargo workspace, binary `ucmd`, Python bridge
├── ucmd-builder/      own git repo: Python library, CLI `ucmd-build`, PySide6 GUI
└── ucmd-analysis/     own git repo: Python library, CLI `ucmd-analyze`
```

The `ucmd-*` folders are independent git repositories, ignored by this one. Run git commands
inside the repo you are changing.

## Architecture invariants

Changing any of these needs an ADR approved by the author.

1. `ucmd-md` (integrators, thermostats, run loop) depends only on `ucmd-core` and `ucmd-force`,
   never on a provider crate. Providers are wired by name in `ucmd-cli`. Keep this enforced by the
   Cargo dependency graph.
2. Components never import each other's code. They communicate only through the spec'd files
   (system package, `run.toml`, H5MD trajectory) and the provider protocol (Rust trait in-process,
   i-PI socket out-of-process).
3. **Units, internally and in all files:** nm, ps, amu, kJ/mol, e, K; pressure in bar in configs
   and logs.
   - Convert only at boundaries: importers, external providers, GUI display.
   - Physical constants live in one module per language, derived from CODATA 2018. Never type a
     rounded literal elsewhere.
   - Config keys carry their unit: `timestep_fs`, `cutoff_nm`, `temperature_K`, `pressure_bar`.
   - Decided in ADR 0001.
4. **Atom order is canonical:** components in manifest order → instances → template atom order.
   Outputs always use canonical order, even if a kernel reorders atoms internally.
5. Topology, masses and charges are immutable during a run and come from the system package. The
   engine has no element table and never guesses a mass.
6. Forces are F = −∂E/∂r; the virial is W = −∂E/∂ε (`spec/units.md`). The engine checks the
   length and finiteness of every provider result before using it.
7. **Errors propagate.** Never replace a failed or missing evaluation with zero, stale or default
   values. On a provider error, write an emergency checkpoint of the last good state and exit
   non-zero.
8. Every random number comes from a seeded, checkpointable RNG. A single-threaded run is bitwise
   reproducible, including across a checkpoint restart.
9. Every output file records provenance: tool version and git hash, spec version, the fully
   resolved config, system-package hash, provider identities.
10. Thermostats, barostats and constraints are operators composed with the integrator
    (PLAN.md §2.5), never code inside velocity Verlet.
11. **Local-first, cluster-capable** (ADR 0002).
    - A classical run needs only `ucmd`, a system package and `run.toml`.
    - Scheduler code lives only in the execution layer (`ucmd-launch`).
    - Machine-specific paths and settings live in the per-machine profile, never in packages
      or `run.toml`.

## How to work

- Work task by task from PLAN.md (IDs like `E1.5`). Stop at the end of a task.
- Each phase starts with a design doc `docs/design/<phase>.md`: types, interfaces, files touched,
  acceptance tests, open questions. Do not implement until the author approves it.
- Phase ends are gates. Stop and report what was built, the evidence, any deviations and open
  questions.
- Physics code is test-first. Write the validation test before or together with the
  implementation: finite-difference force check, energy conservation, analytic case, oracle
  comparison.
- Never loosen a tolerance, skip a test, or delete a failing test to get a green run. If a
  criterion looks wrong, report it with numbers and ask.
- Evidence over claims. Validation results go in `<repo>/validation/<case>/REPORT.md`, with the
  numbers, the commands and the versions used.
- At the end of each task, update `docs/STATUS.md` (done, evidence, next, open questions). Record
  interface or convention decisions as short ADRs in `docs/decisions/NNNN-title.md`.
- From NeNePo_builder, port behaviour, not code. Reimplement from the equations, with tests. Do
  not copy files with third-party author headers (audit §7).
- Make small commits per task: `<area>: <what>`, with the why in the body.
- **The repos are public on GitHub, in the organization `mines-of-morja`.**
  - Push only when the author asks or after an approved gate.
  - Never force-push or rewrite published history.
  - Never commit secrets, the PDFs in `../Lit` or other copyrighted material, large binary
    outputs, or absolute paths from the author's machine.

## Ask the author before

- changing anything under `spec/` once a version is tagged;
- choosing physical parameters (force-field values, charge scaling ζ, validation cutoffs). Every
  parameter must cite a source. **Never invent one.** Rahman-1964 argon and SPC/Fw water are
  pre-approved for fixtures;
- adding a dependency that needs system packages or sudo (e.g. `libhdf5-dev`), or a heavy Python
  dependency;
- deviating from an acceptance criterion or from the phase order;
- removing or changing behaviour that came from the thesis code.

## Conventions

**Rust (`ucmd-engine`)**
- Stable toolchain via rustup, edition 2024.
- `cargo fmt`, `cargo clippy --all-targets -- -D warnings`, `cargo test`.
- Errors: `thiserror` in libraries, `anyhow` only in the CLI. No `unwrap`/`expect` in library code
  outside tests.
- Every public item documents its units. Physics uses f64.
- Benchmarks with criterion. Slow validation tests are `#[ignore]` and run explicitly.

**Python (builder, analysis, spec validator, bridge)**
- Python ≥ 3.12 (3.13 locally). One virtualenv per repo: `uv venv` or `python3 -m venv .venv`.
- Debian's system Python is externally managed. Never `pip install` into it, and never use
  `--break-system-packages`.
- ruff (lint and format), pytest, type hints on the public API. NumPy float64 arrays in spec units.

**External programs** (Packmol, ORCA, Gaussian, …) are called by absolute path from config and
probed at start-up. **On this workstation `/usr/bin/orca` is the GNOME screen reader, not the
ORCA quantum-chemistry program.**

## Environment (author's workstation)

- 16 cores, 31 GB RAM, AMD GPUs (RX 580, Radeon VII), so no CUDA. The engine is CPU-only; GPUs are
  used only through external providers (OpenMM OpenCL, PyTorch ROCm).
- Rust 1.99.1 stable via rustup in `~/.cargo`. If `cargo` is not found, run
  `. "$HOME/.cargo/env"`.
- Python 3.13.5; `python3 -m venv` works (pip 25.1.1 inside venvs).
- HDF5: the runtime library (libhdf5 1.14, serial) is installed; the headers (`libhdf5-dev`) are
  not. cmake, gcc and pkg-config are available.
- Not installed: uv, OpenMM, Packmol, GROMACS, LAMMPS, ORCA, Gaussian.

## Commands

Run these inside the repo concerned, and keep this table current.

| Repo | Setup / build | Test | Lint / format / checks |
|---|---|---|---|
| spec (validator) | `cd spec/validator && python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'` | `.venv/bin/pytest` | `.venv/bin/ruff check .`; fixtures: `spec/fixtures/_generators/generate.py` |
| tools/oracle | `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt` | `.venv/bin/python -m pytest test_oracle.py` | — |
| ucmd-engine | `cargo build --workspace` | `UCMD_REQUIRE_SPEC=1 cargo test --workspace` | `cargo fmt --all --check`; `cargo clippy --workspace --all-targets -- -D warnings`; `scripts/check-architecture.sh`; `cargo build --workspace --no-default-features`; physics: `validation/argon/run.sh` |
| ucmd-builder | `python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'` | `.venv/bin/pytest` | `.venv/bin/ruff check .`; `.venv/bin/ruff format --check .` |
| ucmd-analysis | same as ucmd-builder | `.venv/bin/pytest` | same as ucmd-builder |

Each component repo has a CI workflow in `.github/workflows/ci.yml` that runs the same checks.
In Python repos, `tests/test_architecture.py` enforces the import boundaries between
components.

## Reference material

- `../Lit/Lehnert_2025_J._Electrochem._Soc._172_050523.pdf` and `…_SI.pdf` — the target
  benchmark (OPLS-AA, scaled ion charges, Onsager coefficients). The SI's MD protocol and
  particle numbers are summarized in `docs/lehnert2025-si-notes.md`.
- `../Lit/Landesfeind_2019_…pdf`, `../Lit/Logan_2018_…pdf` — experimental transport and density
  data.
- NeNePo_builder: https://github.com/PyProgMo/NeNePo_builder (commit fd7f1e2 audited), cloned to
  `_reference/`.
