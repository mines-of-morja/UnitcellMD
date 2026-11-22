"""Write the reference single points for argon-864 (E1.7) and kob-andersen-500 (spec 0.1.2).

    tools/oracle/.venv/bin/python tools/oracle/make_references.py

Energies and forces come from OpenMM (Reference platform, double precision). The virial tensor
comes from the independent NumPy brute force in test_oracle.py, whose energies and forces
agree with OpenMM to 1e-10 / 1e-9 and whose virial trace matches the finite-difference strain
derivative of the OpenMM energy (potential-shift mode).
"""

import json
from pathlib import Path

import numpy as np
import openmm

import oracle

HERE = Path(__file__).resolve().parent
FIXTURES = HERE.parents[1] / "spec" / "fixtures" / "valid"
CUTOFF_NM = 0.85


def virial_tensor(pkg: oracle.Package, cutoff_nm: float) -> np.ndarray:
    box = pkg.cell_nm[0, 0]
    if pkg.pairs is None:  # one type (argon)
        sigma, eps = pkg.sigma_nm[0], pkg.epsilon_kjmol[0]
    else:  # per pair, with the overrides (spec 0.1.2)
        t = pkg.pairs.type_index
        sigma = pkg.pairs.sigma_nm[t[:, None], t[None, :]]
        eps = pkg.pairs.epsilon_kjmol[t[:, None], t[None, :]]
    d = pkg.positions_nm[:, None, :] - pkg.positions_nm[None, :, :]
    d -= box * np.round(d / box)
    r2 = (d**2).sum(-1)
    np.fill_diagonal(r2, np.inf)
    inside = r2 < cutoff_nm**2
    sr6 = np.where(inside, (sigma**2 / r2) ** 3, 0.0)
    f_over_r = np.where(inside, 24 * eps * (2 * sr6**2 - sr6) / r2, 0.0)
    # W = sum_{i<j} r_ij (x) F_ij  with F_ij = f_over_r * r_ij
    return 0.5 * np.einsum("ij,ija,ijb->ab", f_over_r, d, d)


def main() -> None:
    for name in ("argon-864", "kob-andersen-500"):
        write(name)


def write(name: str) -> None:
    out = HERE / "reference" / name
    out.mkdir(parents=True, exist_ok=True)
    pkg = oracle.load_package(FIXTURES / name)
    tail = (
        oracle.lj_dispersion_correction(pkg, CUTOFF_NM)
        if pkg.pairs is None
        else oracle.lj_dispersion_correction_types(pkg, CUTOFF_NM)  # N_a N_b, as the engine
    )
    for mode in ("truncate", "potential-shift"):
        energy, forces = oracle.evaluate(oracle.lj_system(pkg, CUTOFF_NM, mode), pkg.positions_nm, pkg.cell_nm)
        stem = f"lj-{mode}-rc{CUTOFF_NM}"
        np.save(out / f"{stem}-forces.npy", np.ascontiguousarray(forces, dtype="<f8"))
        record = {
            "package": f"spec/fixtures/valid/{name}",
            "provider": {"kind": "lennard-jones", "cutoff_nm": CUTOFF_NM, "cutoff_mode": mode,
                         "dispersion_correction": False},
            "energy_kjmol": energy,
            "forces_file": f"{stem}-forces.npy",
            "virial_kjmol": virial_tensor(pkg, CUTOFF_NM).tolist(),
            "dispersion_correction_energy_kjmol": tail,
            "generated_by": f"tools/oracle/make_references.py, OpenMM {openmm.__version__} Reference platform",
        }
        (out / f"{stem}.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        print(name, stem, f"E = {energy:.6f} kJ/mol")


if __name__ == "__main__":
    main()
