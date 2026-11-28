"""The 3 M density map after SC-4 (README: plan and reading rule). Standard library only.

    python3 analyze.py OUT.json

Densities with SC-4's own functions (thermo volume, package mass, first 1 ns skipped). The 1 M slopes come from the
scan's finished runs (1 fs, first 1.5 ns skipped), read the same way.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("sc4", HERE.parent / "2026-11-27_density-concentration-M1/analyze.py")
sc4 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sc4)

SCAN = "2026-11-24_parameter-sensitivity-1M"
SCALES_WITH_SALT, DOES_NOT = 2.0, 1.5  # README, reading rule 1


def rho(study: str, run: str, skip: float, end: float) -> float:
    return sc4.point(study, run, "T20C", skip, end)["rho"]


def ratio_verdict(r: float) -> str:
    if r >= SCALES_WITH_SALT:
        return "scales with the salt"
    return "does not scale with the salt" if r <= DOES_NOT else "partly"


def main(out_path: str) -> None:
    m3 = {n: rho(HERE.name, f"m1_3.0M_{n}", 1000.0, 3000.0) for n in ("zeta_0.65", "zeta_0.85", "epsEMC_x0.85")}
    m3["base"] = rho("2026-11-27_density-concentration-M1", "m1_3.0M", 1000.0, 3000.0)
    m1 = {n: rho(SCAN, n, 1500.0, 5000.0) for n in ("zeta_0.65", "zeta_0.85", "epsEMC_x0.85", "base_s1")}
    d3 = (m3["zeta_0.85"] - m3["zeta_0.65"]) / 0.20
    d1 = (m1["zeta_0.85"] - m1["zeta_0.65"]) / 0.20
    e3, e1 = m3["epsEMC_x0.85"] - m3["base"], m1["epsEMC_x0.85"] - m1["base_s1"]
    out = {"rho_3M": m3, "rho_1M_scan": m1, "drho_dzeta_3M": d3, "drho_dzeta_1M": d1, "ratio_zeta": d3 / d1,
           "verdict_zeta": ratio_verdict(d3 / d1), "eps_change_3M": e3, "eps_change_1M": e1, "ratio_eps": e3 / e1}  # fmt: skip
    Path(out_path).write_text(json.dumps(out, indent=1) + "\n")
    for k, v in out.items():
        print(k, v)


if __name__ == "__main__":
    main(sys.argv[1])
