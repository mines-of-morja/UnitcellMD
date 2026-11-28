"""The PF6 size map (README: plan and reading rule). Standard library only.

    python3 analyze.py OUT.json

Densities with SC-4's functions (thermo volume, package mass, first 1 ns of 3 skipped). The apparent molar
volume uses the model's solvent density rho0 of docs/research/density-c-T/apparent_volume.json (the PF6 size does
not change the solvent) and each run's own concentration.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sc4 = _load("sc4", HERE.parent / "2026-11-27_density-concentration-M1/analyze.py")
av = _load("av", ROOT / "docs/research/density-c-T/apparent_volume.py")
PROBES = (0.95, 1.05)
BASE = ("2026-11-27_density-concentration-M1", "m1_3.0M")


def reading(removed_fraction: float) -> str:
    """README reading rule 1, for the x0.95 probe."""
    if removed_fraction >= 0.75:
        return "carries most of the excess"
    if removed_fraction >= 0.25:
        return "carries part of the excess"
    return "carries little of the excess"


def main(out_path: str) -> None:
    ref = json.loads((ROOT / "docs/research/density-c-T/apparent_volume.json").read_text())
    rho0, m = ref["model"]["rho0"], ref["salt_molar_mass_g_mol"]
    excess = ref["model"]["v_phi_excess_cm3_mol"]
    runs = {"base": sc4.point(*BASE, "T20C", 1000.0, 3000.0)}
    for f in PROBES:
        runs[f"x{f:.2f}"] = sc4.point(HERE.name, f"m1_3.0M_sigmaPF6_x{f:.2f}", "T20C", 1000.0, 3000.0)
    for p in runs.values():
        p["v_phi_cm3_mol"] = av.v_phi(p["rho"], p["c_mol_l"], rho0, m)
    dv = {k: runs[k]["v_phi_cm3_mol"] - runs["base"]["v_phi_cm3_mol"] for k in runs if k != "base"}
    removed = -dv["x0.95"] / excess
    out = {
        "runs": runs,
        "delta_v_phi_cm3_mol": dv,
        "excess_v_phi_cm3_mol": excess,
        "removed_fraction_x0.95": removed,
        "reading": reading(removed),
        "settled": all(abs(p["halves_pct"]) <= sc4.SETTLE_PCT for p in runs.values()),
    }
    Path(out_path).write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
