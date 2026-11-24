"""Sensitivity scan at 1 M: metrics per run and trends per knob (README: plan and reading rule).

    HDF5_USE_FILE_LOCKING=FALSE ucmd-analysis/.venv/bin/python \
        studies/2026-11-24_parameter-sensitivity-1M/analyze.py OUT.json

Finished runs only; unfinished ones are listed. The first 1.5 ns are skipped. Trend of a quantity
y: ln y = a + b ln x (least squares; the baselines enter as single points at x = 1), x = value /
baseline value. The noise of ln y is the standard deviation over the baselines of this study and
the three M1 runs of trial T2 (same protocol, older bridge), not the scatter about the line.
"""

from __future__ import annotations

import json
import math
import re
import statistics as st
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ANALYZE = ROOT / "ucmd-analysis/.venv/bin/ucmd-analyze"
T2 = ROOT / "studies/2026-11-21_trial-t2-ec-model-1M/runs"
SKIP_PS = "1500"
X0 = {"zeta": 0.75, "sigmaLi": 1.0, "epsEMC": 1.0}
PARTNERS = {"EC": "EC:O:1", "EMC": "EMC:O:1", "PF6": "PF6:P"}
TREND = ["kappa_NE", "D_Li", "D_PF6", "D_EC", "D_EMC", "density"]
MATTERS_LN, MATTERS_SE = 0.2, 2.0  # README, reading rule


def tool(*args: str) -> dict:
    out = subprocess.run([str(ANALYZE), *args], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def metrics(traj: Path) -> dict:
    skip = ["--skip-ps", SKIP_PS]
    tr = tool("transport", str(traj), "--temperature-K", "293.15", "--cation", "Li",
              "--anion", "PF6", *skip)  # fmt: skip
    m = {k: tr[f"D_{k[2:]}_m2_per_s"]["mean"] for k in ("D_Li", "D_PF6", "D_EC", "D_EMC")}
    m["kappa_NE"] = tr["kappa_NE_S_per_m"]["mean"]
    m["density"] = tool("density", str(traj), *skip)["density_g_cm3"]["mean"]
    for r_cut, tag in (("0.28", "028"), ("0.516", "0516")):
        cmd = ["shell", str(traj), *skip, "--a", "Li:Li"]
        for b in PARTNERS.values():
            cmd += ["--b", b]
        cmd += [a for _ in PARTNERS for a in ("--r-cut-nm", r_cut)]
        contacts = tool(*cmd)["mean_contacts"]
        m |= {f"n_{name}_{tag}": contacts[p] for name, p in PARTNERS.items()}
    for name in ("EC", "EMC"):
        g = tool("rdf", str(traj), "--a", "Li:Li", "--b", PARTNERS[name], *skip)
        m[f"r_LiO_{name}_nm"] = g["first_peak_nm"]
    return m


def trend(points: list[tuple[float, float]], sd_ln: float) -> dict:
    lx = np.log([p[0] for p in points])
    ly = np.log([p[1] for p in points])
    sxx = float(((lx - lx.mean()) ** 2).sum())
    b = float(((lx - lx.mean()) * (ly - ly.mean())).sum() / sxx)
    se, span = sd_ln / math.sqrt(sxx), float(lx.max() - lx.min())
    change = b * span
    return {"exponent": b, "exponent_se": se, "ln_change_over_range": change,
            "ln_change_se": se * span,
            "matters": abs(change) >= MATTERS_LN and abs(change) >= MATTERS_SE * se * span}  # fmt: skip


def main(out_path: str) -> None:
    runs, missing = {}, []
    for pkg in sorted((HERE / "packages").glob("*.ucsys")):
        run = HERE / "runs" / pkg.stem / "T20C"
        status = run / "status.json"
        if not status.exists() or json.loads(status.read_text()).get("state") != "done":
            missing.append(pkg.stem)
            continue
        knob, value = re.fullmatch(r"(base|zeta|sigmaLi|epsEMC)_(.+)", pkg.stem).groups()
        x = 1.0 if knob == "base" else float(value.lstrip("x")) / X0[knob]
        runs[pkg.stem] = {"knob": knob, "x": x, **metrics(run / "out/trajectory.h5")}
    old = {f"t2_m1_s{k}": metrics(T2 / f"t2_m1_s{k}/T20C/out/trajectory.h5") for k in (1, 2, 3)}
    base = [r for r in runs.values() if r["knob"] == "base"]
    result = {"runs": runs, "not_finished": missing, "t2_m1": old, "noise_sd_ln": {}, "trends": {}}
    for y in TREND:
        groups = [g for g in ([r[y] for r in base], [r[y] for r in old.values()]) if len(g) > 1]
        dof = sum(len(g) - 1 for g in groups)
        var = sum((len(g) - 1) * st.variance(map(math.log, g)) for g in groups) / dof  # pooled
        result["noise_sd_ln"][y] = math.sqrt(var)
    for knob in X0:
        pts = [r for r in runs.values() if r["knob"] in (knob, "base")]
        if len({r["x"] for r in pts}) < 3:
            continue
        result["trends"][knob] = {
            y: trend([(r["x"], r[y]) for r in pts], result["noise_sd_ln"][y]) for y in TREND
        }
    Path(out_path).write_text(json.dumps(result, indent=1) + "\n")
    print("not finished:", missing)
    for name, r in runs.items():
        print(f"{name:16s} kNE {r['kappa_NE']:.3f}  D_Li {r['D_Li'] * 1e11:.2f}  rho {r['density']:.4f}"
              f"  EC/EMC/PF6(0.28) {r['n_EC_028']:.2f}/{r['n_EMC_028']:.2f}/{r['n_PF6_028']:.3f}")  # fmt: skip
    for knob, t in result["trends"].items():
        for y in ("kappa_NE", "D_Li"):
            print(knob, y, {k: round(v, 3) if not isinstance(v, bool) else v for k, v in t[y].items()})


if __name__ == "__main__":
    main(sys.argv[1])
