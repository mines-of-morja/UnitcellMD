"""Reference single point of a periodic box with PME, per energy term (E2.4, M2a).

    tools/oracle/.venv/bin/python tools/oracle/make_box_references.py PACKAGE NAME \
        [--cutoff-nm 1.4] [--tolerance 1e-5]

The package is stored under reference/<NAME>/ (system.json, positions.npy).
- PME parameters: α = √(−ln(2·tol))/r_c and the grid n_d = ⌈2α·h_d/(3·tol^{1/5})⌉, made
  FFT-friendly (factors 2, 3, 5, 7). These are OpenMM's rules and the engine's defaults.
- They are passed to OpenMM explicitly and recorded, so the engine test can use exactly the same
  values. OpenMM's PME uses B-splines of order 5.
- LJ is truncated at the cutoff, without a tail correction; 1-4 pairs are computed without
  cutoff (oracle v1).
- Stored: terms.json (energy per term), forces-total.npy and forces-coulomb.npy (kJ mol⁻¹ nm⁻¹).
"""

import argparse
import json
import math
import shutil
from pathlib import Path

import numpy as np
import openmm

import oracle

HERE = Path(__file__).resolve().parent


def legal_size(n: int) -> int:
    m = max(n, 1)
    while True:
        r = m
        for f in (2, 3, 5, 7):
            while r % f == 0:
                r //= f
        if r == 1:
            return m
        m += 1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("package", type=Path)
    ap.add_argument("name")
    ap.add_argument("--cutoff-nm", type=float, default=1.4)
    ap.add_argument("--tolerance", type=float, default=1e-5)
    args = ap.parse_args()
    out = HERE / "reference" / args.name
    out.mkdir(parents=True, exist_ok=True)
    shutil.copy(args.package / "system.json", out / "system.json")
    shutil.copy(args.package / "positions.npy", out / "positions.npy")
    top = oracle.load_topology(out)
    rc, tol = args.cutoff_nm, args.tolerance
    alpha = math.sqrt(-math.log(2.0 * tol)) / rc
    heights = [top.cell_nm[d, d] for d in range(3)]
    grid = [legal_size(math.ceil(2.0 * alpha * h / (3.0 * tol**0.2))) for h in heights]
    system = oracle.molecular_system(top, cutoff_nm=rc, pme_parameters=(alpha, *grid))
    terms = oracle.energy_terms(system, top.positions_nm, top.cell_nm)
    forces = oracle.term_forces(system, top.positions_nm, top.cell_nm)
    # Two force files keep the reference small: the total, and the Coulomb part that PME decides.
    total = sum(forces.values())
    np.save(out / "forces-total.npy", np.ascontiguousarray(total, dtype="<f8"))
    np.save(out / "forces-coulomb.npy", np.ascontiguousarray(forces["coulomb"], dtype="<f8"))
    (out / "terms.json").write_text(
        json.dumps(
            {
                "openmm": openmm.__version__,
                "platform": "Reference",
                "cutoff_nm": rc,
                "ewald_tolerance": tol,
                "ewald_alpha_per_nm": alpha,
                "pme_grid": grid,
                "pme_order": 5,
                "lj": "truncate, no tail correction",
                "terms_kjmol": terms,
            },
            indent=1,
        )
        + "\n"
    )
    print(args.name, "alpha", round(alpha, 6), "grid", grid, {k: round(v, 4) for k, v in terms.items()})


if __name__ == "__main__":
    main()
