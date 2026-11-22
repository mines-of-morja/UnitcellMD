"""Physics sanity of the valid fixtures, and the committed fixtures equal the generator output."""

import filecmp
import importlib.util
import math

import numpy as np
from conftest import FIXTURES, load_system

N_A = 6.02214076e23


def test_argon_density_and_state_point() -> None:
    doc = load_system(FIXTURES / "valid" / "argon-864")
    box = doc["cell_nm"][0][0]
    density_g_cm3 = 864 * 39.948 / N_A / (box**3 * 1e-21)
    assert math.isclose(density_g_cm3, 1.374, rel_tol=1e-5)
    lj = doc["forcefield"]["atom_types"]["Ar"]
    assert lj["sigma_nm"] == 0.34
    assert math.isclose(lj["epsilon_kjmol"] / 0.00831446261815324, 120.0, rel_tol=1e-12)


def test_kob_andersen_parameters_and_state_point() -> None:
    """Kob & Andersen 1995: sigma_BB 0.88, eps_BB 0.5, sigma_AB 0.8, eps_AB 1.5; rho sigma^3 1.2."""
    doc = load_system(FIXTURES / "valid" / "kob-andersen-500")
    ff = doc["forcefield"]
    a, b = ff["atom_types"]["A"], ff["atom_types"]["B"]
    (ab,) = ff["pair_overrides"]
    assert sorted(ab["types"]) == ["A", "B"]
    assert a["sigma_nm"] == 0.34
    assert math.isclose(b["sigma_nm"] / a["sigma_nm"], 0.88, rel_tol=1e-9)
    assert math.isclose(b["epsilon_kjmol"] / a["epsilon_kjmol"], 0.5, rel_tol=1e-12)
    assert math.isclose(ab["sigma_nm"] / a["sigma_nm"], 0.8, rel_tol=1e-9)
    assert math.isclose(ab["epsilon_kjmol"] / a["epsilon_kjmol"], 1.5, rel_tol=1e-12)
    counts = [c["count"] for c in doc["components"]]
    assert counts == [400, 100]
    box = doc["cell_nm"][0][0]
    assert math.isclose(500 / box**3 * a["sigma_nm"] ** 3, 1.2, rel_tol=1e-5)
    # the override is not what the combination rule would give
    assert not math.isclose(ab["sigma_nm"], 0.5 * (a["sigma_nm"] + b["sigma_nm"]), rel_tol=1e-3)


def test_argon_positions_are_a_perturbed_fcc_lattice() -> None:
    positions = np.load(FIXTURES / "valid" / "argon-864" / "positions.npy")
    box = load_system(FIXTURES / "valid" / "argon-864")["cell_nm"][0][0]
    lattice_spacing = box / 6
    # nearest-neighbour distance of FCC is a/sqrt(2); displacements are at most 0.005 nm per axis
    d = positions[:, None, :] - positions[None, :, :]
    d -= box * np.round(d / box)
    r = np.sqrt((d**2).sum(-1)) + np.eye(864) * 10
    assert abs(r.min() - lattice_spacing / math.sqrt(2)) < 0.02


def test_water_geometry_is_close_to_spcfw_equilibrium() -> None:
    positions = np.load(FIXTURES / "valid" / "water-2" / "positions.npy")
    for o in (0, 3):
        r1 = np.linalg.norm(positions[o + 1] - positions[o])
        r2 = np.linalg.norm(positions[o + 2] - positions[o])
        cos_t = np.dot(positions[o + 1] - positions[o], positions[o + 2] - positions[o]) / (r1 * r2)
        assert abs(r1 - 0.1012) < 0.006 and abs(r2 - 0.1012) < 0.006
        assert abs(math.degrees(math.acos(cos_t)) - 113.24) < 5.0


def test_nacl_is_a_perfect_rock_salt_lattice() -> None:
    positions = np.load(FIXTURES / "valid" / "nacl-crystal" / "positions.npy")
    box = load_system(FIXTURES / "valid" / "nacl-crystal")["cell_nm"][0][0]
    d = positions[:, None, :] - positions[None, :, :]
    d -= box * np.round(d / box)
    r = np.sqrt((d**2).sum(-1)) + np.eye(64) * 10
    assert np.allclose(r.min(axis=1), 0.282, atol=1e-12)


def test_committed_fixtures_equal_generator_output(tmp_path) -> None:
    spec = importlib.util.spec_from_file_location(
        "generate", FIXTURES / "_generators" / "generate.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.generate(tmp_path)

    def differing(cmp: filecmp.dircmp) -> list[str]:
        out = [f"{cmp.left}/{n}" for n in cmp.diff_files + cmp.left_only + cmp.right_only]
        for sub in cmp.subdirs.values():
            out.extend(differing(sub))
        return out

    for part in ("valid", "invalid", "runs"):
        cmp = filecmp.dircmp(FIXTURES / part, tmp_path / part, ignore=["__pycache__"])
        assert not differing(cmp), "fixtures are stale: run spec/fixtures/_generators/generate.py"
