# Units and conventions (spec v0.1)

Normative for every UnitcellMD file, protocol and component. Decided in
[ADR 0001](../docs/decisions/0001-units.md).

## 1. Unit system

| Quantity | Unit | Suffix in keys |
|---|---|---|
| length | nm | `_nm` |
| time | ps (timesteps in configs may be given in fs) | `_ps`, `_fs` |
| mass | g/mol, labelled `amu` (numerically the relative atomic mass) | `_amu` |
| energy | kJ/mol | `_kjmol` |
| charge | elementary charge e | `_e` |
| temperature | K | `_K` |
| pressure | bar in files, configs and logs; kJ mol⁻¹ nm⁻³ internally | `_bar` |
| angle | degree in files; radian internally | `_deg`, `_rad` |
| velocity | nm/ps | — |
| force | kJ mol⁻¹ nm⁻¹ | — |
| force constants | kJ mol⁻¹ nm⁻² (bonds), kJ mol⁻¹ rad⁻² (angles) | `_kjmol_nm2`, `_kjmol_rad2` |
| compressibility | bar⁻¹ | `_per_bar` |
| friction / rate | ps⁻¹ | `_per_ps` |

- Defining the mass unit as g/mol makes the system exactly self-consistent:
  1 (g/mol)·nm²·ps⁻² = 1 kJ/mol, so F = m·a needs no conversion factor. (The dalton per
  particle differs from g/mol ÷ N_A by 3.5×10⁻¹⁰ since the 2019 SI redefinition; MD codes use
  molar masses, and so do we.)
- **Key-naming rule.** Every numeric key in a JSON or TOML file whose value has a unit ends with
  the unit suffix from the table. Keys without a suffix are dimensionless: counts, indices,
  factors, integer periodicities.
- Bulk arrays (NPY, HDF5) carry their units through this spec (NPY) or through `unit`
  attributes (HDF5).

## 2. Constants

Each language implementation derives its constants in one module from the CODATA 2018 values
below. No other code may contain rounded literals.

| Symbol | Value | Status |
|---|---|---|
| e | 1.602176634 × 10⁻¹⁹ C | exact |
| N_A | 6.02214076 × 10²³ mol⁻¹ | exact |
| k_B | 1.380649 × 10⁻²³ J K⁻¹ | exact |
| h | 6.62607015 × 10⁻³⁴ J s | exact |
| ε₀ | 8.8541878128 × 10⁻¹² F m⁻¹ | CODATA 2018 |
| E_h (hartree) | 4.3597447222071 × 10⁻¹⁸ J | CODATA 2018 |
| a₀ (bohr) | 5.29177210903 × 10⁻¹¹ m | CODATA 2018 |

Derived values, for checking implementations:

| Quantity | Value |
|---|---|
| k_B·N_A | 0.00831446261815324 kJ mol⁻¹ K⁻¹ |
| Coulomb constant e²N_A/(4πε₀) | 138.93545764438196 kJ mol⁻¹ nm e⁻² |
| 1 kJ mol⁻¹ nm⁻³ | 16.605390671738466 bar |
| 1 hartree | 2625.4996394798254 kJ/mol |
| 1 bohr | 0.0529177210903 nm |
| atomic unit of time ħ/E_h | 2.4188843265857193 × 10⁻⁵ ps |
| 1 eV | 96.48533212331002 kJ/mol |
| 1 kcal (thermochemical) | 4.184 kJ, exact |
| 1 Å | 0.1 nm, exact |

## 3. Geometry

- **Cell.** A 3×3 matrix whose **rows** are the lattice vectors **a**, **b**, **c**, in nm. It
  must be in reduced lower-triangular form:
  - a = (a_x, 0, 0), b = (b_x, b_y, 0), c = (c_x, c_y, c_z);
  - a_x, b_y, c_z > 0;
  - |b_x| ≤ a_x/2, |c_x| ≤ a_x/2, |c_y| ≤ b_y/2.

  The volume is V = a_x·b_y·c_z. Producers (the builder) reduce general cells to this form; a
  rotation of the whole system is allowed for that.
- **Positions** are Cartesian, in nm, in canonical atom order (system-package.md §4).
  - They are **unwrapped**: every molecule is whole, and atoms may lie outside the primary cell.
  - Wrapping happens only inside PBC kernels and is never written back.
- **Angles.** The bond angle θ_ijk lies in [0°, 180°]. Dihedral and improper angles φ_ijkl
  follow the IUPAC convention: φ is the angle between the planes (i, j, k) and (j, k, l),
  trans = 180°, range (−180°, 180°].

## 4. Mechanics

- **Forces:** F_i = −∂E/∂r_i.
- **Virial tensor** (kJ/mol): W_ab = −∂E/∂ε_ab at ε = 0, for the affine deformation
  r → (1+ε)·r, h → (1+ε)·h, where ε is a small 3×3 strain.
  - For pair potentials this is W = Σ_{i<j} r_ij ⊗ F_ij, with r_ij = r_i − r_j and F_ij the
    force on i due to j.
  - For an isolated system it equals Σ_i r_i ⊗ F_i.
  - It is symmetric for central forces.
- **Pressure tensor:** P = (Σ_i m_i v_i ⊗ v_i + W)/V. The scalar pressure is p = tr(P)/3.
- **Kinetic energy:** K = Σ_i ½ m_i |v_i|².
- **Temperature:** T = 2K/(N_dof·k_B), with N_dof = 3N − N_constraints − N_removed.
  N_removed = 3 if the centre-of-mass momentum is removed, plus 3 if the angular momentum is
  removed (allowed only for non-periodic systems).
- **Conserved quantity** of thermostatted or barostatted dynamics: H = K + E_pot plus the
  integrated work done by the thermostat and barostat (their "bath energy"). Reported as
  `conserved_energy`.
