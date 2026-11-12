"""Validation of H5MD trajectories (spec/trajectory-h5md.md §3). Needs the optional h5py."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from .report import Invalid, Report

REQUIRED_UNITS = {
    "particles/all/position/value": "nm",
    "particles/all/position/time": "ps",
    "particles/all/box/edges/value": "nm",
    "particles/all/mass": "amu",
}
OPTIONAL_UNITS = {
    "particles/all/velocity/value": "nm ps-1",
    "particles/all/force/value": "kJ mol-1 nm-1",
    "observables/potential_energy/value": "kJ mol-1",
    "observables/kinetic_energy/value": "kJ mol-1",
    "observables/conserved_energy/value": "kJ mol-1",
    "observables/temperature/value": "K",
    "observables/pressure/value": "bar",
    "observables/volume/value": "nm3",
}


def validate_trajectory(path: Path | str) -> Report:
    path = Path(path)
    report = Report(str(path))
    try:
        _validate(path)
    except Invalid as exc:
        report.issues.append(exc.issue)
    return report


def _text(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    if isinstance(value, np.ndarray) and value.shape == ():
        return _text(value.item())
    return str(value)


def _validate(path: Path) -> None:
    try:
        import h5py
    except ImportError as exc:  # pragma: no cover - depends on the environment
        raise Invalid(
            "E_H5MD_STRUCTURE", "h5py is needed: pip install 'ucmd-spec[trajectory]'"
        ) from exc
    try:
        fh = h5py.File(path, "r")
    except OSError as exc:
        raise Invalid("E_H5MD_STRUCTURE", f"not a readable HDF5 file ({exc})") from exc
    with fh:
        for group in ("h5md", "h5md/author", "h5md/creator", "particles/all", "parameters/ucmd"):
            if group not in fh:
                raise Invalid("E_H5MD_STRUCTURE", f"missing group /{group}", f"/{group}")
        version = tuple(int(v) for v in np.asarray(fh["h5md"].attrs.get("version", [])).ravel())
        if version != (1, 1):
            raise Invalid(
                "E_H5MD_STRUCTURE", f"/h5md version must be [1, 1], got {version}", "/h5md"
            )
        for name in ("system_json", "run_config_toml"):
            if name not in fh["parameters/ucmd"]:
                raise Invalid("E_H5MD_STRUCTURE", f"missing /parameters/ucmd/{name}")
        system = json.loads(_text(fh["parameters/ucmd/system_json"][()]))
        n_atoms = int(system["atom_count"])

        for dataset, unit in {**REQUIRED_UNITS, **OPTIONAL_UNITS}.items():
            if dataset not in fh:
                if dataset in REQUIRED_UNITS:
                    raise Invalid("E_H5MD_STRUCTURE", f"missing /{dataset}", f"/{dataset}")
                continue
            found = _text(fh[dataset].attrs.get("unit", ""))
            if found != unit:
                raise Invalid(
                    "E_H5MD_UNITS", f"/{dataset}: unit {found!r}, expected {unit!r}", f"/{dataset}"
                )

        position = fh["particles/all/position"]
        step, value = np.asarray(position["step"]), position["value"]
        if value.ndim != 3 or value.shape[1:] != (n_atoms, 3) or value.shape[0] != step.shape[0]:
            raise Invalid(
                "E_H5MD_SHAPE",
                f"position/value has shape {value.shape}, "
                f"expected (n, {n_atoms}, 3) with n = {step.shape[0]}",
                "/particles/all/position/value",
            )
        if step.size > 1 and not np.all(np.diff(step) > 0):
            raise Invalid(
                "E_H5MD_SHAPE",
                "position/step is not strictly increasing",
                "/particles/all/position/step",
            )
        edges = fh["particles/all/box/edges/value"]
        if edges.shape[1:] != (3, 3):
            raise Invalid(
                "E_H5MD_SHAPE", f"box/edges/value has shape {edges.shape}, expected (n, 3, 3)"
            )
        for frame in range(value.shape[0]):
            if not np.isfinite(value[frame]).all():
                raise Invalid(
                    "E_NONFINITE",
                    f"non-finite position in frame {frame}",
                    "/particles/all/position/value",
                )
