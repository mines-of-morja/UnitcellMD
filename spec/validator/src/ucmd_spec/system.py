"""Validation of system packages (spec/system-package.md §7).

Checks run in the order fixed by the spec and stop at the first error:
E_JSON, E_FORMAT, E_VERSION, E_UNITS, E_SCHEMA, E_REFERENCE, E_INDEX, E_ATOM_COUNT, E_CELL,
E_PARAMETERS, E_NET_CHARGE, E_ARRAY_MISSING / E_ARRAY_FORMAT / E_NONFINITE (positions, then
velocities), E_MOLECULE_SPLIT. Warnings (W_*) are collected along the way.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from .common import check_schema, check_spec_version
from .npy import read_vec3_array
from .report import Invalid, Issue, Report

CANONICAL_UNITS = {
    "length": "nm",
    "time": "ps",
    "mass": "amu",
    "energy": "kJ/mol",
    "charge": "e",
    "temperature": "K",
    "angle": "deg",
}
BONDED = ("bonds", "angles", "dihedrals", "impropers")
INDEXED = (*BONDED, "constraints")

#: |sum of partial charges| allowed for periodic systems, in e.
NET_CHARGE_TOLERANCE_E = 1e-6
#: relative slack on the reduced-cell inequalities (floating-point noise only).
REDUCED_CELL_TOLERANCE = 1e-9


def validate_system_package(package: Path | str) -> Report:
    """Validate a system package directory. The report holds at most one error."""
    package = Path(package)
    report = Report(str(package))
    try:
        _validate(package, report)
    except Invalid as exc:
        report.issues.append(exc.issue)
    return report


def load_system_document(package: Path) -> Any:
    path = package / "system.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise Invalid("E_JSON", "system.json is missing", "system.json") from exc
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise Invalid("E_JSON", f"system.json is not valid JSON ({exc})", "system.json") from exc


def _validate(package: Path, report: Report) -> None:
    doc = load_system_document(package)
    if not isinstance(doc, dict) or doc.get("format") != "ucmd-system":
        found = doc.get("format") if isinstance(doc, dict) else type(doc).__name__
        raise Invalid("E_FORMAT", f'format must be "ucmd-system", got {found!r}', "/format")
    check_spec_version(doc.get("spec_version"))
    if doc.get("units") != CANONICAL_UNITS:
        raise Invalid("E_UNITS", f"units must be exactly {CANONICAL_UNITS}", "/units")
    check_schema(doc, "system")

    molecule_types: dict[str, Any] = doc["molecule_types"]
    components: list[dict[str, Any]] = doc["components"]
    forcefield: dict[str, Any] | None = doc.get("forcefield")
    periodic = any(doc["periodicity"])

    _check_references(molecule_types, components, forcefield)
    _check_indices(molecule_types)
    _check_atom_count(doc["atom_count"], molecule_types, components)
    _check_cell(doc["periodicity"], doc["cell_nm"])
    charges_present = _check_parameters(molecule_types, forcefield)
    if periodic and charges_present:
        _check_net_charge(molecule_types, components)

    n_atoms = doc["atom_count"]
    positions = read_vec3_array(package / "positions.npy", n_atoms)
    if (package / "velocities.npy").exists():
        read_vec3_array(package / "velocities.npy", n_atoms)

    if periodic:
        _check_whole_molecules(doc, positions)
        formal = sum(
            c["count"] * molecule_types[c["molecule_type"]]["formal_charge_e"] for c in components
        )
        if formal != 0:
            report.issues.append(
                Issue("W_FORMAL_CHARGE", f"formal charges sum to {formal} e, not 0", "/components")
            )


def _check_references(
    molecule_types: dict[str, Any],
    components: list[dict[str, Any]],
    forcefield: dict[str, Any] | None,
) -> None:
    for k, component in enumerate(components):
        if component["molecule_type"] not in molecule_types:
            raise Invalid(
                "E_REFERENCE",
                f"component {k} names unknown molecule type {component['molecule_type']!r}",
                f"/components/{k}",
            )
    if forcefield is None:
        return
    atom_types = forcefield["atom_types"]
    for name, mtype in molecule_types.items():
        for k, atom in enumerate(mtype["atoms"]):
            if "type" in atom and atom["type"] not in atom_types:
                raise Invalid(
                    "E_REFERENCE",
                    f"atom {k} of molecule type {name!r} names unknown atom type {atom['type']!r}",
                    f"/molecule_types/{name}/atoms/{k}",
                )


def _check_indices(molecule_types: dict[str, Any]) -> None:
    for name, mtype in molecule_types.items():
        n_atoms = len(mtype["atoms"])
        for kind in INDEXED:
            for k, entry in enumerate(mtype.get(kind, [])):
                atoms = entry["atoms"]
                location = f"/molecule_types/{name}/{kind}/{k}"
                if max(atoms) >= n_atoms:
                    raise Invalid(
                        "E_INDEX",
                        f"{kind}[{k}] of {name!r} uses atom {max(atoms)}, "
                        f"but the type has {n_atoms} atoms",
                        location,
                    )
                if len(set(atoms)) != len(atoms):
                    raise Invalid("E_INDEX", f"{kind}[{k}] of {name!r} repeats an atom", location)


def _check_atom_count(
    atom_count: int, molecule_types: dict[str, Any], components: list[dict[str, Any]]
) -> None:
    expected = sum(
        c["count"] * len(molecule_types[c["molecule_type"]]["atoms"]) for c in components
    )
    if atom_count != expected:
        raise Invalid(
            "E_ATOM_COUNT", f"atom_count is {atom_count}, components give {expected}", "/atom_count"
        )


def _check_cell(periodicity: list[bool], cell: list[list[float]] | None) -> None:
    if any(periodicity) and cell is None:
        raise Invalid("E_CELL", "cell_nm is null although a direction is periodic", "/cell_nm")
    if not any(periodicity) and cell is not None:
        raise Invalid("E_CELL", "cell_nm must be null when no direction is periodic", "/cell_nm")
    if cell is None:
        return
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = cell
    if ay != 0 or az != 0 or bz != 0:
        raise Invalid(
            "E_CELL", "cell_nm must be lower-triangular (a_y = a_z = b_z = 0)", "/cell_nm"
        )
    if min(ax, by, cz) <= 0:
        raise Invalid("E_CELL", "cell_nm diagonal (a_x, b_y, c_z) must be positive", "/cell_nm")
    slack = REDUCED_CELL_TOLERANCE * max(ax, by, cz)
    if abs(bx) > ax / 2 + slack or abs(cx) > ax / 2 + slack or abs(cy) > by / 2 + slack:
        raise Invalid(
            "E_CELL",
            "cell_nm is not reduced (|b_x| <= a_x/2, |c_x| <= a_x/2, |c_y| <= b_y/2)",
            "/cell_nm",
        )


def _check_parameters(molecule_types: dict[str, Any], forcefield: dict[str, Any] | None) -> bool:
    """Check completeness rules; return whether partial charges are present."""
    atoms = [
        (name, k, atom)
        for name, mtype in molecule_types.items()
        for k, atom in enumerate(mtype["atoms"])
    ]
    with_charge = sum("charge_e" in atom for _, _, atom in atoms)
    if 0 < with_charge < len(atoms):
        raise Invalid("E_PARAMETERS", "charge_e must be given for all atoms or for none", "")
    for name, mtype in molecule_types.items():
        for k, atom in enumerate(mtype["atoms"]):
            if forcefield is not None and ("type" not in atom or "charge_e" not in atom):
                raise Invalid(
                    "E_PARAMETERS",
                    f"parameterized package: atom {k} of {name!r} needs type and charge_e",
                    f"/molecule_types/{name}/atoms/{k}",
                )
        for kind in BONDED:
            for k, entry in enumerate(mtype.get(kind, [])):
                location = f"/molecule_types/{name}/{kind}/{k}"
                if forcefield is not None and "form" not in entry:
                    raise Invalid(
                        "E_PARAMETERS",
                        f"parameterized package: {kind}[{k}] of {name!r} needs form and params",
                        location,
                    )
                if forcefield is None and "form" in entry:
                    raise Invalid(
                        "E_PARAMETERS",
                        f"{kind}[{k}] of {name!r} has parameters, "
                        "but the package has no forcefield",
                        location,
                    )
    return with_charge == len(atoms) and len(atoms) > 0


def _check_net_charge(molecule_types: dict[str, Any], components: list[dict[str, Any]]) -> None:
    total = sum(
        c["count"] * sum(atom["charge_e"] for atom in molecule_types[c["molecule_type"]]["atoms"])
        for c in components
    )
    if abs(total) > NET_CHARGE_TOLERANCE_E:
        raise Invalid(
            "E_NET_CHARGE",
            f"periodic system has net charge {total:.6g} e (tolerance {NET_CHARGE_TOLERANCE_E} e)",
            "/molecule_types",
        )


def perpendicular_heights(cell: np.ndarray) -> np.ndarray:
    """Distances between opposite cell faces, for the a, b and c directions (nm)."""
    a, b, c = cell
    volume = abs(float(np.linalg.det(cell)))
    return np.array(
        [
            volume / np.linalg.norm(np.cross(b, c)),
            volume / np.linalg.norm(np.cross(c, a)),
            volume / np.linalg.norm(np.cross(a, b)),
        ]
    )


def _check_whole_molecules(doc: dict[str, Any], positions: np.ndarray) -> None:
    cell = np.array(doc["cell_nm"], dtype=float)
    heights = perpendicular_heights(cell)
    limit = 0.5 * min(h for h, p in zip(heights, doc["periodicity"], strict=True) if p)
    offset = 0
    for component in doc["components"]:
        mtype = doc["molecule_types"][component["molecule_type"]]
        n_atoms, count = len(mtype["atoms"]), component["count"]
        pairs = [e["atoms"] for e in mtype["bonds"]] + [
            e["atoms"] for e in mtype.get("constraints", [])
        ]
        if pairs:
            pair_index = np.asarray(pairs)
            first = offset + n_atoms * np.arange(count)[:, None]
            i = (first + pair_index[:, 0]).ravel()
            j = (first + pair_index[:, 1]).ravel()
            distances = np.linalg.norm(positions[i] - positions[j], axis=1)
            worst = int(np.argmax(distances))
            if distances[worst] > limit:
                raise Invalid(
                    "E_MOLECULE_SPLIT",
                    f"atoms {i[worst]} and {j[worst]} ({component['molecule_type']!r}) are "
                    f"{distances[worst]:.4f} nm apart, more than half the smallest cell height "
                    f"({limit:.4f} nm): the molecule is not whole",
                    "positions.npy",
                )
        offset += n_atoms * count
