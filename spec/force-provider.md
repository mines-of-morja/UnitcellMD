# Force-provider contract (spec v0.1)

A force provider maps a configuration to an energy and forces. **The engine's integrators see
forces only through this contract.** They never learn whether a provider is an analytic force
field, an ML potential, a QM program or a combination of these. Units and sign conventions:
[units.md](units.md).

There are two realizations of the same contract:

- **in-process:** the Rust trait `ForceProvider` in the engine crate `ucmd-force` (PLAN.md §2.4);
- **out-of-process:** the i-PI socket protocol (§5), so any i-PI client can be a provider.

## 1. Lifecycle

1. `initialize(system)` is called once, with the immutable system: masses, charges,
   elements, formal charges, molecule index, topology, force-field parameters, periodicity.
2. `evaluate(positions, cell, request)` is called once per force evaluation.
3. `finalize()` is called once at the end. It must also be safe after an error.

## 2. Evaluation

**Input:**

- `positions`: [N][3], nm, canonical order, unwrapped (molecules whole).
- `cell`: reduced 3×3 matrix in nm, or none for non-periodic systems.
- `request`:
  - `step`, `time_ps`;
  - `need_energy` (bool): the engine also needs the energy, not only forces;
  - `need_virial` (bool).

**Output:**

| Field | Required | Unit | Rule |
|---|---|---|---|
| `energy` | when `need_energy` | kJ/mol | potential energy of the configuration |
| `forces` | always | kJ mol⁻¹ nm⁻¹ | [N][3], canonical order, F = −∂E/∂r |
| `virial` | when `need_virial` and the virial capability is set | kJ/mol | W = −∂E/∂ε (units.md §4) |
| `energy_terms` | no | kJ/mol | named parts that sum to `energy` (relative difference ≤ 10⁻¹⁰) |
| `observables` | no | declared per observable | extra results, e.g. dipole moment or other electronic-state energies; each has a name, a value (number or array) and a unit |

- The energy, forces and virial of one evaluation refer to the **same** configuration.
- The engine checks every result: forces have length N; every value is finite; a requested
  virial is present. A failed check is an error, never a silent repair.

## 3. Capabilities

Declared once, after `initialize`:

| Capability | Meaning | Consequence |
|---|---|---|
| `periodic` | accepts a periodic cell | without it, a periodic run is rejected (`E_INCOMPATIBLE`) |
| `virial` | can return W | needed for pressure output and barostats |
| `energy_terms` | returns a decomposition | |
| `deterministic` | the same input gives a bitwise identical output | without it, restart tests only check tolerances (e.g. SCF codes) |

## 4. Errors

An evaluation either succeeds completely or fails with one of these categories:

| Category | Example |
|---|---|
| `unsupported` | periodic cell given to a gas-phase provider |
| `invalid_input` | NaN coordinates, overlapping atoms |
| `not_converged` | SCF did not converge |
| `external` | external program exited with non-zero status; includes the program, status and the last lines of stderr |
| `protocol` | socket closed, malformed message, timeout |
| `parse` | expected output missing, wrongly shaped, or stale (belongs to another geometry) |

- **Engine policy:** abort the step, write an emergency checkpoint of the last good state
  (checkpoint.md), and exit with a non-zero status.
- A provider must never substitute zero, stale or default values for a failed evaluation
  (lessons from NeNePo_builder, docs/nenepo-audit.md §5).
- Retries, such as an SCF restart with another guess, happen inside the provider, are logged,
  and are reported as observables.

## 5. Out-of-process profile: i-PI socket protocol

The engine is the i-PI **server**; the provider process is the **client**, e.g.
`ucmd-bridge` wrapping an ASE calculator.

- **Transport:** a Unix domain socket (local) or TCP (other nodes), configured in `run.toml`
  provider keys. Message headers are 12-byte ASCII strings, padded with spaces.
- **Units on the wire:** atomic units (bohr, hartree). The engine converts at the boundary.
- **Sequence:**
  1. The server sends `STATUS`; the client answers `READY`, or `NEEDINIT` (then the server
     sends `INIT`, the bead index and an init string).
  2. The server sends `POSDATA`, the cell matrix (9 f64), its inverse (9 f64), N (i32) and the
     positions (3N f64).
  3. The server sends `STATUS`; the client answers `HAVEDATA`.
  4. The server sends `GETFORCE`; the client answers `FORCEREADY`, the energy (f64), N (i32),
     the forces (3N f64), the virial (9 f64), the length of the extra string (i32) and the
     extra string.
  5. The server sends `EXIT` at the end.
- **Extra string:** a JSON object carrying `observables` (and optionally `energy_terms`).
- **Matrix orientation and virial on the wire**
  ([ADR 0007](../docs/decisions/0007-ipi-wire-conventions.md), verified against ASE 3.29):
  - In POSDATA the cell is sent as h = cellᵀ (lattice vectors as columns), row-major, in
    bohr, followed by inverse(cell) in bohr⁻¹ (clients ignore it).
  - In FORCEREADY the nine virial values are Wᵀ row-major, in hartree; transpose them on
    receipt. The virial is W = −V·σ = −∂E/∂ε (units.md §4).
- **Extras:** an empty extra field, or a single zero byte (ASE always sends one), means "no
  extras".
- **Constants:** clients we control (`ucmd-bridge`) use the constants of units.md §2. ASE must
  be switched to CODATA 2018, with `Bohr` and `Hartree` pinned to the tabulated values, which
  makes the transport exact to round-off. Third-party clients may use other CODATA versions;
  compare their results at 10⁻⁷ relative.
- **Limitation:** the protocol carries no point charges. Electrostatic-embedding QM/MM needs a
  protocol extension (PLAN.md E3.8).

## 6. Conformance tests

Every provider, in-process or external, passes the engine's provider test kit:

1. **Finite-difference forces:** central differences of the energy along every coordinate of
   a test configuration. Scan the step size h ∈ {10⁻³, …, 10⁻⁷} nm. At the best h, the
   largest relative error on components with |F| > 10⁻³ kJ mol⁻¹ nm⁻¹ is ≤ 10⁻⁵.
2. **Finite-difference virial:** central differences of the energy under homogeneous strain ±ε
   reproduce W (relative 10⁻⁵).
3. **Energy terms** sum to the energy.
4. **Momentum conservation:** for providers without external fields, |Σ_i F_i| ≤ 10⁻⁸ ·
   Σ_i |F_i|.
5. **Finiteness and shape** checks.
6. **Determinism:** two evaluations of the same input are bitwise identical, if declared.
