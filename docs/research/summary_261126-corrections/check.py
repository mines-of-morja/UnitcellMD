"""Recompute the numbers of Jo's feedback (27 November) on the summary of 26 November from our own data.

    ucmd-analysis/.venv/bin/python docs/research/summary_261126-corrections/check.py

Writes check.json next to this file. Sources are the ones build.py of summary_261126 reads, plus the box
volumes from the thermo tables (local run folders) and SC-1's configurational temperatures. Jo worked from
the PDF only; here the real box edges and the stored V_phi values replace Jo's assumptions. No physical
parameter is chosen here. The viscosities are a scan range (Jo's table), not values of the model, which is
unknown until V-1 / V-2 report.
"""

from __future__ import annotations

import itertools
import json
import math
import statistics as st
import subprocess
from pathlib import Path

from ucmd_analysis import constants as c

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
R = ROOT / "docs/research"
SC1_REF = "9eda5bd"  # as in summary_261126/build.py
ETA_RANGE_MPA_S = (10.0, 7.0, 5.0, 3.5)  # Jo's table, section 1 (a range, not a model value)
EA_RANGE_KJ_MOL = (16.0, 25.0)  # Jo's section 2 (activation energies used there)
T_K = 293.15
out: dict = {}


def git_show(ref: str, path: str) -> str:
    cmd = ["git", "-C", str(ROOT), "show", f"{ref}:{path}"]
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def mean_se(xs: list[float]) -> tuple[float, float]:
    return st.fmean(xs), (st.stdev(xs) / math.sqrt(len(xs)) if len(xs) > 1 else float("nan"))


def box_edge_nm(thermo: Path) -> float:
    """Cube root of the mean volume over the second half of the table (NVT: the fixed volume)."""
    cols, vols = None, []
    for line in thermo.read_text().splitlines():
        if line.startswith("#"):
            cols = line[1:].split()
            continue
        vols.append(float(line.split("\t")[cols.index("volume_nm3")]))
    return st.fmean(vols[len(vols) // 2 :]) ** (1 / 3)


def yeh_hummer_m2_s(eta_mpa_s: float, edge_nm: float) -> float:
    """ΔD = k_B T ξ / (6π η L), the same for every species."""
    return (c.BOLTZMANN_J_PER_K * T_K * c.YEH_HUMMER_XI_CUBIC
            / (6 * math.pi * eta_mpa_s * 1e-3 * edge_nm * c.NM_IN_M))  # fmt: skip


# ------------------------------------------------------------------ inputs (as in build.py)
t2 = json.loads((R / "trials/T2/t2_result.json").read_text())
scan = json.loads((R / "summary_261125/data/scan.json").read_text())
pilot_dir = ROOT / "studies/2026-11-19_transport-pilot/runs/ec-emc_3-7w_1.0M/T20C"
tr = json.loads((pilot_dir / "transport.repaired.json").read_text())
sc1 = json.loads(git_show(SC1_REF, "docs/research/timestep/sc1.json"))
tconf = json.loads((R / "timestep/tconf/summary.json").read_text())
LIT = json.loads((R / "summary/literature.json").read_text())["entries"]
lf = LIT["landesfeind2019_density_fit_ec_emc_3_7"]["value"]

# ------------------------------------------------------------------ 1. box edges and Yeh-Hummer (Jo section 1)
T2_RUNS = ROOT / "studies/2026-11-21_trial-t2-ec-model-1M/runs"
SCAN_RUNS = ROOT / "studies/2026-11-24_parameter-sensitivity-1M/runs"
edges = {"pilot M0 (NVT)": box_edge_nm(pilot_dir / "out/thermo.tsv")}
for name in ("t2_m1_s1", "t2_m1_s2", "t2_m1_s3"):
    edges[f"T2 {name}"] = box_edge_nm(T2_RUNS / name / "T20C/out/thermo.tsv")
for name in ("base_s1", "base_s2", "base_s3", "epsEMC_x0.85"):
    edges[f"scan {name}"] = box_edge_nm(SCAN_RUNS / name / "T20C/out/thermo.tsv")
out["box_edge_nm"] = edges

# kappa_NE is linear in D_Li + D_PF6 at fixed c, so the corrected value is kappa_NE * (sum + 2 dD) / sum.
sets = {
    "pilot M0": ([tr["D_Li_m2_per_s"]["mean"]], [tr["D_PF6_m2_per_s"]["mean"]],
                 [tr["kappa_NE_S_per_m"]["mean"]], [edges["pilot M0 (NVT)"]]),
    "T2 M1": tuple(zip(*[(r["reported_only"]["D_Li_m2_per_s"]["mean"], r["reported_only"]["D_PF6_m2_per_s"]["mean"],
                          r["reported_only"]["kappa_NE_S_per_m"]["mean"], edges[f"T2 {k}"])
                         for k, r in t2["runs"].items() if r["model"] == "M1"], strict=True)),
    "scan M1 baselines": tuple(zip(*[(r["D_Li"], r["D_PF6"], r["kappa_NE"], edges[f"scan {k}"])
                                     for k, r in scan["runs"].items() if r["knob"] == "base"], strict=True)),
    "probe epsEMC x0.85": ([scan["runs"]["epsEMC_x0.85"]["D_Li"]], [scan["runs"]["epsEMC_x0.85"]["D_PF6"]],
                           [scan["runs"]["epsEMC_x0.85"]["kappa_NE"]], [edges["scan epsEMC_x0.85"]]),
}  # fmt: skip
p = LIT["landesfeind2019_kappa_eq15_ec_emc"]["value"]
e = math.exp(1000.0 / T_K)
k_exp = p["p1"] * (1 + T_K - p["p2"]) * (1 + p["p3"] + p["p4"] * (1 + p["p5"] * e)) / (1 + p["p6"] * e) / 10
fs = {"kappa_exp_S_m": k_exp, "eta_range_mPa_s": ETA_RANGE_MPA_S, "rows": {}}
for label, (dli, dpf, kne, L) in sets.items():
    row = {"runs": len(kne), "kappa_NE_uncorrected": mean_se(list(kne))}
    for eta in ETA_RANGE_MPA_S:
        corr = [k * (a + b + 2 * yeh_hummer_m2_s(eta, edge)) / (a + b)
                for a, b, k, edge in zip(dli, dpf, kne, L, strict=True)]  # fmt: skip
        row[f"eta_{eta:g}"] = {
            "dD_1e-11_m2_s": 1e11 * yeh_hummer_m2_s(eta, st.fmean(L)),
            "kappa_NE": mean_se(corr),
            "fraction_of_measured": st.fmean(corr) / k_exp,
        }
    fs["rows"][label] = row
# the pilot's kappa / kappa_NE with the corrected kappa_NE (Onsager kappa taken as box-independent, Jo's premise)
kap, kap_se = tr["kappa_S_per_m"]["mean"], tr["kappa_S_per_m"]["sem"]
fs["pilot_kappa_over_kappaNE"] = {"uncorrected": kap / tr["kappa_NE_S_per_m"]["mean"]}
for eta in ETA_RANGE_MPA_S:
    kne = fs["rows"]["pilot M0"][f"eta_{eta:g}"]["kappa_NE"][0]
    fs["pilot_kappa_over_kappaNE"][f"eta_{eta:g}"] = (kap / kne, kap_se / kne)
out["finite_size"] = fs

# ------------------------------------------------------------------ 2. time step and the warm liquid (Jo section 2)
sc4 = json.loads((R / "density-c-T/sc4.json").read_text())
drho_dT_1M = sc4["drho_dT"]["value"]  # model M1, g cm-3 K-1
rep = json.loads((R / "report/data.json").read_text())["solvent_densities"]
drho_dT_emc = (rep["emc_40_on"]["rho"] - rep["emc_25_on"]["rho"]) / 15.0  # model M0 EMC, 25 -> 40 C
ts = {}
for key, drho_dT, rho, sc1key in (("1M", drho_dT_1M, sc1["density"]["1M"]["runs"]["0.5"], "1M"),
                                   ("emc", drho_dT_emc, None, "EMC")):  # fmt: skip
    a, b = tconf[f"{key}_1fs"], tconf[f"{key}_0p5fs"]
    dT = a["excess_K"] - b["excess_K"]
    dT_se = math.hypot(a["seed_se_K"], b["seed_se_K"])
    rho_ref = st.fmean(r["rho"] for r in rho) if rho else rep["emc_25_on"]["rho"]
    pred = -100 * drho_dT * dT / rho_ref  # cooler by dT at 0.5 fs -> denser
    ts[key] = {
        "Tconf_excess_1fs_K": (a["excess_K"], a["seed_se_K"]),
        "Tconf_excess_0p5fs_K": (b["excess_K"], b["seed_se_K"]),
        "dt2_prediction_0p5fs_K": a["excess_K"] / 4,
        "dT_1fs_minus_0p5fs_K": (dT, dT_se),
        "density_shift_predicted_pct": (pred, abs(pred) * dT_se / abs(dT)),
        "density_shift_measured_pct": (sc1["density"][sc1key]["diff_pct"], sc1["density"][sc1key]["se_pct"]),
    }
    if key == "1M":
        ts[key]["D_shift_predicted_pct"] = {
            f"Ea_{ea:g}": 100 * (math.exp(-ea / c.GAS_CONSTANT_KJ_PER_MOL_K * dT / T_K**2) - 1)
            for ea in EA_RANGE_KJ_MOL
        }
        ts[key]["D_shift_measured_pct"] = {k: 100 * (math.exp(v["diff"]) - 1) for k, v in sc1["D"]["1M"].items()}
out["timestep"] = ts

# ------------------------------------------------------------------ 5. small things
vz = json.loads((R / "density-c-T/v_phi_zeta.json").read_text())
av = json.loads((R / "density-c-T/apparent_volume.json").read_text())
v_exp, slope = vz["experiment_v_phi_cm3_mol"], vz["1M"]["dv_phi_dzeta_cm3_mol"]
v_used = vz["1M"]["runs"]["0.75"]  # what build.py used for zeta*
v_sc4 = av["model"]["points"]["1 M, 20 C"]  # what the summary prints as V_phi at 1 M
out["zeta_star_1M"] = {
    "build_py_uses": {"v_phi": v_used["v_phi_cm3_mol"], "rho": v_used["rho"],
                      "source": "density-slope-3M map, 1 M, 1 fs",
                      "zeta_star": 0.75 + (v_exp - v_used["v_phi_cm3_mol"]) / slope},
    "summary_prints": {"v_phi": v_sc4["v_phi_cm3_mol"], "rho": v_sc4["rho"], "source": "SC-4, 0.5 fs",
                       "zeta_star": 0.75 + (v_exp - v_sc4["v_phi_cm3_mol"]) / slope},
}  # fmt: skip


def crossing(pts: list[tuple[float, float]]) -> float | None:
    """First c where the deviation changes sign, linear between neighbours."""
    for (c1, d1), (c2, d2) in itertools.pairwise(pts):
        if d1 > 0 >= d2:
            return c1 + d1 * (c2 - c1) / (d1 - d2)
    return None


own = sorted((q["c_mol_l"], q["dev_pct"]) for k, q in sc4["points"].items() if k.endswith("20 C"))
aw = LIT["iupac_atomic_weights"]["value"]
M_ = {"EC": 3 * aw["C"] + 4 * aw["H"] + 3 * aw["O"], "EMC": 4 * aw["C"] + 8 * aw["H"] + 3 * aw["O"],
      "Li": aw["Li"], "PF6": aw["P"] + 6 * aw["F"]}  # fmt: skip
t1s = LIT["lehnert2025_table_s1_ec_emc"]["value"]
leh = []
for i, cc in enumerate(t1s["c_M"]):
    rho = sum(t1s[s][i] * M_[s] for s in M_) * cc / (1000 * t1s["Li"][i])
    leh.append((cc, 100 * (rho / (lf["p1"] + lf["p2"] * cc + lf["p3"] * T_K) - 1)))
# Jo 3c / item (a): Lehnert SI S1.2 tuned the ion numbers by simulation at 20 C until c matched the target, so the
# implied density is their model's own, up to the integer step. With the nearest count, |c_true/c_target - 1| <=
# 1/(2 N_pairs), and rho_implied/rho_true = c_target/c_true; one full pair (1/N) is the bound if "most consistent"
# was not the nearest.
leh_err = []
for i, cc in enumerate(t1s["c_M"]):
    n = t1s["Li"][i]
    leh_err.append({"c_M": cc, "pairs": n, "dev_pct": leh[i][1],
                    "half_step_pct": 100 / (2 * n), "one_pair_pct": 100 / n})  # fmt: skip
rho_leh = [(cc, sum(t1s[s][i] * M_[s] for s in M_) * cc / (1000 * t1s["Li"][i])) for i, cc in enumerate(t1s["c_M"])]
w = [1 / (r * e["half_step_pct"] / 100) ** 2 for (_, r), e in zip(rho_leh, leh_err, strict=True)]
xm = sum(wi * x for wi, (x, _) in zip(w, rho_leh, strict=True)) / sum(w)
ym = sum(wi * y for wi, (_, y) in zip(w, rho_leh, strict=True)) / sum(w)
sxx = sum(wi * (x - xm) ** 2 for wi, (x, _) in zip(w, rho_leh, strict=True))
slope_w = sum(wi * (x - xm) * (y - ym) for wi, (x, y) in zip(w, rho_leh, strict=True)) / sxx
out["lehnert_implied"] = {"points": leh_err, "slope_weighted_g_cm3_M": (slope_w, 1 / math.sqrt(sxx)),
                          "slope_experiment_g_cm3_M": lf["p2"]}  # fmt: skip
out["fig3_crossings_M"] = {"M1 (SC-4)": crossing(own), "Lehnert boxes, implied": crossing(sorted(leh)),
                           "M1 points": own, "Lehnert points": sorted(leh)}  # fmt: skip

(HERE / "check.json").write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out, indent=1))
