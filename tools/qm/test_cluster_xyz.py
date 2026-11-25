"""cluster_xyz.py on a synthetic result (no Psi4).

    tools/oracle/.venv/bin/python -m pytest tools/qm/test_cluster_xyz.py
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cluster_xyz

LI = ("Li", 0.0, 0.0, 0.0)
A = [("C", 3.0, 0.0, 0.0), ("O", 1.9, 0.0, 0.0), ("O", 4.1, 0.0, 0.0)]
B = [(e, -x, y, z) for e, x, y, z in A]
FINAL = [LI, *A, *B]


def block(atoms, dx=0.0):
    rows = "".join(f"    {e:>2} {x + dx:15.10f} {y:15.10f} {z:15.10f}\n" for e, x, y, z in atoms)
    return f"Next Geometry in Ang \n\tFragment 1 (Ang)\n\n{rows}\n\n    Structure for next step:\n"


def result(tmp_path, out_text):
    row = {"start": "li_x.xyz", "solvents": ["EC", "EC"], "complex_xyz": FINAL}
    (tmp_path / "r.json").write_text(json.dumps([row]))
    (tmp_path / "r_li_x.out").write_text(out_text)
    return tmp_path / "r.json"


def test_path_holds_the_steps_of_the_complex_only(tmp_path):
    energy = "     1   -1375.64567440   -1.38e+03      3.19e-02 ~\n"
    text = energy + block(FINAL, 0.1) + energy + block(FINAL, 0.2) + block(A)  # A: a solvent alone
    final, path = cluster_xyz.export(result(tmp_path, text), tmp_path / "view")
    frames = path.read_text().splitlines()
    assert frames.count("7") == 3  # two steps and the final geometry
    assert "0.100000 0.000000 0.000000 0" in frames[2]
    assert "1375" not in path.read_text() + final.read_text()  # no energies


def test_molecules_are_numbered(tmp_path):
    assert cluster_xyz.molecules(FINAL) == [0, 1, 1, 1, 2, 2, 2]


def test_other_elements_are_an_error(tmp_path):
    wrong = [LI, *A, ("C", -3.0, 0.0, 0.0), ("O", -1.9, 0.0, 0.0), ("H", -4.1, 0.0, 0.0)]
    with pytest.raises(ValueError, match="other elements"):
        cluster_xyz.export(result(tmp_path, block(wrong)), tmp_path / "view")


def test_a_missing_output_is_an_error(tmp_path):
    r = result(tmp_path, block(FINAL))
    (tmp_path / "r_li_x.out").unlink()
    with pytest.raises(FileNotFoundError):
        cluster_xyz.export(r, tmp_path / "view")
