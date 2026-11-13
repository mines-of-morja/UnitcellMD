"""Reference single points for molecules, per energy term (E2.1, E2.2).

    tools/oracle/.venv/bin/python tools/oracle/make_molecule_references.py [PACKAGE ...]

- Each PACKAGE is a builder-made one-molecule package. It is stored without periodicity
  under reference/molecules/<name>/ (system.json, positions.npy).
- Without arguments, the packages already stored there are re-evaluated.
- A synthetic molecule `allforms` is always written by this script. It carries every bonded
  form of the spec with asymmetric phases, plus 1-4 and longer-range pairs, so that the
  engine's sign and wrapping conventions are pinned to OpenMM's.
- Per case: terms.json (energy per term and total, kJ/mol) and forces-<term>.npy
  (kJ mol⁻¹ nm⁻¹), from oracle v1 on OpenMM's Reference platform, in vacuum. Oracle v1 itself
  agrees with OpenMM's GROMACS reader to 1e-12 (ucmd-builder validation/b1-openmm).
"""

import json
import math
import sys
from pathlib import Path

import numpy as np
import openmm

import oracle

HERE = Path(__file__).resolve().parent
OUT = HERE / "reference" / "molecules"


def store_without_periodicity(package: Path, name: str) -> Path:
    target = OUT / name
    target.mkdir(parents=True, exist_ok=True)
    doc = json.loads((package / "system.json").read_text())
    doc["periodicity"] = [False, False, False]
    doc["cell_nm"] = None
    doc["provenance"] = {
        "created_by": doc["provenance"]["created_by"],
        "created_utc": doc["provenance"]["created_utc"],
        "notes": "one molecule from a ucmd-builder package, stored without periodicity by "
        "tools/oracle/make_molecule_references.py",
        "sources": doc["provenance"].get("sources", []),
    }
    (target / "system.json").write_text(json.dumps(doc, indent=1) + "\n")
    # A small deterministic displacement takes every term off its minimum (e.g. PF6-, which is
    # stored at its exact octahedral geometry), so that all terms are tested with non-zero forces.
    positions = np.load(package / "positions.npy")
    rng = np.random.default_rng(20261112)
    positions = positions + rng.uniform(-0.004, 0.004, size=positions.shape)
    np.save(target / "positions.npy", np.ascontiguousarray(positions, dtype="<f8"))
    return target


ALLFORMS_XYZ = np.array(
    [
        [0.000, 0.000, 0.000],
        [0.150, 0.020, 0.010],
        [0.200, 0.150, -0.030],
        [0.330, 0.170, 0.050],
        [0.390, 0.300, 0.020],
        [0.170, -0.060, 0.140],
    ]
)


def write_allforms() -> Path:
    target = OUT / "allforms"
    target.mkdir(parents=True, exist_ok=True)

    def bond(i, j, r0, k):
        return {"atoms": [i, j], "form": "harmonic", "params": {"r0_nm": r0, "k_kjmol_nm2": k}}

    def angle(i, j, k, t0, kk):
        return {"atoms": [i, j, k], "form": "harmonic", "params": {"theta0_deg": t0, "k_kjmol_rad2": kk}}

    charges = [0.3, -0.25, 0.15, -0.4, 0.1, 0.1]
    types = ["A", "B", "A", "B", "A", "C"]
    mol = {
        "description": "synthetic: every bonded form with asymmetric phases (test numbers, not a force field)",
        "formal_charge_e": 0,
        "atoms": [
            {"name": f"X{k}", "element": "C", "mass_amu": 12.011, "charge_e": q, "type": t}
            for k, (q, t) in enumerate(zip(charges, types, strict=True))
        ],
        "bonds": [bond(0, 1, 0.153, 2.2e5), bond(1, 2, 0.141, 2.7e5), bond(2, 3, 0.123, 4.8e5),
                  bond(3, 4, 0.109, 2.8e5), bond(1, 5, 0.150, 3.1e5)],
        "angles": [angle(0, 1, 2, 110.0, 400.0), angle(0, 1, 5, 108.5, 350.0), angle(2, 1, 5, 120.0, 500.0),
                   angle(1, 2, 3, 116.9, 690.0), angle(2, 3, 4, 109.5, 290.0)],
        "dihedrals": [
            {"atoms": [0, 1, 2, 3], "form": "periodic", "params": {"k_kjmol": 2.5, "n": 1, "phi0_deg": 30.0}},
            {"atoms": [0, 1, 2, 3], "form": "periodic", "params": {"k_kjmol": 1.2, "n": 3, "phi0_deg": 0.0}},
            {"atoms": [1, 2, 3, 4], "form": "ryckaert-bellemans",
             "params": {f"c{i}_kjmol": c for i, c in enumerate([9.28, 12.16, -13.12, -3.06, 26.24, -31.5])}},
            {"atoms": [5, 1, 2, 3], "form": "opls-fourier",
             "params": {"v1_kjmol": 3.0, "v2_kjmol": -1.5, "v3_kjmol": 0.8, "v4_kjmol": 0.4}},
        ],
        "impropers": [
            {"atoms": [0, 1, 2, 5], "form": "periodic", "params": {"k_kjmol": 43.9, "n": 2, "phi0_deg": 160.0}},
            {"atoms": [2, 1, 5, 0], "form": "harmonic", "params": {"xi0_deg": 25.0, "k_kjmol_rad2": 80.0}},
        ],
    }
    doc = {
        "format": "ucmd-system",
        "spec_version": "0.1.0",
        "name": "allforms",
        "description": "Synthetic molecule pinning the engine's bonded conventions to OpenMM's.",
        "units": {"length": "nm", "time": "ps", "mass": "amu", "energy": "kJ/mol", "charge": "e",
                  "temperature": "K", "angle": "deg"},
        "periodicity": [False, False, False],
        "cell_nm": None,
        "molecule_types": {"allforms": mol},
        "components": [{"molecule_type": "allforms", "count": 1}],
        "atom_count": 6,
        "forcefield": {
            "name": "synthetic test parameters",
            "combination_rule": "geometric",
            "scale_14_lj": 0.5,
            "scale_14_coulomb": 0.8333,
            "atom_types": {
                "A": {"sigma_nm": 0.35, "epsilon_kjmol": 0.276},
                "B": {"sigma_nm": 0.296, "epsilon_kjmol": 0.879},
                "C": {"sigma_nm": 0.25, "epsilon_kjmol": 0.126},
            },
        },
        "provenance": {"created_by": "tools/oracle/make_molecule_references.py", "created_utc": "2026-11-12T00:00:00Z"},
    }
    (target / "system.json").write_text(json.dumps(doc, indent=1) + "\n")
    np.save(target / "positions.npy", ALLFORMS_XYZ.astype("<f8"))
    return target


def evaluate(case: Path) -> None:
    top = oracle.load_topology(case)
    system = oracle.molecular_system(top)
    terms = oracle.energy_terms(system, top.positions_nm)
    forces = oracle.term_forces(system, top.positions_nm)
    for name, f in forces.items():
        np.save(case / f"forces-{name}.npy", np.ascontiguousarray(f, dtype="<f8"))
    total = sum(v for k, v in terms.items() if k != "total")
    assert math.isclose(total, terms["total"], rel_tol=1e-12, abs_tol=1e-9)
    (case / "terms.json").write_text(
        json.dumps({"openmm": openmm.__version__, "platform": "Reference", "terms_kjmol": terms}, indent=1) + "\n"
    )
    print(case.name, {k: round(v, 6) for k, v in terms.items()})


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cases = [store_without_periodicity(Path(p), json.loads((Path(p) / "system.json").read_text())["name"])
             for p in sys.argv[1:]]
    cases.append(write_allforms())
    if not sys.argv[1:]:
        cases = sorted(p for p in OUT.iterdir() if (p / "system.json").is_file())
    for case in cases:
        evaluate(case)


if __name__ == "__main__":
    main()
