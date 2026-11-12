# Run configuration `run.toml` (spec v0.1)

`run.toml` says **how** a system package is simulated: integrator, ensemble, force providers,
outputs. The same package can be run with different `run.toml` files, e.g. classical,
ML-based or QM-based forces.

- A `run.toml` is **location-independent**: every path in it is relative to the directory that
  contains the `run.toml`.
- Machine-specific settings (executables, scratch space, threads) live in the **machine
  profile** (§4), never here ([ADR 0002](../docs/decisions/0002-local-first-execution.md)).

Units: [units.md](units.md); every key with a unit carries the suffix.
Schema: [schemas/run-config.schema.json](schemas/run-config.schema.json), applied to the parsed
TOML document.

## 1. Example (argon, NVT equilibration with CSVR)

```toml
spec_version = "0.1.0"
system = "../fixtures/valid/argon-864"   # system package directory, relative to this file
title = "Argon, Rahman 1964 state point"

[run]
integrator = "velocity-verlet"
timestep_fs = 4.0
steps = 25000
seed = 20261112                         # master seed; every random stream is derived from it

[velocities]                            # optional: generate initial velocities
generate = "maxwell-boltzmann"
temperature_K = 94.4

[momentum]                              # optional
remove_com_every = 1000                 # steps; 0 = only once at the start
remove_angular = false                  # only allowed for non-periodic systems

[thermostat]                            # optional; absent = NVE
kind = "csvr"
temperature_K = 94.4
tau_ps = 0.5

[[providers]]                           # one or more; their forces and energies are summed
kind = "lennard-jones"
cutoff_nm = 0.85
cutoff_mode = "potential-shift"
dispersion_correction = true

[output]
directory = "out"

[output.trajectory]
file = "trajectory.h5"
every = 100
velocities = false
precision = "float64"

[output.thermo]
file = "thermo.tsv"
every = 10

[output.checkpoint]
file = "checkpoint.ucchk"
every = 5000
```

## 2. Keys

### Top level

| Key | Required | Meaning |
|---|---|---|
| `spec_version` | yes | semver; readers apply the policy of system-package.md §9 |
| `system` | yes | relative path to the system package directory |
| `title` | no | free text |

### `[run]`

| Key | Required | Meaning |
|---|---|---|
| `integrator` | yes | `"velocity-verlet"` (E1); `"langevin-baoab"` (E2) |
| `timestep_fs` | yes | > 0 |
| `steps` | yes | integer ≥ 0; 0 = evaluate forces and write outputs once |
| `seed` | yes | integer ≥ 0; master seed for every random number in the run |

### `[velocities]` (optional)

If present, velocities are generated and override `velocities.npy` in the package.

| Key | Required | Meaning |
|---|---|---|
| `generate` | yes | `"maxwell-boltzmann"` |
| `temperature_K` | yes | ≥ 0 |

### `[momentum]` (optional)

| Key | Required | Meaning |
|---|---|---|
| `remove_com_every` | no | default 0 = remove the COM momentum once, after velocity setup. `n` > 0 removes it every n steps |
| `remove_angular` | no | default false; rejected for periodic systems |

### `[thermostat]` (optional)

If absent, the dynamics are NVE.

| `kind` | Keys |
|---|---|
| `csvr` (Bussi 2007) | `temperature_K`, `tau_ps` |
| `nose-hoover-chain` (E2.6) | `temperature_K`, `tau_ps`, `chain_length` (default 3) |
| `langevin` (only with `integrator = "langevin-baoab"`, E2.6) | `temperature_K`, `friction_per_ps` |

### `[barostat]` (optional, E2.7)

| Key | Meaning |
|---|---|
| `kind` | `"c-rescale"` |
| `pressure_bar` | target pressure |
| `tau_ps` | coupling time |
| `compressibility_per_bar` | e.g. 4.5e-5 for water |
| `every` | steps between applications, default 10 |
| `coupling` | `"isotropic"` (default) or `"anisotropic"` |

### `[[providers]]` (one or more)

Each table selects a force provider by `kind`. The engine sums the providers (`Composite`).

| Key | Meaning |
|---|---|
| `kind` | required; registry name, e.g. `"lennard-jones"`, `"harmonic-tether"`, `"ipi-socket"` |
| `name` | optional; prefix for energy terms, default `kind` |

All other keys belong to the provider, which validates them. The schema only requires `kind`.
Every provider documents its keys, with unit suffixes.

### `[output]`

| Key | Meaning |
|---|---|
| `directory` | relative path, default `"out"` |
| `[output.trajectory]` | `file`, `every` (steps), `velocities` (bool), `forces` (bool), `precision` (`"float64"` default, or `"float32"`); format in trajectory-h5md.md |
| `[output.thermo]` | `file`, `every`; tab-separated table: step, time_ps, energies, temperature_K, pressure_bar, volume_nm3, conserved_energy_kjmol |
| `[output.checkpoint]` | `file`, `every`; see checkpoint.md |

## 3. Validation

Checks run in this order and stop at the first error:

- **`E_TOML`:** the file is missing or is not valid TOML.
- **`E_VERSION`:** unsupported `spec_version`.
- **`E_PATH`:** an absolute path, or a path starting with `~`.
- **`E_SCHEMA`:** schema violations.
- **`E_INCOMPATIBLE`:** settings that contradict each other, e.g. the `langevin` thermostat
  without the `langevin-baoab` integrator.

Cross-checks against the package happen when the engine starts:

- **`E_INCOMPATIBLE`:** e.g. a barostat for a non-periodic system, `remove_angular` with PBC,
  or a provider whose capabilities don't cover the request.

## 4. Machine profile

Machine-specific settings live in a TOML file outside every package and run directory. Lookup
order:

1. `$UCMD_MACHINE_PROFILE`;
2. `$XDG_CONFIG_HOME/ucmd/machine.toml`;
3. `~/.config/ucmd/machine.toml`.

If no profile exists, defaults apply.

```toml
spec_version = "0.1.0"
threads = 16                      # default: all logical cores
scratch_dir = "/tmp/ucmd"         # default: system temp directory

[executables]                     # absolute paths, probed when a provider starts
packmol = "/opt/packmol/packmol"
orca = "/opt/orca/orca"
g16 = "/opt/g16/g16"
```

Providers that call external programs look up executables here by name. A run never searches
`PATH` for them. On the author's workstation `orca` on `PATH` is the GNOME screen reader.
