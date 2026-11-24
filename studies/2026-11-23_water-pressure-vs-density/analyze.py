"""Pressure against density for SPC/Fw water (NVT): the numbers and the pre-registered verdict.

    analyze.py [RUNS_DIR] [OUT.json]

RUNS_DIR holds spcfw_512_rho*/T25.01C/out/thermo.tsv (default: runs/; the data of the first scan,
made with the drifting bridge, are in logs/unfixed-bridge/runs). Mean pressure over 0.5-2 ns
with errors from 5 blocks; a drift test (slope of the block means against time); the slope of
P against density with its compressibility; the criteria of README.md, applied only if no run
drifts.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

DENSITY = {"spcfw_512_rho1000": 1.000, "spcfw_512_rho10072": 1.0072, "spcfw_512_rho1012": 1.012}
SKIP_PS, BLOCKS = 500.0, 5
ONE_ATM_BAR = 1.01325


def pressure_series(thermo: Path) -> tuple[np.ndarray, np.ndarray]:
    rows = np.loadtxt(thermo, comments="#")
    t, p = rows[:, 1], rows[:, 7]
    keep = np.isfinite(p) & (t >= SKIP_PS)
    return t[keep], p[keep]


def blocks(t: np.ndarray, p: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    idx = np.array_split(np.arange(len(p)), BLOCKS)
    return np.array([t[i].mean() for i in idx]), np.array([p[i].mean() for i in idx])


def sem(x: np.ndarray) -> float:
    return float(np.std(x, ddof=1) / np.sqrt(len(x)))


def main(runs: Path, out: Path | None) -> dict:
    per_run = {}
    for name, rho in DENSITY.items():
        t, p = pressure_series(runs / name / "T25.01C" / "out" / "thermo.tsv")
        bt, bp = blocks(t, p)
        slope, intercept = np.polyfit(bt, bp, 1)  # bar/ps over the block means
        resid = bp - (slope * bt + intercept)
        slope_err = float(np.sqrt((resid**2).sum() / (BLOCKS - 2) / ((bt - bt.mean()) ** 2).sum()))
        per_run[name] = {
            "rho_g_cm3": rho,
            "n_samples": len(p),
            "window_ps": [float(t[0]), float(t[-1])],
            "P_mean_bar": float(p.mean()),
            "P_err_bar": sem(bp),
            "block_means_bar": bp.tolist(),
            "drift_bar_per_ns": 1000.0 * float(slope),
            "drift_err_bar_per_ns": 1000.0 * slope_err,
            "drift_significant": bool(abs(slope) > 3.0 * slope_err),
        }
    names = list(DENSITY)
    rho = np.array([DENSITY[n] for n in names])
    mean = np.array([per_run[n]["P_mean_bar"] for n in names])
    blocks_by_run = np.array([per_run[n]["block_means_bar"] for n in names])  # (3, 5)
    slopes = np.array([np.polyfit(rho, blocks_by_run[:, b], 1)[0] for b in range(BLOCKS)])
    dpdrho, dpdrho_err = float(np.polyfit(rho, mean, 1)[0]), sem(slopes)  # bar per (g/cm3)
    kappa = 1.0 / (rho.mean() * dpdrho) if dpdrho > 0 else float("nan")
    p_npt = per_run["spcfw_512_rho10072"]["P_mean_bar"]
    drifting = any(per_run[n]["drift_significant"] for n in names)
    near = abs(p_npt - ONE_ATM_BAR) <= 30.0
    kappa_ok = 3.5e-5 <= kappa <= 6.0e-5
    if drifting:
        verdict = (
            "not applied: the pressure drifts in at least one run (the estimator is not sound)"
        )
    elif near and kappa_ok:
        verdict = "criterion 1: consistent"
    elif not near:
        verdict = "criterion 2: inconsistent (P at the NPT density is outside +-30 bar of 1 atm)"
    else:
        verdict = (
            "criterion 3: unresolved (P near 1 atm, compressibility outside 3.5e-5..6e-5 /bar)"
        )
    result = {
        "runs": per_run,
        "dP_drho_bar_per_g_cm3": dpdrho,
        "dP_drho_err": dpdrho_err,
        "kappa_T_per_bar": kappa,
        "P_at_NPT_density_bar": p_npt,
        "verdict": verdict,
    }
    for n in names:
        r = per_run[n]
        print(
            f"{n:20s} rho {r['rho_g_cm3']:.4f}  P = {r['P_mean_bar']:8.1f} +- {r['P_err_bar']:5.1f} bar"
            f"   drift {r['drift_bar_per_ns']:7.1f} +- {r['drift_err_bar_per_ns']:5.1f} bar/ns"
            f"{'  <-- DRIFT' if r['drift_significant'] else ''}"
        )
    print(f"dP/drho = {dpdrho:.0f} +- {dpdrho_err:.0f} bar/(g/cm3), kappa_T = {kappa:.2e} /bar")
    print("verdict:", verdict)
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    main(
        Path(sys.argv[1] if len(sys.argv) > 1 else "runs"),
        Path(sys.argv[2]) if len(sys.argv) > 2 else None,
    )
