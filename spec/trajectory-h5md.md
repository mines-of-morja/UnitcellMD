# Trajectory format: H5MD profile (spec v0.1)

- **Format:** trajectories are HDF5 files following **H5MD 1.1** (de Buyl, Colberg, Höfling,
  Comput. Phys. Commun. 185, 1546 (2014)), plus the UnitcellMD conventions below. They can be
  read with h5py, and with MDAnalysis's H5MD reader.
- **Self-contained:** a trajectory carries a copy of the `system.json` it was produced from, so
  analysis needs no other file.
- Producers: the engine (E1.9) and converters for external trajectories (A1.1).

## 1. Structure

```
/h5md                              attrs: version = [1, 1] (int32)
  author                           attrs: name (string; from the machine profile, default "anonymous")
  creator                          attrs: name = "ucmd", version = "<engine version>"
  modules/units                    attrs: version = [1, 0]      (H5MD units module)
/particles/all
  box                              attrs: dimension = 3, boundary = ["periodic"|"none"] × 3
    edges                          time-dependent group (step, time, value [n,3,3]); rows = a, b, c
  position                         time-dependent group: value [n, N, 3]   unit "nm"
  velocity                         optional, value [n, N, 3]               unit "nm ps-1"
  force                            optional, value [n, N, 3]               unit "kJ mol-1 nm-1"
  mass                             dataset [N] float64                     unit "amu"
  charge                           dataset [N] float64                     unit "e" (only if the package has charges)
  species                          dataset [N] int32: atomic number, 0 for element null
  molecule_index                   dataset [N] int64: global molecule index (canonical order)
/observables
  potential_energy                 time-dependent, value [n]               unit "kJ mol-1"
  kinetic_energy                   time-dependent, value [n]               unit "kJ mol-1"
  conserved_energy                 time-dependent, value [n]               unit "kJ mol-1"
  temperature                      time-dependent, value [n]               unit "K"
  pressure                         time-dependent, value [n]               unit "bar" (only if a virial is available)
  pressure_tensor                  time-dependent, value [n, 3, 3]         unit "bar" (same condition)
  volume                           time-dependent, value [n]               unit "nm3" (periodic only)
  energy_terms/<name>              time-dependent, value [n]               unit "kJ mol-1"
  provider/<name>                  time-dependent, provider observables (dipole, state energies, …) with their units
/parameters/ucmd                   attrs: spec_version, engine_version, engine_git_hash,
                                          system_sha256, positions = "unwrapped"
  system_json                      dataset: UTF-8 string, the system.json of the run
  run_config_toml                  dataset: UTF-8 string, the fully resolved run configuration
```

## 2. Rules

- **Time-dependent groups** follow H5MD: `step` (int64 [n]), `time` (float64 [n], attribute
  `unit` = "ps") and `value`. Groups sampled at the same steps may share `step` and `time`
  through hard links.
- **Units** are given as an HDF5 attribute `unit` on every `value` and `time` dataset (H5MD units
  module syntax: space-separated factors with integer exponents, e.g. "nm ps-1").
- **Positions** are unwrapped (units.md §3); `/parameters/ucmd` attribute `positions =
  "unwrapped"`. No image flags are stored.
- **The box** is time-dependent in every trajectory, even at constant volume. This keeps
  readers simple. Non-periodic systems: `boundary = ["none", "none", "none"]`, `edges` all
  zeros.
- **Precision:** `value` datasets are float64 by default; float32 when the run config says
  `precision = "float32"`. Integers and `time` stay 64-bit.
- **Chunking:** one frame per chunk along the time axis. Compression is optional (gzip level ≤ 4).
- **Order:** canonical atom order (system-package.md §4).
- **Restarts** append to the same file after truncating to the checkpoint step
  (checkpoint.md).

## 3. Validation

The reference validator (`ucmd-spec validate-trajectory <file>`, needs h5py) checks:

- the required groups and attributes;
- shapes that match `atom_count` in the embedded `system_json`;
- monotonic `step`;
- unit attributes;
- finite values.

Error codes: `E_H5MD_STRUCTURE`, `E_H5MD_SHAPE`, `E_H5MD_UNITS`, `E_NONFINITE`.

*Status:* the box `edges` orientation and MDAnalysis compatibility are verified by spike S1
(ADR 0004).
