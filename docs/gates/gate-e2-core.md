# Gate report — E2 core and milestone M2a ("the core stands")

- **Date:** 2026-11-13.
- **Where:** branch `e2` of ucmd-engine; branch `e2` of this repo (oracle references, design
  docs, this report).
- **Design:** [design/E2.md](../design/E2.md), approved 2026-11-12, with every §13
  recommendation and the hardware requirement of [ADR 0010](../decisions/0010-swappable-hardware.md).
- **Next, after approval:** the GUI preview B2a. Its design is ready for review:
  [design/B2a.md](../design/B2a.md).

## 1. Summary

- **The engine runs the electrolyte.** The builder's 1 M LiPF₆ in EC:EMC 3:7 box (7036 atoms)
  is minimized and runs NVT with PME and Nosé–Hoover chains. M2a passes every criterion
  (`ucmd-engine/validation/m2a/REPORT.md`, engine `6106ba7`).
- **Agreement with OpenMM is at round-off level.**
  - Single molecules (EC, EMC, LiPF₆ and a test molecule with every bonded form): energy terms
    within 3×10⁻¹⁴, forces within 10⁻¹⁵ of max |F|. Criterion: 10⁻⁸.
  - The full box with PME, before and after minimization: total energy within 1.6×10⁻¹³,
    forces within 10⁻¹³ (rms). Criteria: 10⁻⁶ and 10⁻⁵.
  - The virial pressure agrees with a finite difference of OpenMM's energy to 10⁻⁶.
- **Same results on any hardware (ADR 0010).**
  - The CPU reference backend is bitwise reproducible across machines: GitHub's CI reproduces
    the golden hash computed on the workstation.
  - It is also bitwise independent of the thread count, and a restart continues bitwise:
    checked for the full box in M2a.
  - 16 threads are about 7.5× faster than one on the workstation (8 cores, 16 threads).
- **State:**
  - 89 tests, plus one slow validation test (`--ignored`);
  - clippy `-D warnings` clean; dependency rules enforced; builds with and without HDF5;
  - CI green on `e2`.

## 2. Acceptance criteria and evidence

| Task | Criterion | Evidence |
|---|---|---|
| E2.R | bitwise identical on every machine | `libm` for transcendental functions, own normal and gamma samplers, scalar FFT. `tests/reproducibility.rs`: a 300-step argon CSVR run gives the committed SHA-256 on the workstation and on GitHub's runners, in debug and release, with Rust 1.99 and 1.100 |
| E2.1 | test kit per term; molecules vs OpenMM to 10⁻⁸ | bonds, angles, proper and improper dihedrals (periodic, Ryckaert–Bellemans, OPLS Fourier, harmonic) pass the test kit; `tests/oracle_molecules.rs`: EC, EMC, LiPF₆, all-forms molecule, energy terms ≤ 3.2×10⁻¹⁴, forces ≤ 9.5×10⁻¹⁶ of max \|F\| |
| E2.2 | EC/EMC decomposition matches OpenMM term by term | the same test, per term (bond, angle, dihedral, improper, lj, lj14, coulomb) |
| E2.3 | Madelung to 10⁻⁸; test kit | `tests/ewald_madelung.rs`: 1.747564594633, relative error 8.9×10⁻¹⁶; Ewald passes the test kit in a triclinic cell |
| E2.4 | PME vs Ewald ≤ 10⁻⁵ rms; vs OpenMM 10⁻⁶ (E), 10⁻⁵ (F) | converges to Ewald with order and grid; a charge pair agrees to 10⁻⁸. `tests/oracle_pme.rs`, full LP57 box, grid 70³: energy terms ≤ 1.3×10⁻¹³, total 1.6×10⁻¹³, forces 2.6×10⁻¹⁵ of max \|F\| |
| E2.0 | LJ cluster minima; packed box below the threshold | LJ₇ −16.505384 ε, LJ₁₃ −44.326801 ε (Wales & Doye 1997); the packed LP57 box goes from max \|F\| 18 838 to 99.9 kJ mol⁻¹ nm⁻¹ in 618 FIRE steps (45 s) |
| E2.6 | canonical ⟨K⟩, Var(K); conserved quantities | interacting test system (64 argon-mass particles, quartic traps, ring springs), 1 ns: NHC ⟨K⟩ −0.02 %, Var(K) −2.7 % ± 1.6 %, ⟨−r·F⟩ +0.06 %, conserved drift 1.2×10⁻⁴ of ⟨K⟩. Langevin BAOAB: ⟨K⟩ −0.45 %, Var(K) −5.5 % ± 2.1 %. Over 10 ns (`--ignored`): all within 0.5 % (Var(K) within one block error). BAOAB at ωΔt = 1: ⟨x²⟩ = kT/k to +0.23 %, ⟨v²⟩ = (kT/m)(1 − (ωΔt/2)²) to +0.18 % |
| E2.6 | bitwise restart with each thermostat | `tests/cli.rs`: CSVR, NHC and Langevin, 200 steps = 100 + restart + 100; checkpoint format v2 stores the chain; v1 files are still read |
| §9 | bitwise identical for any thread count | unit test: forces, energy terms and virial for 1, 4 and 16 threads, with PME and with direct Coulomb; a deliberately thread-dependent chunking fails it. A second unit test: a neighbour list built at other positions (as after a restart) gives bitwise the same result. LP57 box: forces and a 100-step NHC run are byte-identical for 1, 4, 16 threads |
| M2a | the chain of design §10 | **PASS** (`validation/m2a/REPORT.md`): single points before and after minimization within 1.6×10⁻¹³ (energy) and 10⁻¹³ (forces, rms) of OpenMM; engine defaults give OpenMM's α and grid bitwise; 10 ps NVT with ⟨T⟩ = 298.34 ± 0.26 K over 5–10 ps and σ_T = 2.87 K (canonical 2.90 K); a restart after 5 ps byte-identical, checkpoint files included; 1, 4, 16 threads byte-identical; 70 ms/step on 16 threads |

## 3. Deviations from the design

- **Test locations:** the thermostat sampling tests live in `ucmd-md/src/dynamics.rs`, not in
  `thermostat.rs` and `langevin.rs`. The thread test is a unit test in `nonbonded.rs`, not
  `tests/threads.rs`, and M2a repeats it end to end. The Madelung test is
  `tests/ewald_madelung.rs`.
- **Thermo column name (an E1 deviation, now fixed):** the engine wrote `conserved_kjmol`;
  spec/run-config.md names it `conserved_energy_kjmol`. The engine now follows the spec, and a
  test pins the spec'd names. H5MD already used `conserved_energy`.
- **An E1 gap, still open:** spec/checkpoint.md says a forced restart (`--force`) is recorded
  in the trajectory provenance. E1 did not implement that record (§6, question 3).

## 3a. Found and fixed during M2a

- **Restarts of molecular runs were not bitwise identical** after the threading commit.
  - **Cause:** the pair chunks were cut by the neighbour list's pair counts. A restart rebuilds
    the list at the restart positions, while the continuous run kept the list of an earlier
    step. So the chunk boundaries, and with them the rounding of the force sums, differed.
  - **Why the earlier tests missed it:** the argon restart tests use the Lennard-Jones
    provider, which is not chunked.
  - **Fix** (`4a34e70`): the boundaries now depend only on the atom count. A new unit test
    builds the list at displaced positions and requires bitwise equality; it fails with the
    old code.
  - **Check:** M2a's restart check, and the electrolyte example (1000 + restart + 1000 steps
    equal 2000 steps, byte for byte).
- **The swings of the conserved energy** in the first 0.3 ps (about 400 kJ/mol) are not a
  thermostat error.
  - They come from velocity Verlet with flexible C–H bonds at 1 fs (vibration period about
    11 fs), whose bounded error is of order (ωΔt)².
  - The minimized structure starts all bonds in phase, so the errors add up until the
    vibrations dephase.
  - Evidence: the same swings appear in NVE without a thermostat, and halving Δt shrinks them
    4.2-fold (M2a §6).
  - Lehnert's SI uses velocity Verlet with 1 fs and mentions no constraints, so this is their
    protocol too. Constraints on X–H bonds (E2.5) would allow longer steps later.

- **Two engine fixes found on the way to the gate:**
  - **Checkpoint floats** (`5fd2871`): the restart left the thermostat work off by one ulp.
    serde_json's default float parser is not correctly rounded: 7520 of 39 993 test values
    changed in the round trip. The same JSON carries the Nosé–Hoover chain state, so bitwise
    restarts held only by luck. The fix enables `float_roundtrip`. The restart tests now
    compare whole checkpoint files.
  - **XYZ frames** (`a8df7a9`): frames are flushed when complete, so `ase gui` can open the
    trajectory of a running simulation (docs/testing.md §8a).
- **Checkpoint floats, a second effect:** the same parser also read `system.json`. So charges,
  σ and ε were sometimes one ulp off the values in the package, while OpenMM read them exactly.
  The engine now reads them exactly. That is also why M2a's 10 ps differ in detail from an
  earlier run of the same chain.
- **The pressure at the placeholder density is high and still falling.**
  - M2a, mean per ps: 6293, 4713, 3552, 3166, 2700, 2550, 2352, 2036, 1821, 1769 bar.
  - The engine computes it correctly: its analytic virial agrees with a finite difference of
    OpenMM's energy under box scaling, to 7×10⁻⁸ for the packed box and 1.3×10⁻⁶ for the
    minimized one.
  - The falling trend shows that the packed and minimized box is still relaxing towards a
    liquid structure. So 10 ps do not tell whether the force field's density matches the
    builder's placeholder of 1.2 g/cm³.
  - Lehnert's protocol sets the density by 3 ns NPT at 1 atm. That needs the barostat (E2.7)
    before production (§6, question 4).

## 4. Implementation choices for review

1. **Nosé–Hoover chains:**
   - fourth-order Suzuki–Yoshida with five stages, one multiple-time-step loop;
   - the chain does nothing when there are no degrees of freedom (Q₁ would be 0).
   - LAMMPS's `fix nvt` uses the same masses, without Yoshida weights by default.
2. **Langevin:** the centre-of-mass degrees of freedom count when Langevin noise is on and
   nothing removes the COM momentum, as in GROMACS and OpenMM.
3. **Forced restart across a thermostat change** (e.g. CSVR equilibration → NHC production):
   a warning, and the chain starts fresh. Without `--force`, a missing chain state is an error.
4. **Threads:**
   - the rows of the pair list are cut into at most 64 chunks, by the atom count alone (equal
     shares of the all-pairs count), never by the list, so that restarts stay bitwise;
   - PME is split by grid planes;
   - the thread count comes from the machine profile, by default all logical cores;
   - new dependency `rayon` 1.12 (MIT/Apache-2.0, pure Rust), as in the approved design.
5. **M2a protocol details:**
   - velocities at 298.15 K, from Lehnert's preparation at 25 °C;
   - COM momentum removed every 100 steps, GROMACS's default `nstcomm`, because smooth PME
     does not conserve momentum exactly;
   - truncated LJ without tail correction, as Lehnert's LAMMPS setup.

## 5. Speed

- The full box with a 1.4 nm cutoff has about 5×10⁶ pairs per step.
- On the workstation (Ryzen 7 2700X, 16 threads), one step takes about 70 ms. At 1 fs that is
  1.2–1.3 ns/day; one thread takes 0.57 s per step.
- Most of the time goes into the real-space kernel (erfc and exp per pair).
- **For the transport study this is too slow.** Lehnert's protocol needs at least about 60 ns
  per simulation and three simulations per state point: some 150 days per state point here. The ways forward are in PLAN.md and
  need a decision (§6, question 2).

## 6. Questions for the author

1. **Gate E2 core:** approve, and merge `e2` into `main` of ucmd-engine and of this repo?
2. **Compute for production:**
   - **E2.8, speed up the reference backend:** tabulated kernels, a better cell list and the
     real-to-complex FFT. My estimate is 3–5×. It stays bitwise reproducible.
   - **E3.7, OpenMM as an alternative backend** on the Radeon VII (OpenCL). Results must agree
     numerically at start-up and statistically in their results (ADR 0010). Likely tens of
     ns/day for this box.
   - **A cluster** (ADR 0002, deferred).

   My recommendation: E3.7 first for production throughput, with the reference backend as the
   check, and E2.8 later.
3. **Forced restarts:** record them in the H5MD provenance as `/parameters/ucmd/restarts`, a
   list of step, time and the overridden differences. The location is free under spec v0.1.
   OK?
4. **Density:** the barostat (E2.7) comes next among the physics tasks, before the first
   state point, so that the density can be set by NPT as in Lehnert's protocol. Agreed? It
   also tells us which density the working-horse force field gives (§3a).
5. **B2a design:** questions 1–5 in [design/B2a.md](../design/B2a.md) §11.
6. **Still open from before:** Gate B1a; the Landesfeind 2019 SI for densities; the validator
   packaging fix.
