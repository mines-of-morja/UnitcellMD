# System package (spec v0.1)

A system package describes **what** is simulated: atoms, molecules, connectivity, the periodic
cell, the initial state, and optionally force-field parameters. It says nothing about **how** it
is simulated (integrator, ensemble, force method, cutoffs); that belongs to `run.toml`
(run-config.md).

A package is self-contained and location-independent: it can be copied anywhere and used as is.
Units and conventions: [units.md](units.md).

## 1. Layout

A package is a directory, by convention named `<name>.ucsys/`:

| File | Required | Content |
|---|---|---|
| `system.json` | yes | metadata, cell, molecule types, components, optional force field, provenance (§2–§5) |
| `positions.npy` | yes | initial positions, float64, shape (atom_count, 3), nm (§6) |
| `velocities.npy` | no | initial velocities, float64, shape (atom_count, 3), nm/ps (§6) |

No other files are read. Producers may add a `README.md`.

## 2. `system.json`, top level

```json
{
  "format": "ucmd-system",
  "spec_version": "0.1.0",
  "name": "argon-864",
  "description": "optional free text",
  "units": {"length": "nm", "time": "ps", "mass": "amu", "energy": "kJ/mol",
            "charge": "e", "temperature": "K", "angle": "deg"},
  "periodicity": [true, true, true],
  "cell_nm": [[3.4686, 0, 0], [0, 3.4686, 0], [0, 0, 3.4686]],
  "molecule_types": {"Ar": { … }},
  "components": [{"molecule_type": "Ar", "count": 864}],
  "atom_count": 864,
  "forcefield": { … },
  "provenance": {"created_by": "…", "created_utc": "2026-11-12T00:00:00Z"}
}
```

| Key | Required | Meaning |
|---|---|---|
| `format` | yes | always `"ucmd-system"` |
| `spec_version` | yes | semver of the spec the file follows (§9) |
| `name` | yes | short identifier |
| `description` | no | free text |
| `units` | yes | must be exactly the block above. It documents the units; it is not a choice |
| `periodicity` | yes | three booleans for the a, b, c directions |
| `cell_nm` | yes | 3×3 matrix in reduced form (units.md §3), or `null` when no direction is periodic |
| `molecule_types` | yes | map of name → molecule type (§3). Names match `^[A-Za-z0-9_.+-]+$` |
| `components` | yes | ordered list of `{"molecule_type": <name>, "count": <int ≥ 1>}`; the same type may appear more than once |
| `atom_count` | yes | Σ over components of count × number of atoms in the type; a redundancy check |
| `forcefield` | no | force-field parameters (§5). Present ⇔ the package is *parameterized* |
| `provenance` | yes | object with at least `created_by` (tool and version) and `created_utc` (ISO 8601, UTC). Recommended: `recipe`, `seed`, `sources` (a list of `{what, citation, doi?, url?}`), `notes`. Further keys are free-form |

Everything that can repeat lives in a **molecule type**, instantiated `count` times; there is no
separate "explicit atoms" mechanism. Crystals use single-atom molecule types (e.g. `Li`, `F`),
or one large molecule type with count 1 when intramolecular bonds are needed.

## 3. Molecule type

```json
"EC": {
  "description": "ethylene carbonate",
  "formal_charge_e": 0,
  "atoms": [
    {"name": "C1", "element": "C", "mass_amu": 12.011, "charge_e": 0.0, "type": "ec_c1"}
  ],
  "bonds":     [{"atoms": [0, 1], "form": "harmonic", "params": {"r0_nm": 0.1, "k_kjmol_nm2": 1.0}}],
  "angles":    [{"atoms": [0, 1, 2], "form": "harmonic", "params": {…}}],
  "dihedrals": [{"atoms": [0, 1, 2, 3], "form": "opls-fourier", "params": {…}}],
  "impropers": [{"atoms": [0, 1, 2, 3], "form": "periodic", "params": {…}}],
  "constraints": [{"atoms": [0, 1], "length_nm": 0.1}]
}
```

- `formal_charge_e` (integer, required): the ionic charge number z of the molecule, e.g. +1 for
  Li⁺, −1 for PF₆⁻, 0 for EC. Analysis uses it (κ, t⁺), as do QM providers (total charge). It
  is independent of the possibly scaled partial charges.
- `atoms` (required, non-empty): `name` (string), `element` (chemical symbol, or `null` for
  pseudo-particles), `mass_amu` (> 0). In parameterized packages also `charge_e` and `type`.
- `bonds` (required, possibly empty) define the connectivity: exclusions (§5.2), molecule
  wholeness checks, and analysis.
- `angles`, `dihedrals`, `impropers` (optional): bonded energy terms. They are only meaningful
  with parameters.
- `constraints` (optional): fixed distances that belong to the model (e.g. rigid water). Run
  protocols may add more constraints (e.g. all bonds to H); see run-config.md.
- All atom indices are 0-based within the molecule type. An interaction never repeats an index.
  Bonds between different molecules do not exist in v0.1.

## 4. Canonical order

The global atom order is: components in list order → instances 0…count−1 → atoms in
molecule-type order. The global atom index and the global molecule index follow this order.
Every array, trajectory and force vector in UnitcellMD uses it. Kernels may reorder atoms
internally, but every output is in canonical order.

## 5. Force field (`forcefield`)

```json
"forcefield": {
  "name": "OPLS-AA (source …)",
  "combination_rule": "geometric",
  "scale_14_lj": 0.5,
  "scale_14_coulomb": 0.5,
  "atom_types": {"ec_c1": {"sigma_nm": 0.375, "epsilon_kjmol": 0.43932}}
}
```

### 5.1 Parameterized vs. unparameterized packages

- **Parameterized** (`forcefield` present):
  - every atom has `type`, which is a key of `atom_types`, and `charge_e`;
  - every bond, angle, dihedral and improper has `form` and `params`.

  Classical providers require this.
- **Unparameterized** (`forcefield` absent): interactions carry no `form`/`params`. Charges are
  optional, but must be given for all atoms or for none. QM and ML providers use such packages.

### 5.2 Non-bonded interactions

- **Lennard-Jones 12-6:** E = 4ε_ij[(σ_ij/r)¹² − (σ_ij/r)⁶]. Pair parameters come from the
  atom types via `combination_rule`:
  - `geometric`: σ_ij = √(σ_i σ_j), ε_ij = √(ε_i ε_j) (OPLS);
  - `lorentz-berthelot`: σ_ij = (σ_i + σ_j)/2, ε_ij = √(ε_i ε_j).
- **Coulomb:** E = k_e q_i q_j / r, with k_e from units.md §2.
- **Exclusions:** within a molecule, let d be the shortest path length in the bond graph. Pairs
  with d = 1 or 2 are excluded. Pairs with d = 3 interact with LJ scaled by `scale_14_lj` and
  Coulomb scaled by `scale_14_coulomb`. All other pairs, and all intermolecular pairs, interact
  fully. (This is the LAMMPS `special_bonds` and OpenMM `createExceptionsFromBonds` behaviour.
  In rings a pair counts by its shortest path.)
- Cutoffs, long-range electrostatics and dispersion corrections are run settings, not part of
  the package.

### 5.3 Bonded functional forms

| Interaction | `form` | Energy | `params` |
|---|---|---|---|
| bond | `harmonic` | ½ k (r − r₀)² | `r0_nm` > 0, `k_kjmol_nm2` ≥ 0 |
| angle | `harmonic` | ½ k (θ − θ₀)² | `theta0_deg` ∈ [0, 180], `k_kjmol_rad2` ≥ 0 |
| dihedral, improper | `periodic` | k [1 + cos(nφ − φ₀)] | `k_kjmol`, `n` (integer 0…6), `phi0_deg` |
| dihedral | `opls-fourier` | ½[V₁(1+cos φ) + V₂(1−cos 2φ) + V₃(1+cos 3φ) + V₄(1−cos 4φ)] | `v1_kjmol` … `v4_kjmol` |
| dihedral | `ryckaert-bellemans` | Σₙ₌₀⁵ Cₙ cosⁿψ, with ψ = φ − 180° | `c0_kjmol` … `c5_kjmol` |
| improper | `harmonic` | ½ k (ξ − ξ₀)², with ξ − ξ₀ wrapped to (−180°, 180°] | `xi0_deg`, `k_kjmol_rad2` ≥ 0 |

- Note the ½ in the harmonic forms. Sources that write K(r − r₀)², such as LAMMPS, AMBER and many
  OPLS tables, have k = 2K. Producers convert; the package always uses the forms above.
- Several entries with the same atoms are allowed and add up, e.g. a periodic dihedral with
  n = 1, 2, 3.

## 6. State arrays

- **Format:** NPY version 1.0 or 2.0, dtype `<f8` (little-endian float64), C order
  (`fortran_order: False`), shape (atom_count, 3), canonical atom order.
- **`positions.npy`** (nm): unwrapped, so every molecule is whole (units.md §3).
- **`velocities.npy`** (nm/ps): optional. If it is absent, the run config must generate
  velocities, or the run starts at rest.

## 7. Validation

A package is valid when it passes the JSON Schema `schemas/system.schema.json` and the semantic
rules below. Readers in every language report these **stable error codes**. The reference
validator is `ucmd-spec validate <package>` (`validator/`). Codes starting with `W_` are
warnings: the package is valid, but suspicious.

| Code | Rule |
|---|---|
| `E_JSON` | `system.json` missing, or not valid JSON |
| `E_FORMAT` | `format` missing or not `"ucmd-system"` |
| `E_VERSION` | `spec_version` not semver, or not supported by the reader (§9) |
| `E_UNITS` | `units` block missing or different from §2 |
| `E_SCHEMA` | any other JSON Schema violation (missing key, wrong type, unknown key, parameter out of range) |
| `E_REFERENCE` | a component names an unknown molecule type, or an atom names an unknown atom type |
| `E_INDEX` | an interaction index is out of range for its molecule type, or repeated within one interaction |
| `E_ATOM_COUNT` | `atom_count` ≠ Σ count × atoms per type |
| `E_CELL` | `cell_nm` is `null` although a direction is periodic, or present although none is; not in reduced form; or a non-positive diagonal |
| `E_ARRAY_MISSING` | `positions.npy` missing |
| `E_ARRAY_FORMAT` | an array is not NPY 1.0/2.0, not `<f8`, not C order, or has the wrong shape |
| `E_NONFINITE` | NaN or ±inf in an array |
| `E_PARAMETERS` | parameterized package with an atom lacking `type`/`charge_e` or an interaction lacking `form`/`params`; unparameterized package with `form`/`params`; charges given for only some atoms |
| `E_NET_CHARGE` | periodic package with charges whose sum deviates from 0 by more than 10⁻⁶ e |
| `E_MOLECULE_SPLIT` | periodic package where two bonded or constrained atoms are farther apart than half the smallest perpendicular cell height (the molecule is not whole) |
| `W_FORMAL_CHARGE` | periodic package whose formal charges do not sum to 0 |

Checks run in this order; the first error stops validation:
E_JSON → E_FORMAT → E_VERSION → E_UNITS → E_SCHEMA → semantic checks → arrays.
Warnings are collected.

## 8. Example

The smallest valid package is `fixtures/valid/harmonic-3d`: three particles, not periodic, no
force field. The test fixtures in [fixtures/](fixtures/) are the normative examples.

## 9. Versioning

- `spec_version` follows semver. While the major version is 0, every **minor** version may
  break compatibility.
- A reader of spec 0.1.x accepts exactly the files with `spec_version` 0.1.x and rejects others
  with `E_VERSION`. From 1.0 on, readers accept the same major version and the same or an older
  minor version.
- Every change is recorded in `CHANGELOG.md`. A change also updates the schemas, the fixtures
  and every reader, together.
