"""Our EC package (builder, from the explicit itp) against OpenMM reading the ORIGINAL Caleman
files (96-49-1.top + oplsaaff.itp, type lookup), term by term, in vacuum.

    PYTHONPATH=../../tools/oracle <oracle venv>/bin/python compare_original.py PACKAGE TOPOLOGY

The package's atom order follows the recipe's SMILES; its atom types are named EC.t<k> after the
topology atom k, which gives the permutation. Tolerance 1e-8 relative per term (as
tools/oracle/compare_gromacs.py).
"""

import dataclasses
import json
import sys
from pathlib import Path

import numpy as np

import compare_gromacs
import oracle

pkg, topfile = Path(sys.argv[1]), Path(sys.argv[2])
doc = json.loads((pkg / "system.json").read_text())
atoms = next(iter(doc["molecule_types"].values()))["atoms"]
order = [int(a["type"].split(".t")[1]) - 1 for a in atoms]  # package atom → topology atom
top = dataclasses.replace(oracle.load_topology(pkg), cell_nm=None)
ours = oracle.energy_terms(oracle.molecular_system(top), top.positions_nm)
x_top = np.empty_like(top.positions_nm)
x_top[order] = top.positions_nm
theirs, masses = compare_gromacs.gromacs_terms(topfile, x_top)
assert np.allclose(masses[order], top.masses_amu, rtol=1e-6), "masses differ under the mapping"
worst = 0.0
for name in [*oracle.TERMS.values(), "total"]:
    a, b = ours[name], theirs[name]
    rel = abs(a - b) / max(abs(b), 1e-3)
    worst = max(worst, rel)
    print(f"{name:<10}{a:>20.10f}{b:>20.10f}{rel:>12.2e}")
print(f"{'PASS' if worst <= 1e-8 else 'FAIL'}: worst relative difference {worst:.2e}")
