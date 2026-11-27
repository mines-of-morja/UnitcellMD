"""Apparent molar volume of the salt against zeta, at 1 M (scan, 1 fs) and 3 M (map, 0.5 fs). Added after the
3 M map was read; not part of its reading rule.

    python3 v_phi_zeta.py OUT.json

V_phi with apparent_volume.py's formula, each run's own concentration and the model's solvent density (zeta does
not change the solvent). The 1 M base is the scan's base_s1 (1 fs), the 3 M base SC-4's point (0.5 fs).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sc4 = _load("sc4", ROOT / "studies/2026-11-27_density-concentration-M1/analyze.py")
av = _load("av", HERE / "apparent_volume.py")
RUNS = {
    "1M": {
        0.65: ("2026-11-24_parameter-sensitivity-1M", "zeta_0.65", 1500.0, 5000.0),
        0.75: ("2026-11-24_parameter-sensitivity-1M", "base_s1", 1500.0, 5000.0),
        0.85: ("2026-11-24_parameter-sensitivity-1M", "zeta_0.85", 1500.0, 5000.0),
    },
    "3M": {
        0.65: ("2026-11-27_density-slope-3M", "m1_3.0M_zeta_0.65", 1000.0, 3000.0),
        0.75: ("2026-11-27_density-concentration-M1", "m1_3.0M", 1000.0, 3000.0),
        0.85: ("2026-11-27_density-slope-3M", "m1_3.0M_zeta_0.85", 1000.0, 3000.0),
    },
}


def main(out_path: str) -> None:
    ref = json.loads((HERE / "apparent_volume.json").read_text())
    rho0, m = ref["model"]["rho0"], ref["salt_molar_mass_g_mol"]
    exp_v = ref["experiment"]["v_phi_cm3_mol"]
    out: dict = {"experiment_v_phi_cm3_mol": exp_v}
    for box, runs in RUNS.items():
        rows = {}
        for zeta, (study, run, skip, end) in runs.items():
            p = sc4.point(study, run, "T20C", skip, end)
            rows[f"{zeta:.2f}"] = {
                "rho": p["rho"],
                "c_mol_l": p["c_mol_l"],
                "halves_pct": p["halves_pct"],
                "v_phi_cm3_mol": av.v_phi(p["rho"], p["c_mol_l"], rho0, m),
            }
        dv = (rows["0.85"]["v_phi_cm3_mol"] - rows["0.65"]["v_phi_cm3_mol"]) / 0.20
        out[box] = {"runs": rows, "dv_phi_dzeta_cm3_mol": dv}
    Path(out_path).write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
