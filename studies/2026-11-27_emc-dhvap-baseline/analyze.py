"""Enthalpy of vaporization of the current EMC model at 25 C (README). Run with ucmd-analysis's venv (constants).

    ucmd-analysis/.venv/bin/python analyze.py OUT.json

dH_vap = <U_gas> - <U_liq>/N + RT (the EC test's and Caleman 2012's definition). <U_gas>: the three gas runs,
first 0.5 ns skipped. <U_liq>: SC-1's EMC liquids (500 molecules, 25 C, NPT), the window of SC-1 (0.5-2 ns), at
1 fs (the protocol of ADR 0017) and, for the record, at 0.5 fs. Errors: the spread of the three seeds.
"""

from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

from ucmd_analysis.constants import GAS_CONSTANT_KJ_PER_MOL_K

HERE = Path(__file__).resolve().parent
STUDIES = HERE.parent
T_K = 298.15
N_LIQ = 500
GAS_SKIP_PS, GAS_END_PS = 500.0, 10000.0
LIQ = {"1": "2026-11-25_timestep-emc-1fs", "0.5": "2026-11-25_timestep-emc-0p5fs"}
LIQ_SKIP_PS, LIQ_END_PS = 500.0, 2000.0
SEEDS = (1, 2, 3)


def mean_potential(thermo: Path, skip_ps: float, end_ps: float) -> float:
    """kJ/mol, mean of potential_kjmol after skip_ps; a restarted run may repeat rows (the last one wins)."""
    rows: dict[int, tuple[float, float]] = {}
    with thermo.open() as fh:
        names = fh.readline().lstrip("# ").strip().split("\t")
        step, time, pot = (names.index(n) for n in ("step", "time_ps", "potential_kjmol"))
        for line in fh:
            f = line.split("\t")
            rows[int(f[step])] = (float(f[time]), float(f[pot]))
    ordered = [rows[k] for k in sorted(rows)]
    if not ordered or ordered[-1][0] < end_ps - 1e-3:
        raise SystemExit(f"{thermo}: not finished")
    u = [x for t, x in ordered if skip_ps < t <= end_ps + 1e-9]
    if not u or not all(map(math.isfinite, u)):
        raise SystemExit(f"{thermo}: no finite energies")
    return statistics.fmean(u)


def mean_se(xs: list[float]) -> tuple[float, float]:
    return statistics.fmean(xs), statistics.stdev(xs) / math.sqrt(len(xs))


def dh_vap(u_gas: float, u_liq_total: float, n: int, t_k: float) -> float:
    """kJ/mol."""
    return u_gas - u_liq_total / n + GAS_CONSTANT_KJ_PER_MOL_K * t_k


def main(out_path: str) -> None:
    gas = [mean_potential(HERE / f"runs/emc_gas_s{s}/T25C/out/thermo.tsv", GAS_SKIP_PS, GAS_END_PS) for s in SEEDS]
    g, g_se = mean_se(gas)
    out: dict = {"u_gas_kjmol": gas, "u_gas_mean": g, "u_gas_se": g_se}
    for arm, study in LIQ.items():
        liq = [
            mean_potential(STUDIES / study / f"runs/emc_500_s{s}/T25C/out/thermo.tsv", LIQ_SKIP_PS, LIQ_END_PS) / N_LIQ
            for s in SEEDS
        ]
        m, se = mean_se(liq)
        out[f"liquid_{arm}fs"] = {
            "u_liq_per_molecule_kjmol": liq,
            "dh_vap_kjmol": dh_vap(g, m * N_LIQ, N_LIQ, T_K),
            "se_kjmol": math.hypot(se, g_se),
        }
    Path(out_path).write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
