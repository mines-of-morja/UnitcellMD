# 0010 — Swappable hardware, reproducible results

- **Status:** accepted 2026-11-12 by the author: "adding hardware must be swapped in and out,
  so if someone else runs the software on their computer it should be able to use different
  hardware but run the same program and get the same results (just running faster or
  slower)."
- **Context:**
  - UnitcellMD runs on laptops, on the author's workstation (16 cores, AMD GPUs) and on
    cluster nodes. GPU backends arrive later (OpenMM through the provider interface, E3.7).
  - Floating-point results depend on the order of operations and on the math library. MD
    trajectories are chaotic, so a difference in the last bit grows until two trajectories
    are unrelated after some picoseconds.
  - "The same results" therefore has to be defined per level, and each level needs a test.
- **Decision:**
  1. **Physics and hardware are separate.**
     - The system package and `run.toml` describe the physics (model, parameters, protocol).
     - The machine profile describes the hardware: threads, scratch, executables, and later
       GPU backends.
     - Nothing in a package or `run.toml` names hardware, so switching hardware never edits
       them. This extends ADR 0002.
  2. **Bitwise level: the reference CPU backend.** The same version of `ucmd` gives
     bit-identical trajectories on any machine and with any number of threads. This requires:
     - every transcendental function in physics and random sampling from the pure-Rust `libm`,
       never the platform's math library (which differs between systems and versions);
     - own samplers (normal, gamma) on top of the seeded ChaCha8 stream;
     - no code paths that depend on CPU features: FFT through the scalar planner, no
       `target-cpu=native`, no fast-math, no FMA contraction (Rust's default);
     - parallel loops over fixed-size chunks with reductions in a fixed order, so the thread
       count cannot change a result.

     A golden-hash test proves it. It runs a fixed simulation and compares the SHA-256 of the
     final state with a committed value, in CI on GitHub's machines and locally.
  3. **Numerical level: other backends** (e.g. OpenMM on a GPU).
     - They compute the same model.
     - At start-up, a conformance single point against the reference backend must agree within
       stated tolerances (energy 10⁻⁶, forces 10⁻⁵ relative), or the run does not start.
  4. **Statistical level.** Ensemble results (density, κ, t⁺, RDFs) agree within their error
     bars across all backends. This is the level science needs, because trajectories of
     different backends diverge after picoseconds anyway.
  5. **Provenance:** every output records the backend, its version, precision, thread count
     and hardware (CPU model; GPU later), so results stay traceable.
- **Consequences:**
  - **E1 trajectories change once.** `libm` and own samplers replace the standard library and
    `rand_distr` in physics code. The statistics are unchanged, and the argon validation is
    re-run.
  - **FFT speed.** PME uses rustfft's scalar planner in the reference backend. A future opt-in
    fast mode may trade cross-machine bitwise identity for speed; it would say so in the
    provenance.
  - **GPU backends need a spec change later.** When the first one arrives (E3.7), the machine
    profile gets a backend section; that change needs the author's approval.
