# Gate E1 report — minimal engine (provisional)

- **Date:** 2026-11-12. Prepared by the agent while the author was away.
- **Where:** branch `e1` of `ucmd-engine` (14 commits), built on spec v0.1 of branch `phase-0`
  of the umbrella repo.
- **Status:** E1 was started **provisionally, before Gate 0**, so that review and merge can
  happen together. If Gate 0 changes the spec, E1 adapts (the contract test shows exactly
  where).

## 1. Summary

- All twelve E1 tasks are implemented, and every acceptance criterion is met with measured
  numbers.
- The engine runs real MD end-to-end: check → run → checkpoint/restart → export → rerun.
- It agrees with OpenMM at round-off level for single points, and statistically for 100 ps of
  argon dynamics.
- It reproduces the thesis integrator to 2.5×10⁻¹⁴.
- State: 48 tests; clippy `-D warnings` clean; dependency rules enforced; builds with and
  without HDF5.

## 2. Acceptance criteria and evidence

| Task | Criterion (PLAN.md) | Evidence |
|---|---|---|
| E1.1 | minimum image = brute-force image search; wrap round trip | proptests on random reduced triclinic cells (`ucmd-core::cell`) |
| E1.2 | test kit catches broken providers | sign flip, missing ½ and off-by-one all detected (error > 0.1); `Guarded` rejects wrong length, NaN, missing energy, inconsistent terms; `Composite` sums and prefixes |
| E1.3 | analytic providers pass the test kit | tether (offset anchors) and pair spring (triclinic, minimum image): FD forces and strain virial < 10⁻⁵, momentum < 10⁻¹⁴. **Found a spec error**, see §4 |
| E1.4 | readers report the validator's codes | contract test: 4 valid packages load; 20 invalid packages and 5 invalid run configs give exactly the Python validator's code |
| E1.5 | VV shadow energy, 2nd order, reversible, NeNePo golden | max\|ΔE\|/E₀ = 1.0035 × (ωΔt)²/4 (1.0040 after 10⁶ steps, no drift); error ratio 4.019; reversal to 10⁻¹⁰; **thesis VV (`VV_8_12.py:72-76`) reproduced to 2.5×10⁻¹⁴** |
| E1.6 | CSVR canonical | 100 oscillators, 300 K, 400 ps: ⟨K⟩ +0.10 %, Var(K) −1.9 %, ⟨U⟩ +0.12 %; conserved drift 9.4×10⁻⁶ of ⟨K⟩ |
| E1.7 | LJ vs OpenMM single point | argon-864: energy 1.1×10⁻¹⁵ (truncate) / 5.6×10⁻¹⁵ (shift), forces 1.5×10⁻¹⁴ max/rms, virial 3.0×10⁻¹⁵; tail energy equals the oracle's to 10⁻⁹ (criteria: 10⁻⁸ / 10⁻⁶ / 10⁻⁶) |
| E1.8 | neighbour list = all pairs | equal to 10⁻¹² incl. triclinic; rebuild only after skin/2. Benchmark: see §3 |
| E1.9 | H5MD valid and readable | engine trajectories pass `ucmd-spec validate-trajectory` (also after restarts); MDAnalysis compatibility shown in spike S1 |
| E1.10 | bitwise restart; emergency checkpoint | 200 steps = 100 + restart + 100 **bitwise**, with CSVR; thermo files byte-identical; failure at step 7 → emergency checkpoint of step 6; a changed config is refused |
| E1.11 | CLI and provenance | `check`, `run`, `singlepoint`, `export`, `rerun`; git hash and spec version in every output; rerun reproduces recorded energies exactly |
| E1.12 | argon vs OpenMM | **PASS 8/8** (`ucmd-engine/validation/argon/REPORT.md`): ⟨U⟩ −4290.5 ± 0.6 vs −4290.3 ± 0.9 kJ/mol, ⟨T⟩ 92.93 vs 92.91 K, ⟨P⟩ 306 ± 2 vs 308 ± 3 bar, g(r) peaks within one bin and 1 % in height, D = 2.41 vs 2.31 ×10⁻⁵ cm²/s (Rahman 1964: 2.43), drift −7.8×10⁻⁵ vs 1.1×10⁻⁴ kT/ns/DOF |

**Speed (one core, no optimization yet):** 864 LJ atoms at 186–190 ns/day with dt = 4 fs. The
same 100 ps took 46 s in ucmd and 259 s on OpenMM's double-precision Reference platform.

## 3. Deviations from PLAN.md

- **E1.7:** the `force-switch` cutoff mode is deferred to E2. Lehnert's LAMMPS setup uses a
  plain cutoff, and nothing in E1 needs it.
- **E1.8:** no criterion benchmarks yet. Timings come from real runs; systematic benchmarking
  belongs to E2.8 (performance).
- **E1.11:** `rerun` writes a TSV table, not H5MD observables. Simpler, and enough for the NeNePo
  use case; it can grow later.
- **E1.11, new command:** `ucmd export` turns a checkpoint into a package. It was needed to
  continue an equilibrated state under a new protocol; E1.12 uses it.
- `remove_angular` acts only at the start, not periodically (non-periodic clusters only; E3
  topic).

## 4. Spec corrections made during E1 (branch `phase-0`, all small)

1. **Virial strain convention** (units.md §4). The test kit showed that the column form
   (1+ε)·r gives Wᵀ for asymmetric virials (external fields). Now ASE's row form
   r_b → r_b + ε_ab·r_a, so that W_ab = Σ r_a F_b in general. Symmetric cases are unaffected.
2. **Element symbols** are enumerated in the schema, so both readers reject `"Xx"`. New invalid
   fixture `unknown-element`.
3. `E_TOML` code for unparsable `run.toml`; the full check order of both readers is written
   down.
4. `author_name` added to the machine profile, for `/h5md/author`.

## 5. Design decisions taken in E1 (to review)

| Decision | Where | Why |
|---|---|---|
| `Observer`/`Snapshot` live in `ucmd-force` | design/E1.md §6 | the run loop and the writers share them without depending on each other |
| double-buffered step (spare positions/velocities/forces) | `ucmd-md::dynamics` | a provider error never corrupts the state; emergency checkpoints at no copy cost |
| Maxwell–Boltzmann velocities rescaled to exactly the target T after COM removal | `ucmd-md::velocities` | reproducible, common practice (E1 design question 2) |
| the COM momentum is always removed once at the start (N_dof = 3N − 3) | spec default | as written in run-config.md |
| CSVR scaling factor always positive | `ucmd-md::thermostat` | GROMACS convention |
| tail pressure via the virial route (LAMMPS/GROMACS), not as the strain derivative of E_tail | `lj.rs` | standard; documented in the code |
| checkpoint = JSON metadata + raw f64 arrays | `ucmd-io::checkpoint` | readable and exact; versioned |
| config fingerprint excludes `run.steps` | `RunConfig::fingerprint` | a restart may extend a run, nothing else |
| extended XYZ in Å | `ucmd-io::xyz` | viewers expect Å (format boundary) |

## 6. Proposed next steps

1. **Author:** review Gate 0 (`docs/gates/gate-0.md`) and this report. Then merge `phase-0` →
   `main` (umbrella) and `e1` → `main` (engine).
2. **Next track:**
   - **E2** (molecular force fields: bonded terms, exclusions and 1-4 pairs, Ewald/PME,
     constraints) can start immediately with the existing fixtures: `water-2` (SPC/Fw) and
     `nacl-crystal` (Madelung).
   - **B1** (headless builder) needs the solvent force-field source decision first
     (PLAN.md §10.6).

## 7. Decision (author, 2026-11-12)

**Gate E1 is approved.**
- The author tested the engine hands-on with docs/testing.md: "testing done. The setup and
  testing looked fine for the Argon startup."
- §3 (deviations) and §5 (design decisions) stand.
- `e1` is merged into `main` of ucmd-engine.

