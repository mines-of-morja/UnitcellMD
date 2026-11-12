"""Strict reader for the state arrays of system-package.md §6."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from numpy.lib import format as npy_format

from .report import Invalid


def read_vec3_array(path: Path, n_atoms: int) -> np.ndarray:
    """Read an (n_atoms, 3) little-endian float64 C-order NPY 1.0/2.0 array, all finite."""
    what = path.name
    if not path.is_file():
        raise Invalid("E_ARRAY_MISSING", f"{what} is missing", what)
    with path.open("rb") as fh:
        try:
            version = npy_format.read_magic(fh)
            if version == (1, 0):
                shape, fortran_order, dtype = npy_format.read_array_header_1_0(fh)
            elif version == (2, 0):
                shape, fortran_order, dtype = npy_format.read_array_header_2_0(fh)
            else:
                raise Invalid(
                    "E_ARRAY_FORMAT", f"{what}: NPY version {version} (allowed: 1.0, 2.0)", what
                )
        except (ValueError, OSError) as exc:
            raise Invalid("E_ARRAY_FORMAT", f"{what}: not a valid NPY file ({exc})", what) from exc
        if dtype.str != "<f8":
            raise Invalid("E_ARRAY_FORMAT", f"{what}: dtype {dtype.str} (required: <f8)", what)
        if fortran_order:
            raise Invalid("E_ARRAY_FORMAT", f"{what}: Fortran order (required: C order)", what)
        if tuple(shape) != (n_atoms, 3):
            raise Invalid(
                "E_ARRAY_FORMAT", f"{what}: shape {tuple(shape)} (required: ({n_atoms}, 3))", what
            )
        payload = fh.read(n_atoms * 3 * 8)
    if len(payload) != n_atoms * 3 * 8:
        raise Invalid("E_ARRAY_FORMAT", f"{what}: file is truncated", what)
    array = np.frombuffer(payload, dtype="<f8").reshape(n_atoms, 3)
    bad = np.argwhere(~np.isfinite(array))
    if bad.size:
        atom, component = (int(v) for v in bad[0])
        raise Invalid(
            "E_NONFINITE", f"{what}: non-finite value at atom {atom}, component {component}", what
        )
    return array
