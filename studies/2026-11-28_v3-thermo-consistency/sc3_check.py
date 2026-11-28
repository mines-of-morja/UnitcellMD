"""SC-3's three water arms against V-3's prediction (prediction.json, committed in 9b22a5d before the result was read).

    python3 studies/2026-11-28_v3-thermo-consistency/sc3_check.py [OUT.json]

Reads the arms with SC-3's own analyze.py (imported, not changed); the error of a difference is SC-3's: s^2 pooled
over the three arms (6 degrees of freedom), SE = sqrt(2 s^2 / 3).
"""

from __future__ import annotations

import importlib.util
import json
import math
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDIES = HERE.parent
spec = importlib.util.spec_from_file_location("sc3", STUDIES / "2026-11-25_water-npt-cpu-molecular/analyze.py")
sc3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sc3)


def main() -> None:
    pred = json.loads((HERE / "prediction.json").read_text())
    arms = {}
    for arm, name in sc3.ARMS.items():
        study = STUDIES / name
        arms[arm] = [
            sc3.run_summary(study / "runs" / s / "T25.01C", study / "systems" / s / "built.ucsys") for s in sc3.SEEDS
        ]
    rho = {a: [r["rho"] for r in runs] for a, runs in arms.items()}
    s2 = st.fmean(st.variance(v) for v in rho.values())
    se = math.sqrt(2 * s2 / 3)
    ref = st.fmean(rho["B"])
    wp = pred["water_arms_prediction"]
    out = {"se_of_a_difference_g_cm3": se, "t95_6dof": sc3.T95_6}
    for arm, key in (("A", "rho_cpu_atomic_minus_cpu_molecular_pct"), ("G", "rho_gpu_mc_minus_cpu_molecular_pct")):
        d = st.fmean(rho[arm]) - ref
        p = wp[key] / 100 * ref
        out[f"rho_{arm}_minus_rho_B"] = {
            "measured_g_cm3": d,
            "predicted_g_cm3": p,
            "measured_minus_predicted_in_se": (d - p) / se,
            "consistent_95": abs(d - p) <= sc3.T95_6 * se,
        }
    # the GPU arm's molecular pressure against P0 + rho_mol k (T* - T0)
    pg = [r["pressure"] for r in arms["G"]]
    out["gpu_molecular_pressure_bar"] = {
        "measured": st.fmean(pg),
        "se_3_seeds": st.stdev(pg) / math.sqrt(3),
        "predicted": sc3.TARGET_BAR + pred["water"]["1fs"]["P_true_minus_P0_bar (MC barostat, NHC)"],
    }
    text = json.dumps(out, indent=1)
    print(text)
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(text + "\n")


if __name__ == "__main__":
    main()
