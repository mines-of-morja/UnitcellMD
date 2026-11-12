"""Generate the spec v0.1 fixtures deterministically.

    python spec/fixtures/_generators/generate.py

Rewrites spec/fixtures/{valid,invalid,runs}/. The committed fixtures must equal this script's
output; CI regenerates them and fails on any difference.

Parameter sources (pre-approved for fixtures, CLAUDE.md):
- argon: A. Rahman, Phys. Rev. 136, A405 (1964): sigma = 3.4 Å, epsilon/k_B = 120 K, state
  point 94.4 K at 1.374 g/cm^3.
- water: SPC/Fw, Y. Wu, H. L. Tepper, G. A. Voth, J. Chem. Phys. 124, 024503 (2006), Table I.
  Their bond and angle terms are written as (k/2)(x - x0)^2, i.e. the spec's 1/2 k form.
"""

from __future__ import annotations

import copy
import json
import math
import shutil
from pathlib import Path
from typing import Any

import numpy as np

FIXTURES = Path(__file__).resolve().parents[1]
SPEC_VERSION = "0.1.0"
CREATED = "2026-11-12T00:00:00Z"
GENERATOR = "spec/fixtures/_generators/generate.py"
UNITS = {
    "length": "nm",
    "time": "ps",
    "mass": "amu",
    "energy": "kJ/mol",
    "charge": "e",
    "temperature": "K",
    "angle": "deg",
}
# CODATA 2018 / exact SI values (spec/units.md §2)
N_A = 6.02214076e23
K_B_KJMOL = 0.00831446261815324
KCAL_KJ = 4.184
ANGSTROM_NM = 0.1


def system_doc(
    name: str,
    description: str,
    periodicity: list[bool],
    cell: list[list[float]] | None,
    molecule_types: dict[str, Any],
    components: list[dict[str, Any]],
    forcefield: dict[str, Any] | None = None,
    sources: list[dict[str, str]] | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    atom_count = sum(
        c["count"] * len(molecule_types[c["molecule_type"]]["atoms"])
        for c in components
    )
    provenance: dict[str, Any] = {"created_by": GENERATOR, "created_utc": CREATED}
    if sources:
        provenance["sources"] = sources
    if notes:
        provenance["notes"] = notes
    doc: dict[str, Any] = {
        "format": "ucmd-system",
        "spec_version": SPEC_VERSION,
        "name": name,
        "description": description,
        "units": dict(UNITS),
        "periodicity": periodicity,
        "cell_nm": cell,
        "molecule_types": molecule_types,
        "components": components,
        "atom_count": atom_count,
    }
    if forcefield is not None:
        doc["forcefield"] = forcefield
    doc["provenance"] = provenance
    return doc


def write_package(
    path: Path,
    doc: dict[str, Any] | str,
    positions: np.ndarray | None,
    velocities: np.ndarray | None = None,
    expected: str | None = None,
) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    text = doc if isinstance(doc, str) else json.dumps(doc, indent=2) + "\n"
    (path / "system.json").write_text(text, encoding="utf-8")
    if positions is not None:
        np.save(path / "positions.npy", positions)
    if velocities is not None:
        np.save(path / "velocities.npy", velocities)
    if expected is not None:
        (path / "expected.json").write_text(
            json.dumps({"code": expected}) + "\n", encoding="utf-8"
        )


def f8(values: Any) -> np.ndarray:
    return np.ascontiguousarray(np.asarray(values, dtype="<f8"))


def uniform_noise(seed: int, shape: tuple[int, ...], amplitude: float) -> np.ndarray:
    """Uniform noise in [-amplitude, amplitude) from the raw PCG64 stream.

    Uses only integer operations and exact float arithmetic, so the result is bit-identical on
    every platform and NumPy version (Generator.normal gives no such guarantee).
    """
    raw = np.random.PCG64(seed).random_raw(int(np.prod(shape)))
    unit = (raw >> np.uint64(11)).astype(np.float64) * 2.0**-53
    return (2.0 * unit - 1.0).reshape(shape) * amplitude


# --------------------------------------------------------------------------- valid packages


def harmonic_3d() -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    mtypes = {
        "triplet": {
            "description": "three unbonded pseudo-particles of different mass",
            "formal_charge_e": 0,
            "atoms": [
                {"name": "P1", "element": None, "mass_amu": 1.0},
                {"name": "P2", "element": None, "mass_amu": 2.0},
                {"name": "P3", "element": None, "mass_amu": 3.0},
            ],
            "bonds": [],
        }
    }
    doc = system_doc(
        "harmonic-3d",
        "Three particles for analytic integrator tests; the harmonic tethers come from run.toml. "
        "Not periodic, no force field.",
        [False, False, False],
        None,
        mtypes,
        [{"molecule_type": "triplet", "count": 1}],
        notes="Smallest valid package (system-package.md §8).",
    )
    positions = f8([[0.1, 0.0, 0.0], [0.0, 0.2, 0.0], [0.0, 0.0, -0.15]])
    velocities = f8([[0.0, 1.0, 0.0], [0.5, 0.0, 0.0], [0.0, 0.0, -0.2]])
    return doc, positions, velocities


def argon_864() -> tuple[dict[str, Any], np.ndarray]:
    mass = 39.948
    density_g_cm3 = 1.374
    number_density_nm3 = density_g_cm3 * N_A / mass * 1e-21
    box = round(
        (864 / number_density_nm3) ** (1.0 / 3.0), 6
    )  # rounded: pow is not correctly rounded
    a = box / 6
    basis = np.array([[0, 0, 0], [0.5, 0.5, 0], [0.5, 0, 0.5], [0, 0.5, 0.5]])
    cells = np.array(
        [[i, j, k] for i in range(6) for j in range(6) for k in range(6)], dtype=float
    )
    lattice = ((cells[:, None, :] + basis[None, :, :]).reshape(-1, 3)) * a
    positions = f8(lattice + uniform_noise(1964, lattice.shape, 0.005))
    mtypes = {
        "Ar": {
            "formal_charge_e": 0,
            "atoms": [
                {
                    "name": "Ar",
                    "element": "Ar",
                    "mass_amu": mass,
                    "charge_e": 0.0,
                    "type": "Ar",
                }
            ],
            "bonds": [],
        }
    }
    forcefield = {
        "name": "Lennard-Jones argon (Rahman 1964)",
        "combination_rule": "geometric",
        "scale_14_lj": 1.0,
        "scale_14_coulomb": 1.0,
        "atom_types": {
            "Ar": {
                "sigma_nm": round(3.4 * ANGSTROM_NM, 9),
                "epsilon_kjmol": 120.0 * K_B_KJMOL,
            }
        },
    }
    doc = system_doc(
        "argon-864",
        "864 argon atoms on a perturbed FCC lattice (6x6x6 cells) at the Rahman 1964 state point "
        "(1.374 g/cm^3). A uniform random displacement of up to 0.005 nm makes forces non-zero.",
        [True, True, True],
        [[box, 0.0, 0.0], [0.0, box, 0.0], [0.0, 0.0, box]],
        mtypes,
        [{"molecule_type": "Ar", "count": 864}],
        forcefield,
        sources=[
            {
                "what": "Lennard-Jones parameters and state point",
                "citation": "A. Rahman, Phys. Rev. 136, A405 (1964)",
                "doi": "10.1103/PhysRev.136.A405",
            }
        ],
        notes=f"Box edge {box:.6f} nm from 1.374 g/cm^3 and m = 39.948 g/mol; seed 1964.",
    )
    return doc, positions


def spcfw_type() -> tuple[dict[str, Any], dict[str, Any]]:
    """SPC/Fw molecule type and atom types (Wu, Tepper, Voth 2006, Table I)."""
    k_bond = round(
        1059.162 * KCAL_KJ / ANGSTROM_NM**2, 6
    )  # kcal mol-1 Å-2 -> kJ mol-1 nm-2
    k_angle = round(75.90 * KCAL_KJ, 6)  # kcal mol-1 rad-2 -> kJ mol-1 rad-2
    mtype = {
        "description": "SPC/Fw flexible water",
        "formal_charge_e": 0,
        "atoms": [
            {
                "name": "OW",
                "element": "O",
                "mass_amu": 15.9994,
                "charge_e": -0.82,
                "type": "OW",
            },
            {
                "name": "HW1",
                "element": "H",
                "mass_amu": 1.008,
                "charge_e": 0.41,
                "type": "HW",
            },
            {
                "name": "HW2",
                "element": "H",
                "mass_amu": 1.008,
                "charge_e": 0.41,
                "type": "HW",
            },
        ],
        "bonds": [
            {
                "atoms": [0, 1],
                "form": "harmonic",
                "params": {"r0_nm": 0.1012, "k_kjmol_nm2": k_bond},
            },
            {
                "atoms": [0, 2],
                "form": "harmonic",
                "params": {"r0_nm": 0.1012, "k_kjmol_nm2": k_bond},
            },
        ],
        "angles": [
            {
                "atoms": [1, 0, 2],
                "form": "harmonic",
                "params": {"theta0_deg": 113.24, "k_kjmol_rad2": k_angle},
            }
        ],
    }
    atom_types = {
        "OW": {
            "sigma_nm": round(3.165492 * ANGSTROM_NM, 9),
            "epsilon_kjmol": round(0.1554253 * KCAL_KJ, 10),
        },
        "HW": {"sigma_nm": 0.0, "epsilon_kjmol": 0.0},
    }
    return mtype, atom_types


def water_geometry(origin: np.ndarray, rotation_deg: float) -> np.ndarray:
    half = math.radians(113.24) / 2
    r0 = 0.1012
    local = np.array(
        [
            [0.0, 0.0, 0.0],
            [r0 * math.sin(half), r0 * math.cos(half), 0.0],
            [-r0 * math.sin(half), r0 * math.cos(half), 0.0],
        ]
    )
    if rotation_deg == 0.0:
        cos_a, sin_a = 1.0, 0.0
    elif rotation_deg == 60.0:
        cos_a, sin_a = 0.5, math.sqrt(3.0) / 2  # exact cos, correctly rounded sqrt
    else:
        raise ValueError("only 0 and 60 degrees are used")
    rot_x = np.array([[1, 0, 0], [0, cos_a, -sin_a], [0, sin_a, cos_a]])
    # rounded to 1e-9 nm: math.sin/cos may differ in the last ulp between platforms
    return np.round(local @ rot_x.T + origin, 9)


def water_2() -> tuple[dict[str, Any], np.ndarray]:
    mtype, atom_types = spcfw_type()
    forcefield = {
        "name": "SPC/Fw (Wu, Tepper, Voth 2006)",
        "combination_rule": "lorentz-berthelot",
        "scale_14_lj": 0.5,
        "scale_14_coulomb": 0.5,
        "atom_types": atom_types,
    }
    positions = np.vstack(
        [
            water_geometry(np.zeros(3), 0.0),
            water_geometry(np.array([0.29, 0.03, 0.01]), 60.0),
        ]
    )
    positions = f8(positions + uniform_noise(2006, positions.shape, 0.002))
    doc = system_doc(
        "water-2",
        "Two flexible SPC/Fw water molecules in vacuum, slightly distorted from equilibrium "
        "so that "
        "bonded and non-bonded forces are non-zero. Not periodic.",
        [False, False, False],
        None,
        {"SPCFw": mtype},
        [{"molecule_type": "SPCFw", "count": 2}],
        forcefield,
        sources=[
            {
                "what": "SPC/Fw parameters "
                "(transcribed from Table I; verify before production use)",
                "citation": "Y. Wu, H. L. Tepper, G. A. Voth, J. Chem. Phys. 124, 024503 (2006)",
                "doi": "10.1063/1.2136877",
            }
        ],
        notes="Bond and angle force constants converted from (k/2)(x - x0)^2 in kcal/mol "
        "units; seed 2006. "
        "No 1-4 pairs exist in water, so the scale factors have no effect.",
    )
    return doc, positions


def nacl_crystal() -> tuple[dict[str, Any], np.ndarray]:
    a = 0.5640  # nm; a test value: the Madelung energy scales as 1/a
    fcc = np.array([[0, 0, 0], [0.5, 0.5, 0], [0.5, 0, 0.5], [0, 0.5, 0.5]])
    cells = np.array(
        [[i, j, k] for i in range(2) for j in range(2) for k in range(2)], dtype=float
    )
    na = ((cells[:, None, :] + fcc[None, :, :]).reshape(-1, 3)) * a
    cl = na + np.array([0.5 * a, 0.0, 0.0])
    mtypes = {
        "Na+": {
            "formal_charge_e": 1,
            "atoms": [
                {
                    "name": "Na",
                    "element": "Na",
                    "mass_amu": 22.98977,
                    "charge_e": 1.0,
                    "type": "Na",
                }
            ],
            "bonds": [],
        },
        "Cl-": {
            "formal_charge_e": -1,
            "atoms": [
                {
                    "name": "Cl",
                    "element": "Cl",
                    "mass_amu": 35.453,
                    "charge_e": -1.0,
                    "type": "Cl",
                }
            ],
            "bonds": [],
        },
    }
    forcefield = {
        "name": "point charges only (Madelung test)",
        "combination_rule": "geometric",
        "scale_14_lj": 1.0,
        "scale_14_coulomb": 1.0,
        "atom_types": {
            "Na": {"sigma_nm": 0.0, "epsilon_kjmol": 0.0},
            "Cl": {"sigma_nm": 0.0, "epsilon_kjmol": 0.0},
        },
    }
    doc = system_doc(
        "nacl-crystal",
        "Rock-salt crystal, 2x2x2 conventional cells (32 Na+, 32 Cl-), point charges +-1 e and no "
        "Lennard-Jones: the Coulomb energy is -32 * 1.747565 * k_e / (a/2) (Madelung constant).",
        [True, True, True],
        [[2 * a, 0.0, 0.0], [0.0, 2 * a, 0.0], [0.0, 0.0, 2 * a]],
        mtypes,
        [{"molecule_type": "Na+", "count": 32}, {"molecule_type": "Cl-", "count": 32}],
        forcefield,
        notes="Lattice constant 0.5640 nm is a test value (close to experiment); "
        "canonical order is all Na, then all Cl.",
    )
    return doc, f8(np.vstack([na, cl]))


# --------------------------------------------------------------------------- invalid packages


def invalid_packages(
    root: Path, valid: dict[str, tuple[dict[str, Any], np.ndarray]]
) -> None:
    out = root / "invalid"
    if out.exists():
        shutil.rmtree(out)
    argon_doc, argon_pos = valid["argon-864"]
    water_doc, water_pos = valid["water-2"]
    nacl_doc, nacl_pos = valid["nacl-crystal"]

    def mutate(doc: dict[str, Any], change: Any) -> dict[str, Any]:
        new = copy.deepcopy(doc)
        change(new)
        return new

    cases: list[tuple[str, str, Any, np.ndarray | None]] = [
        ("invalid-json", "E_JSON", json.dumps(water_doc, indent=2)[:-40], water_pos),
        (
            "bad-format",
            "E_FORMAT",
            mutate(water_doc, lambda d: d.update(format="gromacs-top")),
            water_pos,
        ),
        (
            "unknown-major-version",
            "E_VERSION",
            mutate(water_doc, lambda d: d.update(spec_version="1.0.0")),
            water_pos,
        ),
        (
            "unknown-unit",
            "E_UNITS",
            mutate(water_doc, lambda d: d["units"].update(length="angstrom")),
            water_pos,
        ),
        (
            "schema-missing-key",
            "E_SCHEMA",
            mutate(water_doc, lambda d: d.pop("provenance")),
            water_pos,
        ),
        (
            "schema-unknown-param",
            "E_SCHEMA",
            mutate(
                water_doc,
                lambda d: d["molecule_types"]["SPCFw"]["bonds"][0]["params"].update(
                    r0=0.1012
                ),
            ),
            water_pos,
        ),
        (
            "unknown-molecule-type",
            "E_REFERENCE",
            mutate(argon_doc, lambda d: d["components"][0].update(molecule_type="Kr")),
            argon_pos,
        ),
        (
            "unknown-atom-type",
            "E_REFERENCE",
            mutate(
                water_doc,
                lambda d: d["molecule_types"]["SPCFw"]["atoms"][1].update(type="HX"),
            ),
            water_pos,
        ),
        (
            "bond-index-out-of-range",
            "E_INDEX",
            mutate(
                water_doc,
                lambda d: d["molecule_types"]["SPCFw"]["bonds"][1].update(atoms=[0, 3]),
            ),
            water_pos,
        ),
        (
            "atom-count-mismatch",
            "E_ATOM_COUNT",
            mutate(argon_doc, lambda d: d.update(atom_count=863)),
            argon_pos,
        ),
        (
            "cell-not-reduced",
            "E_CELL",
            mutate(
                argon_doc,
                lambda d: d["cell_nm"][1].__setitem__(0, 0.6 * d["cell_nm"][0][0]),
            ),
            argon_pos,
        ),
        (
            "cell-missing",
            "E_CELL",
            mutate(argon_doc, lambda d: d.update(cell_nm=None)),
            argon_pos,
        ),
        (
            "parameters-incomplete",
            "E_PARAMETERS",
            mutate(
                water_doc,
                lambda d: d["molecule_types"]["SPCFw"]["atoms"][0].pop("type"),
            ),
            water_pos,
        ),
        (
            "net-charge",
            "E_NET_CHARGE",
            mutate(
                nacl_doc,
                lambda d: d["molecule_types"]["Na+"]["atoms"][0].update(charge_e=1.1),
            ),
            nacl_pos,
        ),
        ("positions-missing", "E_ARRAY_MISSING", argon_doc, None),
        ("positions-wrong-shape", "E_ARRAY_FORMAT", argon_doc, argon_pos[:-1]),
        ("positions-float32", "E_ARRAY_FORMAT", argon_doc, argon_pos.astype("<f4")),
    ]
    for name, code, doc, positions in cases:
        write_package(out / name, doc, positions, expected=code)

    nan_positions = argon_pos.copy()
    nan_positions[17, 1] = np.nan
    write_package(
        out / "nan-coordinate", argon_doc, nan_positions, expected="E_NONFINITE"
    )

    # A periodic water box whose second hydrogen sits across the boundary: molecule not whole.
    box = 1.0
    split = mutate(
        water_doc,
        lambda d: d.update(
            periodicity=[True, True, True],
            cell_nm=[[box, 0.0, 0.0], [0.0, box, 0.0], [0.0, 0.0, box]],
        ),
    )
    split_pos = water_pos + 0.4
    split_pos[2, 0] += box  # image-shifted hydrogen
    write_package(
        out / "molecule-split", split, f8(split_pos), expected="E_MOLECULE_SPLIT"
    )


# --------------------------------------------------------------------------- run configurations

RUNS = {
    "argon-nvt.toml": """\
spec_version = "0.1.0"
system = "../valid/argon-864"
title = "Argon at the Rahman 1964 state point, NVT equilibration with CSVR"

[run]
integrator = "velocity-verlet"
timestep_fs = 4.0
steps = 25000
seed = 20261112

[velocities]
generate = "maxwell-boltzmann"
temperature_K = 94.4

[momentum]
remove_com_every = 1000

[thermostat]
kind = "csvr"
temperature_K = 94.4
tau_ps = 0.5

[[providers]]
kind = "lennard-jones"
cutoff_nm = 0.85
cutoff_mode = "potential-shift"
dispersion_correction = true

[output]
directory = "out"

[output.trajectory]
file = "trajectory.h5"
every = 100
precision = "float64"

[output.thermo]
file = "thermo.tsv"
every = 10

[output.checkpoint]
file = "checkpoint.ucchk"
every = 5000
""",
    "harmonic-nve.toml": """\
spec_version = "0.1.0"
system = "../valid/harmonic-3d"
title = "Three particles on harmonic tethers to the origin, NVE"

[run]
integrator = "velocity-verlet"
timestep_fs = 1.0
steps = 1000
seed = 1

[[providers]]
kind = "harmonic-tether"
k_kjmol_nm2 = 1000.0
""",
}

INVALID_RUNS = {
    "not-toml.toml": ("E_TOML", 'spec_version = "0.1.0"\nsystem = \n'),
    "bad-version.toml": (
        "E_VERSION",
        RUNS["harmonic-nve.toml"].replace('"0.1.0"', '"2.0.0"', 1),
    ),
    "absolute-path.toml": (
        "E_PATH",
        RUNS["harmonic-nve.toml"].replace(
            'system = "../valid/harmonic-3d"', 'system = "/home/user/harmonic-3d"'
        ),
    ),
    "no-providers.toml": (
        "E_SCHEMA",
        RUNS["harmonic-nve.toml"].split("[[providers]]")[0],
    ),
    "langevin-with-vv.toml": (
        "E_INCOMPATIBLE",
        RUNS["harmonic-nve.toml"]
        + '\n[thermostat]\nkind = "langevin"\ntemperature_K = 300.0\nfriction_per_ps = 1.0\n',
    ),
}


def run_configs(root: Path) -> None:
    out = root / "runs"
    if out.exists():
        shutil.rmtree(out)
    (out / "invalid").mkdir(parents=True)
    for name, text in RUNS.items():
        (out / name).write_text(text, encoding="utf-8")
    expected = {}
    for name, (code, text) in INVALID_RUNS.items():
        (out / "invalid" / name).write_text(text, encoding="utf-8")
        expected[name] = code
    (out / "invalid" / "expected.json").write_text(
        json.dumps(expected, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def generate(root: Path) -> None:
    """Write all fixtures below ``root`` (the committed ones live in spec/fixtures/)."""
    valid_dir = root / "valid"
    if valid_dir.exists():
        shutil.rmtree(valid_dir)
    doc, pos, vel = harmonic_3d()
    write_package(valid_dir / "harmonic-3d", doc, pos, vel)
    valid: dict[str, tuple[dict[str, Any], np.ndarray]] = {}
    for name, builder in (
        ("argon-864", argon_864),
        ("water-2", water_2),
        ("nacl-crystal", nacl_crystal),
    ):
        doc, pos = builder()
        write_package(valid_dir / name, doc, pos)
        valid[name] = (doc, pos)
    invalid_packages(root, valid)
    run_configs(root)


def main(argv: list[str] | None = None) -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--out",
        type=Path,
        default=FIXTURES,
        help="output root (default: spec/fixtures)",
    )
    args = parser.parse_args(argv)
    generate(args.out)
    print(f"fixtures written to {args.out}")


if __name__ == "__main__":
    main()
