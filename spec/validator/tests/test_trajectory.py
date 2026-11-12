import json

import h5py
import numpy as np
import pytest
from conftest import FIXTURES

from ucmd_spec.trajectory import validate_trajectory


def write_minimal(path, n_frames=3, n_atoms=None, unit="nm", steps=None):
    system = (FIXTURES / "valid" / "harmonic-3d" / "system.json").read_text()
    n_atoms = n_atoms or json.loads(system)["atom_count"]
    with h5py.File(path, "w") as f:
        f.create_group("h5md").attrs["version"] = np.array([1, 1], dtype=np.int32)
        f.create_group("h5md/author").attrs["name"] = "anonymous"
        creator = f.create_group("h5md/creator")
        creator.attrs["name"], creator.attrs["version"] = "test", "0"
        part = f.create_group("particles/all")
        pos = part.create_group("position")
        pos["step"] = np.array(steps if steps is not None else range(n_frames), dtype=np.int64)
        pos["time"] = pos["step"][()] * 0.001
        pos["time"].attrs["unit"] = "ps"
        pos["value"] = np.zeros((n_frames, n_atoms, 3))
        pos["value"].attrs["unit"] = unit
        edges = part.create_group("box/edges")
        edges["value"] = np.zeros((n_frames, 3, 3))
        edges["value"].attrs["unit"] = "nm"
        part["mass"] = np.ones(n_atoms)
        part["mass"].attrs["unit"] = "amu"
        par = f.create_group("parameters/ucmd")
        par["system_json"] = system
        par["run_config_toml"] = "spec_version = '0.1.0'"
    return path


def test_minimal_trajectory_is_valid(tmp_path) -> None:
    report = validate_trajectory(write_minimal(tmp_path / "t.h5"))
    assert report.ok, report.error


@pytest.mark.parametrize(
    ("kwargs", "code"),
    [
        ({"unit": "angstrom"}, "E_H5MD_UNITS"),
        ({"n_atoms": 5}, "E_H5MD_SHAPE"),
        ({"steps": [0, 2, 1]}, "E_H5MD_SHAPE"),
    ],
)
def test_broken_trajectories(tmp_path, kwargs, code) -> None:
    report = validate_trajectory(write_minimal(tmp_path / "t.h5", **kwargs))
    assert report.error is not None and report.error.code == code, report.error


def test_not_hdf5(tmp_path) -> None:
    (tmp_path / "x.h5").write_bytes(b"plain text")
    assert validate_trajectory(tmp_path / "x.h5").error.code == "E_H5MD_STRUCTURE"
