"""Enthalpy of vaporization of the LigParGen DMC model at 25 C, the calibration of SC-7 step 0 (README).

    ucmd-analysis/.venv/bin/python studies/2026-11-27_dmc-dhvap-calibration/analyze.py OUT.json

Same definition and code as the EMC baseline (dH_vap = <U_gas> - <U_liq>/N + RT; its functions are imported).
<U_gas>: three gas runs, first 0.5 ns skipped. <U_liq>: the 2026-11-17 DMC liquid at 25 C (500 molecules, 1 fs, one
run of 0.5 ns), the window of that study (0.25-0.5 ns); its error from the two halves of the window.
The reading (README) compares DMC's excess over its reference with EMC's excess over its working range.
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDIES = HERE.parent
_spec = importlib.util.spec_from_file_location("emc_dh", STUDIES / "2026-11-27_emc-dhvap-baseline/analyze.py")
emc_dh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(emc_dh)

T_K = 298.15
N_LIQ = 500
LIQ_THERMO = STUDIES / "2026-11-17_solvent-densities-tail-on/runs/dmc_pure/T25C/out/thermo.tsv"
LIQ_SKIP_PS, LIQ_END_PS = 250.0, 500.0
GAS_SKIP_PS, GAS_END_PS = 500.0, 10000.0
SEEDS = (1, 2, 3)
DMC_REFERENCE = 38.0  # kJ/mol, NIST WebBook table, 298 K (README; primary papers not read, not in the ledger)
EMC_RESULT = HERE.parents[1] / "docs/research/emc-literature/dhvap_baseline.json"
EMC_WORKING = 40.5  # kJ/mol, middle of the 40-41 working range (SC-7 design, Q1 open)


def reading(r: float) -> str:
    """The README's rule on r = DMC excess / EMC excess."""
    if r >= 0.6:
        return "shared by the carbonate types"
    if r <= 0.3:
        return "mainly EMC's own"
    return "partly shared"


def main(out_path: str) -> None:
    gas = [
        emc_dh.mean_potential(HERE / f"runs/dmc_gas_s{s}/T25C/out/thermo.tsv", GAS_SKIP_PS, GAS_END_PS) for s in SEEDS
    ]
    g, g_se = emc_dh.mean_se(gas)
    mid = 0.5 * (LIQ_SKIP_PS + LIQ_END_PS)
    halves = [
        emc_dh.mean_potential(LIQ_THERMO, LIQ_SKIP_PS, mid) / N_LIQ,
        emc_dh.mean_potential(LIQ_THERMO, mid, LIQ_END_PS) / N_LIQ,
    ]
    liq = emc_dh.mean_potential(LIQ_THERMO, LIQ_SKIP_PS, LIQ_END_PS) / N_LIQ
    liq_se = abs(halves[0] - halves[1]) / 2
    dh = emc_dh.dh_vap(g, liq * N_LIQ, N_LIQ, T_K)
    emc = json.loads(EMC_RESULT.read_text())["liquid_1fs"]["dh_vap_kjmol"]
    r = (dh - DMC_REFERENCE) / (emc - EMC_WORKING)
    out = {
        "u_gas_kjmol": gas,
        "u_gas_mean": g,
        "u_gas_se": g_se,
        "u_liq_per_molecule_kjmol": liq,
        "u_liq_halves": halves,
        "dh_vap_kjmol": dh,
        "se_kjmol": math.hypot(g_se, liq_se),
        "dmc_reference_kjmol": DMC_REFERENCE,
        "dmc_excess_kjmol": dh - DMC_REFERENCE,
        "emc_dh_vap_kjmol": emc,
        "emc_excess_kjmol": emc - EMC_WORKING,
        "ratio": r,
        "reading": reading(r),
    }
    Path(out_path).write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
