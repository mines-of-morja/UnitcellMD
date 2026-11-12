# OpenMM oracle

Reference energies, forces and virials for UnitcellMD system packages, used **only for
validation** (PLAN.md D10). Nothing in the engine, builder or analysis may import it.

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest test_oracle.py     # the oracle checked against an independent NumPy implementation
.venv/bin/python make_references.py           # regenerate reference/ (committed)
```

| File | Content |
|---|---|
| `oracle.py` | package → OpenMM System (v0: Lennard-Jones with the engine's cutoff modes; bonded terms and PME in E2) |
| `test_oracle.py` | OpenMM vs. NumPy brute force (energy 1e-10, forces 1e-9 relative); finite-difference strain virial; dispersion correction |
| `make_references.py` | writes `reference/argon-864/lj-{truncate,potential-shift}-rc0.85.{json,-forces.npy}` for the engine tests (E1.7) |
| `requirements.txt` | pinned versions the references were produced with |

Units: identical to the spec (nm, kJ/mol, amu), so nothing is converted.
