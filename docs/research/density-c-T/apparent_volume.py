"""Apparent molar volume of LiPF6 in EC:EMC 3:7 (w), model M1 (SC-4) against Landesfeind 2019.

For a solution of c mol/L with density rho and solvent density rho0 (g/cm3), the salt's apparent
molar volume is

    V_phi = (1000 - (1000 rho - c M) / rho0) / c        (cm3/mol, M the salt's molar mass in g/mol)

i.e. the volume of one litre minus the volume its solvent alone would take, per mole of salt.
A density linear in c, rho = rho0 + s c, gives the constant V_phi = (M - 1000 s) / rho0.

- Experiment: Landesfeind's fit at the same T (it is linear in c, so V_phi is one number).
- Model: rho0 is the intercept of a straight line through the four 20 C points of SC-4; V_phi
  is given per point and from the slope. The residuals show whether the model's rho(c) is straight.
- M comes from the package's masses (Li + PF6 molecule types), not from a typed literal.

    python3 apparent_volume.py OUT.json        (reads sc4.json next to this file)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PACKAGE = ROOT / "studies/2026-11-27_density-concentration-M1/systems/m1_3.0M/minimized.ucsys"
LABELS_20C = ("0.1 M, 20 C", "1 M, 20 C", "2 M, 20 C", "3 M, 20 C")
T_K = 293.15
P1, P2, P3 = 1.41, 0.0912, -0.00109  # Landesfeind 2019 Eq. S1, as in the SC-4 analysis


def salt_molar_mass(package: Path) -> float:
    """g/mol of one Li + one PF6 (the masses in amu equal g/mol)."""
    doc = json.loads((package / "system.json").read_text())
    types = doc["molecule_types"]
    return sum(sum(a["mass_amu"] for a in types[name]["atoms"]) for name in ("Li", "PF6"))


def v_phi(rho: float, c: float, rho0: float, m: float) -> float:
    """cm3/mol; rho, rho0 in g/cm3, c in mol/L, m in g/mol."""
    return (1000.0 - (1000.0 * rho - c * m) / rho0) / c


def line(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """Least-squares intercept and slope."""
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    return my - slope * mx, slope


def main(out: Path) -> None:
    sc4 = json.loads((HERE / "sc4.json").read_text())["points"]
    m = salt_molar_mass(PACKAGE)
    cs = [sc4[k]["c_mol_l"] for k in LABELS_20C]
    rhos = [sc4[k]["rho"] for k in LABELS_20C]
    rho0, s = line(cs, rhos)
    exp_rho0 = P1 + P3 * T_K
    exp_v = (m - 1000.0 * P2) / exp_rho0
    model = {
        k: {
            "c_mol_l": c,
            "rho": r,
            "residual_from_line": r - (rho0 + s * c),
            "v_phi_cm3_mol": v_phi(r, c, rho0, m),
        }
        for k, c, r in zip(LABELS_20C, cs, rhos)
    }
    res = {
        "salt_molar_mass_g_mol": m,
        "T_K": T_K,
        "experiment": {"rho0": exp_rho0, "slope": P2, "v_phi_cm3_mol": exp_v},
        "model": {
            "rho0": rho0,
            "slope": s,
            "v_phi_from_slope_cm3_mol": (m - 1000.0 * s) / rho0,
            "rho0_vs_experiment_pct": 100.0 * (rho0 / exp_rho0 - 1.0),
            "points": model,
        },
    }
    res["model"]["v_phi_excess_cm3_mol"] = res["model"]["v_phi_from_slope_cm3_mol"] - exp_v
    out.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]))
