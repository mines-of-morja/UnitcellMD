"""cluster_dft.py --no-cp (trial T6, amendment 5), with a stub in place of Psi4.

    tools/oracle/.venv/bin/python -m pytest tools/qm/test_cluster_dft.py

The stub checks which energies are asked for, and that E_bind does not depend on counterpoise. It
does not check Psi4's numbers.
"""

import sys
import types
from pathlib import Path

import pytest

sys.modules.setdefault("psi4", types.SimpleNamespace(__version__="stub"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cluster_dft

CO2 = [("C", 0.0, 0.0, 0.0), ("O", 1.16, 0.0, 0.0), ("O", -1.16, 0.0, 0.0)]


@pytest.fixture
def calls(monkeypatch):
    seen = []

    def energy(f, atoms, charge, ghost=frozenset()):
        seen.append((len(atoms), len(ghost)))
        real = [a for i, a in enumerate(atoms) if i not in ghost]
        return (
            -sum(1.0 + 0.01 * abs(a[1]) for a in real) - 0.001 * len(ghost) - 0.1 * (len(real) > 3)
        )

    monkeypatch.setattr(cluster_dft, "energy", energy)
    monkeypatch.setattr(cluster_dft, "optimize", lambda f, atoms, q: atoms)
    return seen


def start(tmp_path):
    atoms = [("Li", 4.0, 0.0, 0.0), *CO2, *[(e, x + 8.0, y, z) for e, x, y, z in CO2]]
    p = tmp_path / "s.xyz"
    body = "\n".join(f"{e} {x} {y} {z}" for e, x, y, z in atoms)
    p.write_text(f"{len(atoms)}\n\n{body}\n")
    return p


def test_no_cp_asks_for_no_ghost_energies(tmp_path, calls):
    row = cluster_dft.run_one(start(tmp_path), "f", cp=False)
    assert sum(g > 0 for _, g in calls) == 0
    assert len(calls) == 4  # complex, Li, two solvents alone
    assert row["counterpoise"] is False
    assert row["e_bind_cp_kcalmol"] is None
    assert row["e_int_cp_at_complex_kcalmol"] is None


def test_e_bind_does_not_depend_on_counterpoise(tmp_path, calls):
    p = start(tmp_path)
    with_cp, without = cluster_dft.run_one(p, "f"), cluster_dft.run_one(p, "f", cp=False)
    assert with_cp["e_bind_kjmol"] == without["e_bind_kjmol"]
    assert with_cp["counterpoise"] is True
    assert with_cp["e_bind_cp_kcalmol"] != with_cp["e_bind_kcalmol"]
    assert sum(g > 0 for _, g in calls) == 3  # Li and two solvents, from the CP run only
