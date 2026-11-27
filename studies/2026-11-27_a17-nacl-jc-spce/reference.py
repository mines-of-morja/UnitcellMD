"""The reference of A1.7 target 2 (README.md): Gamma(m) = 1 + d ln(gamma)/d ln(m) of JC/SPC/E NaCl.

    python3 reference.py [OUT.json]     (numpy; writes reference.json next to this file by default)

From the literature ledger entry mester2015_jc_spce_lngamma (Mester & Panagiotopoulos 2015):
- central value: the derivative of their own fit (Eq. 3 with SI Table XIII, "this work");
- uncertainty: refit b, C, D of Eq. 3 (A and B as printed) to SI Table IV with each ln(gamma)
  drawn from its printed error, the spread of Gamma over 20000 draws, multiplied by the Birge ratio
  sqrt(chi2/dof) of the refit, because Eq. 3 does not fit Table IV within its errors.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
LEDGER = HERE.parents[1] / "docs/research/summary/literature.json"
LN10 = float(np.log(10.0))
MOLALITIES = (1.0, 2.0, 3.0)
DRAWS, SEED = 20000, 20150128


def bracket(m, a, b_, b, c, d):
    """The term in parentheses of Eq. 3: ln(gamma) = ln(10) * bracket."""
    s = np.sqrt(m)
    return -a * s / (1 + b_ * s) + b * m + c * m**2 + d * m**3


def gamma_factor(m, a, b_, b, c, d) -> float:
    """1 + m d ln(gamma)/dm of Eq. 3."""
    s = np.sqrt(m)
    slope = -a / (2 * s * (1 + b_ * s) ** 2) + b + 2 * c * m + 3 * d * m**2
    return float(1 + LN10 * m * slope)


def reference() -> dict:
    entry = json.loads(LEDGER.read_text(encoding="utf-8"))["entries"]["mester2015_jc_spce_lngamma"]
    t, fit = entry["value"]["table_IV"], entry["value"]["table_XIII_this_work"]
    m = np.array(t["m_mol_per_kg"])
    y, err = np.array(t["ln_gamma"]), np.array(t["ln_gamma_err"])
    a, b_ = fit["A"], fit["B"]
    printed = (fit["b"], fit["C"], fit["D"])
    # linear in b, C, D once the A, B term is moved to the left side
    x = LN10 * np.stack([m, m**2, m**3], axis=1)
    rhs = y - LN10 * bracket(m, a, b_, 0.0, 0.0, 0.0)
    w = 1.0 / err

    def refit(target: np.ndarray) -> np.ndarray:
        return np.linalg.lstsq(x * w[:, None], target * w, rcond=None)[0]

    best = refit(rhs)
    chi2 = float(np.sum(((x @ best - rhs) / err) ** 2))
    dof = len(m) - 3
    birge = float(np.sqrt(chi2 / dof))
    rng = np.random.default_rng(SEED)
    draws = np.array([
        [gamma_factor(mm, a, b_, *refit(rhs + rng.normal(0.0, err))) for mm in MOLALITIES]
        for _ in range(DRAWS)
    ])  # fmt: skip
    out = {
        "source": entry["source"], "doi": entry["doi"],
        "definition": "Gamma = 1 + d ln(gamma)/d ln(m), molality scale (TDF_molal of ucmd-analysis)",
        "printed_fit": dict(zip(("A", "B", "b", "C", "D"), (a, b_, *printed), strict=True)),
        "refit_bCD": best.tolist(), "chi2_per_dof": chi2 / dof, "birge_ratio": birge,
        "printed_fit_vs_table_IV": [float(LN10 * bracket(mm, a, b_, *printed)) for mm in m],
        "gamma": {},
    }  # fmt: skip
    for i, mm in enumerate(MOLALITIES):
        out["gamma"][f"{mm:g}"] = {
            "value": gamma_factor(mm, a, b_, *printed),
            "refit": gamma_factor(mm, a, b_, *best),
            "sd_draws": float(draws[:, i].std(ddof=1)),
            "uncertainty": float(draws[:, i].std(ddof=1) * birge),
        }
    return out


def main() -> None:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "reference.json"
    ref = reference()
    target.write_text(json.dumps(ref, indent=1) + "\n")
    for mm, g in ref["gamma"].items():
        print(f"m = {mm} mol/kg: Gamma = {g['value']:.3f} ± {g['uncertainty']:.3f} (refit {g['refit']:.3f})")
    print(f"chi2/dof of the refit {ref['chi2_per_dof']:.2f}")


if __name__ == "__main__":
    main()
