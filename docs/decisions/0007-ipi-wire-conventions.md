# 0007 — i-PI wire conventions; ASE as the universal out-of-process provider

- **Status:** accepted 2026-11-12 by the agent, based on spike S4 (`spikes/s4-ipi-handshake/`).
  To be reviewed at Gate 0.
- **Context:**
  - PLAN.md D7 makes the i-PI socket protocol the transport for every out-of-process force
    provider. The Rust engine is the server; e.g. an ASE calculator is the client.
  - spec/force-provider.md §5 left two things for the spike to settle: the cell-matrix
    orientation and the virial convention on the wire.
- **Experiment:**
  - A 160-line std-only Rust i-PI server sent the `argon-864` fixture (cubic) and a sheared
    triclinic copy (b_x = 0.25 a_x, positions transformed affinely) to ASE 3.29's `SocketClient`,
    running ASE's `LennardJones` (σ = 3.4 Å, ε = 120 K·k_B, rc = 8.5 Å, `smooth=False`).
  - The results received were compared with:
    - a direct ASE evaluation;
    - the OpenMM reference (ADR 0005);
    - the NumPy reference virial.
- **Results** (relative deviations; forces as max|ΔF| / rms F):

  | ASE constants | energy vs direct ASE | forces vs direct ASE | virial vs direct ASE | energy vs OpenMM | triclinic energy vs direct |
  |---|---|---|---|---|---|
  | ASE default (CODATA 2014) | 2.7e-9 | 5.2e-8 | 1.3e-9 | 3.3e-7 (ε via k_B 2014) | 1.9e-9 |
  | `create_units("2018")` | 1.4e-11 | 4.5e-10 | 2.2e-11 | 1.4e-11 | 6.7e-12 |
  | 2018 + Bohr and hartree pinned to the spec's tabulated values | **2.2e-16** | **2.2e-13** | **4.1e-16** | **8.9e-16** | **2.2e-16** |

  - **Cell sent untransposed:** the energy is off by a factor of 5.6×10⁶ (atoms overlap). The
    orientation below is the only correct one.
  - **Latency:** 0.80 ms per full evaluation round trip, for 864 atoms, 2000 repeats, with a
    calculator that returns zeros. This is the Python-side overhead and negligible next to any ML
    or QM evaluation.
  - **Extra bytes:** ASE always sends at least one byte (a zero byte) in the extra field.
  - **Residual at the 1e-11 level** with plain `create_units("2018")`: ASE *derives* the bohr and
    the hartree from other constants, so they differ from the tabulated CODATA values by
    5.9×10⁻¹² and −8.0×10⁻¹². A uniform scaling that small is amplified in per-atom forces that
    are sums of nearly cancelling pair forces (rms 1.25 vs. pair forces of 10–50 kJ mol⁻¹ nm⁻¹).
- **Decision (normative for E3.1 and the spec):**
  1. **POSDATA:**
     - the cell is sent as h = cellᵀ (lattice vectors as columns), row-major, in bohr;
     - then inverse(cell) in rows as given (what ASE's own server sends; clients ignore it), in
       bohr⁻¹;
     - then N (i32) and the positions in bohr, canonical order.
  2. **FORCEREADY:**
     - energy in hartree; forces in hartree/bohr;
     - the 9 virial values arrive as Wᵀ row-major, in hartree, so transpose them on receipt;
     - the virial is W = −V·σ, which equals the spec's W = −∂E/∂ε;
     - extras are an i32 length plus bytes. An empty field or a single zero byte means "no
       extras"; anything else is parsed as JSON.
  3. **Constants:** `ucmd-bridge` sets ASE's units to CODATA 2018 at start-up and pins `Bohr`
     and `Hartree` to the tabulated values of spec/units.md §2. With that, the socket path is
     exact to round-off.
  4. **Tolerance for third-party clients** that use other constants: compare at 10⁻⁷ relative.
     Such codes (CP2K, Quantum ESPRESSO, …) bring their own CODATA versions.
- **Consequences:**
  - The E3.1 acceptance test "socket LJ = in-process LJ" can use 10⁻¹⁰ (energy) and 10⁻¹²·rms
    (forces), since the bridge pins the constants.
  - spec/force-provider.md §5 is updated with the conventions above.
  - The core modularity claim holds: any ASE calculator (ML potentials, QM codes) is an engine
    force provider without new Rust code.
