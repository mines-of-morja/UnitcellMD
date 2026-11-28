"""Analysis of A1.7 target 2 (README.md; the criterion is fixed there): Gamma(m) against Mester 2015.

    HDF5_USE_FILE_LOCKING=FALSE PYTHONPATH=../../ucmd-analysis-tdf/src \
        ../../ucmd-analysis/.venv/bin/python analyze.py            (writes result.json)

ucmd-analysis at 1045065 (branch claude/3-thermodynamic-factor). Per run: TDF_molal (= Gamma) from
`thermodynamic_factor` with the ions as one species and water as the solvent, the first 2 ns left
out, 10 blocks; the volume per 500 water against Mester's SI Table IV.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SKIP_PS = 2000.0
STRIDE = 2  # every second frame (10 ps): the slowest mode relaxes in some 100 ps
N_BLOCKS = 10
K_MAX = 4.0  # nm⁻¹, the criterion's fit range
SCAN = ((3.0, "matrix"), (5.0, "matrix"), (4.0, "coulomb"), (4.0, "scalar"))
JUDGED = {"nacl_m1_w4000": "1", "nacl_m2_w4000": "2", "nacl_m3_w4000": "3"}
MOLALITY = {"nacl_m1_w4000": 1.0, "nacl_m2_w4000": 2.0, "nacl_m3_w4000": 3.0, "nacl_m3_w2000": 3.0}


def verdict(value: float, se: float, ref: float, ref_err: float, long_enough: bool) -> dict:
    """README criterion: |Gamma - Gamma_ref| <= 2 sqrt(SE^2 + sigma_ref^2), blocks >= 5 tau."""
    if not long_enough:
        return {"verdict": "not judged: blocks shorter than 5 relaxation times"}
    bound = 2.0 * math.hypot(se, ref_err)
    diff = value - ref
    return {"verdict": "pass" if abs(diff) <= bound else "FAIL", "difference": diff, "bound": bound}


def analyse_run(run_dir: Path, reference: dict, ledger_v: dict) -> dict:
    from ucmd_analysis.io import read_h5md
    from ucmd_analysis.thermodynamic_factor import thermodynamic_factor

    traj = read_h5md(run_dir / "out/trajectory.h5", stride=STRIDE)
    keep = int(np.searchsorted(traj.times_ps, SKIP_PS))
    traj = read_h5md(run_dir / "out/trajectory.h5", start=keep * STRIDE, stride=STRIDE)
    out: dict = {"frames": len(traj), "t_ps": [float(traj.times_ps[0]), float(traj.times_ps[-1])]}
    for k, form in ((K_MAX, "matrix"), *SCAN):
        key = f"{form}_k{k:g}"
        if key in out:
            continue
        try:
            r = thermodynamic_factor(traj, "Na", "Cl", k_max_nm=k, n_blocks=N_BLOCKS, form=form)
            out[key] = {"TDF_molal": r["TDF_molal"], "TDF_newman": r["TDF_newman"],
                        "nu_e_cm3_per_mol": r["nu_e_cm3_per_mol"], "_meta": r["_meta"]}  # fmt: skip
        except ValueError as e:  # a refusal is a result, recorded as such
            out[key] = {"refused": str(e)}
    primary = out[f"matrix_k{K_MAX:g}"]
    n_water = traj.system.species["water"].count
    n_salt = traj.system.species["Na"].count
    v = float(traj.volumes_nm3().mean())
    t = ledger_v["table_IV"]
    i = [k for k, (ns, nw) in enumerate(zip(t["N_NaCl"], t["N_water"], strict=True))
         if nw == 500 and ns * n_water == 500 * n_salt]  # fmt: skip
    out["volume_per_500_water_nm3"] = v * 500 / n_water
    if i:
        out["mester_V_nm3"] = t["V_nm3"][i[0]]
        out["volume_difference_pct"] = 100 * (out["volume_per_500_water_nm3"] / t["V_nm3"][i[0]] - 1)
    name = run_dir.parent.name
    if "refused" in primary:
        out["criterion"] = {"verdict": f"not judged: {primary['refused']}"}
    elif name in JUDGED:
        g = reference["gamma"][JUDGED[name]]
        tdf = primary["TDF_molal"]
        out["criterion"] = verdict(tdf["whole_run"], tdf["sem"], g["value"], g["uncertainty"], True)
        out["criterion"].update(value=tdf["whole_run"], se=tdf["sem"], reference=g["value"],
                                reference_err=g["uncertainty"])  # fmt: skip
    return out


def main() -> None:
    reference = json.loads((HERE / "reference.json").read_text())
    ledger = json.loads((HERE.parents[1] / "docs/research/summary/literature.json").read_text())
    ledger_v = ledger["entries"]["mester2015_jc_spce_lngamma"]["value"]
    result: dict = {"reference": reference["gamma"], "runs": {}}
    for name in MOLALITY:
        run = HERE / "runs" / name / "T25C"
        status = json.loads((run / "status.json").read_text()) if (run / "status.json").exists() else {}
        if status.get("state") != "done":
            result["runs"][name] = {"state": status.get("state", "missing")}
            continue
        result["runs"][name] = analyse_run(run, reference, ledger_v)
    judged = [r["criterion"]["verdict"] for n, r in result["runs"].items()
              if n in JUDGED and "criterion" in r]  # fmt: skip
    result["verdict"] = (
        "pass" if len(judged) == len(JUDGED) and all(v == "pass" for v in judged)
        else "FAIL" if any(v == "FAIL" for v in judged) else "incomplete"
    )  # fmt: skip
    (HERE / "result.json").write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps({n: r.get("criterion", r.get("state")) for n, r in result["runs"].items()}, indent=1))
    print("verdict:", result["verdict"])


if __name__ == "__main__":
    main()
