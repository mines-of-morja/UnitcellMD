"""Build the results summary of 2026-11-23 (out1/summary.pdf in this folder).

    HDF5_USE_FILE_LOCKING=FALSE ucmd-analysis/.venv/bin/python docs/research/summary_261123/build.py

Dated successor of docs/research/summary (2026-11-21), which stays unchanged. Every number comes
from one of four places, never typed into the text (docs/research/publication.md, rule 6):
- the study data in studies/ (local, not in git), analysed here with ucmd-analyze;
- the committed outputs of the trials and results (T1, T2, T6, wu2006-spcfw-water, tools/qm);
- the literature ledgers (docs/research/summary/literature.json and the Wu 2006 ledger);
- quoted.json, numbers stated in our own reports, checked verbatim against a pinned commit.
Runs that are missing or unfinished are left out and the text says how many were used.
"""

from __future__ import annotations

import io
import json
import math
import shutil
import statistics
import subprocess
import sys
from datetime import date
from pathlib import Path
from string import Template

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
STUDIES = ROOT / "studies"
RESEARCH = ROOT / "docs/research"
WU = RESEARCH / "results/wu2006-spcfw-water"
OUT = HERE / "out1"
ANALYZE = ROOT / "ucmd-analysis" / ".venv" / "bin" / "ucmd-analyze"
LIT = json.loads((RESEARCH / "summary/literature.json").read_text(encoding="utf-8"))["entries"]
QUOTES = json.loads((HERE / "quoted.json").read_text(encoding="utf-8"))["quotes"]

# palette: dataviz reference instance, light mode, validated (blue, orange, aqua)
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, MUTED, GRID = "#1f1f1e", "#6b6a63", "#e4e3de"

v: dict[str, str] = {}  # template values
pending: list[str] = []


# ---------------------------------------------------------------- sources


def quoted(key: str) -> str:
    q = QUOTES[key]
    if q["value"] not in q["context"]:
        sys.exit(f"quoted.json {key}: value not in its context")
    repo = ROOT / q["repo"]
    text = subprocess.run(
        ["git", "-C", str(repo), "show", f"{q['ref']}:{q['path']}"],
        capture_output=True, text=True, check=True,
    ).stdout  # fmt: skip
    if q["context"] not in text:
        sys.exit(f"quoted.json {key}: context not found in {q['repo']}/{q['path']} at {q['ref']}")
    return q["value"]


def shell(traj: Path, partners: list[str], r_cut_nm: float, skip_ps: float = 1000.0) -> dict:
    cmd = [str(ANALYZE), "shell", str(traj), "--skip-ps", str(skip_ps), "--a", "Li:Li"]
    for b in partners:
        cmd += ["--b", b]
    for _ in partners:
        cmd += ["--r-cut-nm", str(r_cut_nm)]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    return json.loads(out)["mean_contacts"]


def finished(run: Path, t_ps: float) -> bool:
    st = run / "status.json"
    if not st.is_file():
        return False
    s = json.loads(st.read_text())
    return s.get("state") == "done" and s.get("summary", {}).get("last_time_ps", 0) >= t_ps - 1


def mean_sem(x: list[float]) -> tuple[float, float]:
    m = statistics.fmean(x)
    return m, (statistics.stdev(x) / math.sqrt(len(x)) if len(x) > 1 else float("nan"))


def f(x: float, nd: int = 2) -> str:
    return f"{x:.{nd}f}".replace("-", "−")


def sf(x: float, nd: int = 1) -> str:
    """Signed: a difference that can have either sign."""
    return ("+" if x > 0 else "") + f(x, nd)


def pm(m: float, s: float, nd: int = 2) -> str:
    return f"{f(m, nd)} ± {s:.{nd}f}"


# ---------------------------------------------------------------- literature


p = LIT["landesfeind2019_kappa_eq15_ec_emc"]["value"]
T20 = 293.15
e = math.exp(1000.0 / T20)
kappa_exp_mScm = (
    p["p1"] * (1 + (T20 - p["p2"])) * 1.0
    * (1 + p["p3"] * 1.0 + p["p4"] * (1 + p["p5"] * e) * 1.0)
    / (1 + 1.0 * p["p6"] * e)
)  # fmt: skip
kappa_exp = kappa_exp_mScm / 10.0  # S/m
v["kappa_exp"] = f(kappa_exp)
tl = LIT["landesfeind2019_tplus_1M_20C_ec_emc"]["value"]
v["tp_lf_meas"], v["tp_lf_fit"] = f(tl["measured"]), f(tl["fit"])
tle = LIT["lehnert2025_tplus_vol_ec_emc"]["value"]
v["tp_le_md"], v["tp_le_enmr"] = f(tle["md"], 3), f(tle["enmr"], 3)
sh = LIT["lehnert2025_shell_fig_s10"]["value"]
v["le_ec"], v["le_emc"], v["le_pf6"] = f(sh["EC"], 1), f(sh["EMC"], 1), f(sh["PF6"], 1)
v["le_share"] = f"{100 * sh['EC'] / (sh['EC'] + sh['EMC']):.0f}"

# DRS (Self 2024): bound EC per Li+ = (1 − A(1 M)/A(neat)) · c_EC(1 M) / c_Li
drs = LIT["self2024_drs_free_ec"]["value"]
aw = LIT["iupac_atomic_weights"]["value"]
m_ec = 3 * aw["C"] + 4 * aw["H"] + 3 * aw["O"]
m_lipf6 = aw["Li"] + aw["P"] + 6 * aw["F"]
rho_box = LIT["lehnert2025_box_density"]["value"]  # g/cm3
c_ec = 0.3 * (rho_box * 1000.0 - 1.0 * m_lipf6) / m_ec  # mol/L; EC is 30 % of the solvent mass
ratio = drs["1M"] / drs["neat"]
ratio_err = ratio * math.hypot(drs["1M_err"] / drs["1M"], drs["neat_err"] / drs["neat"])
bound_frac = 1 - ratio
drs_ec = bound_frac * c_ec / 1.0
drs_ec_err = ratio_err * c_ec
v["drs_a_neat"], v["drs_a_1m"] = f(drs["neat"], 1), f(drs["1M"], 1)
v["drs_frac"] = f"{100 * bound_frac:.0f}"
v["drs_cec"] = f(c_ec)
v["drs_ec"], v["drs_ec_err"] = f(drs_ec, 1), f(drs_ec_err, 1)
m_emc = 4 * aw["C"] + 8 * aw["H"] + 3 * aw["O"]
x_ec = (0.3 / m_ec) / (0.3 / m_ec + 0.7 / m_emc)  # EC mole fraction of EC:EMC 3:7 w:w
v["ec_mol_pct"] = f"{100 * x_ec:.0f}"

ol = LIT["olguin2016_table1"]["value"]
cal = LIT["caleman2012_ec_oplsaa"]["value"]
v["cal_rho"], v["cal_dh"] = f(cal["rho_sim"], 1), f(cal["dhvap_sim"], 2)
v["cal_rho_exp"], v["cal_dh_exp"] = f(cal["rho_exp"], 1), f(cal["dhvap_exp"], 2)

# ---------------------------------------------------------------- quoted validation numbers

for k in QUOTES:
    v["q_" + k] = quoted(k)

# ---------------------------------------------------------------- densities (report data.json)

rep = json.loads((ROOT / "docs/research/report/data.json").read_text())
s2 = rep["table_s2"]
dens = []
for sol, t in (("ec", 40), ("pc", 25), ("dmc", 25), ("emc", 25), ("mp", 25)):
    d = rep["solvent_densities"].get(f"{sol}_{t}_on")
    if d:
        dens.append((sol.upper(), t, d["rho"], 100 * (d["rho"] - s2[sol]) / s2[sol]))
v["dens_ec"] = f(next(x[3] for x in dens if x[0] == "EC"), 1)
v["dens_emc"] = f(next(x[3] for x in dens if x[0] == "EMC"), 1)
v["dens_rows"] = "".join(
    f"<tr><td>{s}</td><td>{t}</td><td>{r:.4f}</td><td>{s2[s.lower()]:.3f}</td>"
    f"<td>{'+' if dev > 0 else ''}{f(dev, 1)} %</td></tr>"
    for s, t, r, dev in dens
)
el_rho, el_sem = rep["electrolyte_npt"]["gpu"]["rho"]  # GPU, 1.5–3 ns
v["el_rho"] = pm(el_rho, el_sem, 4)
v["el_dev"] = f(100 * (el_rho - rep["lehnert_density"]) / rep["lehnert_density"], 1)

# ---------------------------------------------------------------- transport pilot

pilot = STUDIES / "2026-11-19_transport-pilot/runs/ec-emc_3-7w_1.0M/T20C"
tr = json.loads((pilot / "transport.repaired.json").read_text())
k, kne, tp = tr["kappa_S_per_m"], tr["kappa_NE_S_per_m"], tr["t_plus_COM"]
v["kappa"] = pm(k["mean"], k["sem"])
v["kappa_ne"] = pm(kne["mean"], kne["sem"])
v["ionicity"] = pm(tr["ionicity"]["mean"], tr["ionicity"]["sem"])
v["tplus"] = pm(tp["mean"], tp["sem"])
v["kappa_ratio"] = f(kappa_exp / k["mean"], 1)
v["kne_ratio"] = f(kappa_exp / kne["mean"], 1)
for sp in ("Li", "PF6", "EC", "EMC"):
    d = tr[f"D_{sp}_m2_per_s"]
    v[f"D_{sp}"] = f"{d['mean'] * 1e11:.2f} ± {d['sem'] * 1e11:.2f}"
v["pilot_frames"] = str(tr["_meta"]["frames"])

pil = shell(pilot / "out/trajectory.repaired.h5", ["EC:O:1", "EMC:O:1", "PF6:P"], 0.516)
v["pi_ec"], v["pi_emc"], v["pi_pf6"] = (f(pil[x]) for x in ("EC:O:1", "EMC:O:1", "PF6:P"))
v["pi_share"] = f"{100 * pil['EC:O:1'] / (pil['EC:O:1'] + pil['EMC:O:1']):.0f}"

# ---------------------------------------------------------------- one Li+ in EC:EMC 1:1, M0 vs M1

RUNS = {
    "M0": [("2026-11-20_li-preference", "lipf6_in_ec-emc_1-1n")]
    + [("2026-11-21_li-preference-replicas", f"m0_r{i}") for i in (1, 2, 3)],
    "M1": [("2026-11-20_li-preference-m1", "m1_lipf6_in_ec-emc_1-1n")]
    + [("2026-11-21_li-preference-replicas", f"m1_r{i}") for i in (1, 2, 3)],
}
pref: dict[str, dict[str, list[float]]] = {}
for model, runs in RUNS.items():
    pref[model] = {"first": [], "wide": []}
    for study, system in runs:
        run = STUDIES / study / "runs" / system / "T20C"
        if not finished(run, 5000.0):
            pending.append(f"{model} {system}")
            continue
        traj = run / "out/trajectory.h5"
        for key, rc in (("first", 0.28), ("wide", 0.516)):
            c = shell(traj, ["EC:O:1", "EMC:O:1"], rc)
            pref[model][key].append(100 * c["EC:O:1"] / (c["EC:O:1"] + c["EMC:O:1"]))
for model in pref:
    n = len(pref[model]["first"])
    v[f"n_{model}"] = str(n)
    for key in ("first", "wide"):
        m, s = mean_sem(pref[model][key])
        nd = 0 if n > 1 and round(s) >= 1 else 1  # never print a spread as "± 0"
        v[f"{model}_{key}"] = f"{m:.{nd}f} ± {s:.{nd}f}" if n > 1 else f"{m:.0f}"
v["pending_runs"] = (
    f"{len(pending)} of the {sum(len(r) for r in RUNS.values())} runs are still running and "
    "are not included."
    if pending
    else "All runs are included."
)

# ---------------------------------------------------------------- gas-phase binding

ff = json.loads((ROOT / "tools/ffcheck/results/li_binding_2026-11-20.json").read_text())
ffb = {(r["package"].split("_")[0], r["solvent"]): r["e_bind_carbonyl_kcalmol"]
       for r in ff if r["q_li_e"] == 1.0}  # fmt: skip
qm_file = ROOT / "tools/qm/results/li_binding_mp2_aug-cc-pvtz.json"
qm_level = "MP2/aug-cc-pVTZ"
if not qm_file.is_file():
    qm_file = ROOT / "tools/qm/results/li_binding_mp2_6-31+gdp.json"
    qm_level = "MP2/6-31+G(d,p)"
    pending.append("QM at aug-cc-pVTZ")
qm = {r["start"].split("_")[1]: r["e_bind_kcalmol"] for r in json.loads(qm_file.read_text())}
v["qm_level"] = qm_level
v["qm_ec"], v["qm_dmc"] = f(qm["EC"], 1), f(qm["DMC"], 1)
v["ol_ec"], v["ol_dmc"] = f(ol[qm_level]["EC"], 1), f(ol[qm_level]["DMC"], 1)
v["ol_g4_ec"], v["ol_g4_dmc"] = f(ol["G4"]["EC"], 1), f(ol["G4"]["DMC"], 1)
v["dqm"] = f(qm["EC"] - qm["DMC"], 1)
v["dm0"] = f(ffb[("m0", "EC")] - ffb[("m0", "DMC")], 1)
v["dm1"] = f(ffb[("m1", "EC")] - ffb[("m0", "DMC")], 1)
v["m0_ec_bind"] = f(ffb[("m0", "EC")], 1)
under = [ffb[(m, sv)] - ol["G4"][sv] for m, sv in (("m0", "EC"), ("m1", "EC"), ("m0", "DMC"))]
v["under_lo"], v["under_hi"] = f"{min(under):.0f}", f"{max(under):.0f}"
if "EMC" in qm:
    v["qm_emc_sentence"] = (
        f"For EMC, which no published table covers, {qm_level} gives {f(qm['EMC'], 1)} kcal/mol. "
        f"E<sub>bind</sub>(EC) − E<sub>bind</sub>(EMC) is then {f(qm['EC'] - qm['EMC'], 1)} "
        f"kcal/mol in quantum chemistry, {sf(ffb[('m0', 'EC')] - ffb[('m0', 'EMC')])} in M0 and "
        f"{sf(ffb[('m1', 'EC')] - ffb[('m0', 'EMC')])} in M1."
    )
else:
    v["qm_emc_sentence"] = (
        "Li⁺–EMC, which no published table covers, is being computed at the same level."
    )

# DFT functionals of trial T6 (stage 1a) against MP2
t6 = json.loads((RESEARCH / "trials/T6/t6_functional_choice.json").read_text())
NAMES = {"wb97x-d": "ωB97X-D", "wb97m-v//wb97x-d": "ωB97M-V//ωB97X-D", "m06-2x": "M06-2X"}
t6r = {r["functional"]: r for r in t6["ranking"]}
v["t6_chosen"], v["t6_best"] = NAMES[t6["chosen"]], NAMES[t6["best_ranked"]]
v["t6_s_E"] = f(t6r[t6["chosen"]]["s_E_kcalmol"])
v["t6_s_d"] = f(t6r[t6["chosen"]]["s_d_angstrom"], 3)
best = t6r[t6["best_ranked"]]
v["t6_best_miss"] = f(abs(best["ec_minus_emc_kcalmol"] - best["ec_minus_emc_mp2_kcalmol"]), 2)
v["t6_rows"] = "".join(
    f"<tr><td>{NAMES[r['functional']]}</td><td class='n'>{f(r['largest_error_kcalmol'])}</td>"
    f"<td class='n'>{f(r['ec_minus_emc_kcalmol'])}</td>"
    f"<td class='n'>{f(abs(r['ec_minus_emc_kcalmol'] - r['ec_minus_emc_mp2_kcalmol']))}</td>"
    f"<td>{'met' if r['condition_met'] else 'missed'}</td>"
    f"<td class='n'>{f(min(r['li_o_error_angstrom'].values()), 3)} … "
    f"{f(max(r['li_o_error_angstrom'].values()), 3)}</td></tr>"
    for r in t6["ranking"]
)
d_mp2 = qm["EC"] - qm["EMC"]
d_m0 = ffb[("m0", "EC")] - ffb[("m0", "EMC")]
d_m1 = ffb[("m1", "EC")] - ffb[("m0", "EMC")]
v["d_mp2"], v["d_m0"], v["d_m1"] = f(d_mp2), sf(d_m0, 2), f(d_m1)
v["d_m1_pct"] = f"{100 * d_m1 / d_mp2:.0f}"
v["qm_emc"] = f(qm["EMC"], 1)
v["ol_maxdev"] = f(max(abs(qm[s] - ol[qm_level][s]) for s in ("EC", "DMC")), 2)

# ---------------------------------------------------------------- trial T2: EC model at 1 M

t2 = json.loads((RESEARCH / "trials/T2/t2_result.json").read_text())
ms = t2["summary_mean_se"]
for model in ("M0", "M1"):
    for key, tag in (("first_shell_0.28nm", "f"), ("within_0.516nm", "w")):
        for sp, name in (("EC:O:1", "ec"), ("EMC:O:1", "emc"), ("PF6:P", "pf6")):
            m, s = ms[model][f"{key}_{sp}"]
            nd = 3 if (tag, name) == ("f", "pf6") else 2
            v[f"t2_{model}_{tag}_{name}"] = f"{m:.{nd}f}" if nd == 3 else pm(m, s)
    runs = [r for r in t2["runs"].values() if r["model"] == model]
    rho_m, rho_s = mean_sem([r["density"]["density_g_cm3"]["mean"] for r in runs])
    v[f"t2_{model}_rho"] = f"{rho_m:.3f}"
    lf = LIT["landesfeind2019_density_fit_ec_emc_3_7"]["value"]
    rho_lf = lf["p1"] + lf["p2"] * 1.0 + lf["p3"] * T20
    v["rho_lf"] = f"{rho_lf:.3f}"
    v[f"t2_{model}_rho_dev"] = sf(100 * (rho_m - rho_lf) / rho_lf)
    v[f"t2_{model}_kne"] = pm(*mean_sem([r["reported_only"]["kappa_NE_S_per_m"]["mean"] for r in runs]))
    v[f"t2_{model}_dli"] = pm(
        *mean_sem([1e11 * r["reported_only"]["D_Li_m2_per_s"]["mean"] for r in runs]), 1
    )
    v[f"t2_{model}_n"] = str(len(runs))
bound, bound_err = t2["drs_bound"]
ec0, ec1 = ms["M0"]["first_shell_0.28nm_EC:O:1"], ms["M1"]["first_shell_0.28nm_EC:O:1"]
v["t2_gain"] = pm(ec1[0] - ec0[0], math.hypot(ec0[1], ec1[1]))
v["t2_deficit"] = f(bound - ec1[0], 1)
v["t2_frac0"], v["t2_frac1"] = (f"{100 * x[0] / bound:.0f}" for x in (ec0, ec1))
emc1 = ms["M1"]["first_shell_0.28nm_EMC:O:1"][0]
v["t2_emc_share"] = f"{100 * emc1 / (emc1 + ec1[0]):.0f}"
v["bound"], v["bound_err"] = f(bound, 1), f(bound_err, 1)
short = json.loads((RESEARCH / "trials/T2/t2_short.json").read_text())
v["short_m0"], v["short_m1"] = (pm(*short["first_50ps"][m]) for m in ("M0", "M1"))
v["s3_m0"], v["s3_m1"] = (pm(*short["3ns_run_last_1.5ns"][m]) for m in ("M0", "M1"))

# ---------------------------------------------------------------- trial T1: frames of t+

t1 = json.loads((RESEARCH / "trials/T1/t1_result.json").read_text())
ts = t1["stats"]
for k1, k2 in (("COM", "com"), ("SOL", "sol"), ("VOL_A", "vol"), ("VOL_B", "volb")):
    v[f"tp_{k2}"] = pm(ts[k1]["mean"], ts[k1]["sem"])
v["t1_dab"] = f(t1["a_delta_AB"]["mean"], 3)
v["t1_eq2"] = f"{t1['c_max_abs_SOL_minus_Eq2']:.0e}".replace("e-", "e−")
lfit = LIT["lehnert2025_tplus_com_sol_fit_ec_emc"]["value"]
le_com, le_sol = (lfit[k1]["t0"] + lfit[k1]["t1"] * 1.0 for k1 in ("COM", "SOL"))
pulls = [
    abs(ts[fr]["mean"] - x) / ts[fr]["sem"]
    for fr, x in (("SOL", tl["measured"]), ("SOL", tl["fit"]), ("SOL", le_sol), ("VOL_A", tle["md"]),
                  ("VOL_A", tle["enmr"]), ("COM", le_com))
]  # fmt: skip
v["tp_max_pull"] = f(max(pulls), 1)
v["tp_sem_lo"], v["tp_sem_hi"] = (f(fn(ts[x]["sem"] for x in ("COM", "SOL", "VOL_A"))) for fn in (min, max))
v["le_com"], v["le_sol"] = f(le_com), f(le_sol)

# ---------------------------------------------------------------- SPC/Fw water against Wu 2006

wr = json.loads((WU / "data/results.json").read_text())
wt = json.loads((WU / "data/transcribed.json").read_text())
wl = json.loads((WU / "literature.json").read_text())["entries"]["wu2006_spcfw_table2"]["value"]
rho_w, rho_wu = wr["density_g_cm3"], wl["rho_g_cm3"]["value"]
v["w_rho_dev"] = f(100 * (rho_w["mean"] - rho_wu) / rho_wu)
v["w_rho_low"] = f(-100 * (rho_w["mean"] - rho_wu) / rho_wu)
v["w_rho"] = pm(rho_w["mean"], rho_w["sem"], 4)
v["w_cpu_rho"] = pm(wt["twin_density_cpu"]["mean"], wt["twin_density_cpu"]["sem"], 4)
v["w_eta"] = pm(wr["viscosity_mPa_s"]["mean"], wr["viscosity_mPa_s"]["sem"], 3)
v["wu_eta"] = f(wl["eta_cP_at_300.2_K"]["value"])
eb = wr["epsilon"]
dfs = wr["D_finite_size_1e-5_cm2_s"]
wrows = [
    ("⟨r<sub>OH</sub>⟩ (Å)", f"{wr['r_OH_angstrom']['mean']:.4f}", f"{wl['r_OH_angstrom']['value']:.4f}"),
    ("⟨θ<sub>HOH</sub>⟩ (°)", f"{wr['theta_HOH_deg']['mean']:.2f}", f"{wl['theta_HOH_deg']['value']:.2f}"),
    ("⟨μ⟩ (D)", f"{wr['mu_debye']['mean']:.2f}", f"{wl['mu_debye']['value']:.2f}"),
    ("ΔH<sub>vap</sub> (kcal/mol)", f"{wr['hvap_wu_definition']['kcal_per_mol']['mean']:.2f}",
     f"{wl['dHvap_kcal_mol']['value']:.2f}"),
    ("ε", f"{eb['epsilon']:.1f} (blocks {pm(eb['epsilon_blocks']['mean'], eb['epsilon_blocks']['sem'], 1)})",
     f"{wl['epsilon0']['value']:.2f}"),
    ("D in Wu's box (10⁻⁵ cm²/s)", f"{dfs['D_expected_in_wu_box']:.2f}",
     f"{wl['Ds_1e-5_cm2_s']['value']:.2f}"),
    ("ρ (g/cm³)", v["w_rho"], f"{rho_wu:.3f}"),
    ("η at 300.2 K (mPa·s)", v["w_eta"], v["wu_eta"]),
]  # fmt: skip
v["w_rows"] = "".join(
    f"<tr><td>{n}</td><td class='n'>{x}</td><td class='n'>{y}</td></tr>" for n, x, y in wrows
)
v["w_hvap_05"] = f"{wt['hvap_at_0.5fs_kcal_mol']['value']:.2f}"
v["w_ps"] = f"{(wr['run']['skip_ps'] + wr['run']['production_ps']) / 1000:.1f}"
v["w_n"] = str(wr["run"]["molecules"])

# ---------------------------------------------------------------- pass window and EC rung

v["kappa_lo"], v["kappa_hi"] = f(0.85 * kappa_exp), f(1.15 * kappa_exp)  # ±15 %, decision 7
ec_rho, ec_dh = (float(v[f"q_ec_rung_{x}"].split()[0]) for x in ("rho", "dhvap"))
v["ec_rho_vs_cal"] = sf(100 * (ec_rho / cal["rho_sim"] - 1))
v["ec_dh_vs_cal"] = sf(100 * (ec_dh / cal["dhvap_sim"] - 1))
v["ec_rho_vs_exp"] = sf(100 * (ec_rho / cal["rho_exp"] - 1))
v["ec_dh_vs_exp"] = sf(100 * (ec_dh / cal["dhvap_exp"] - 1))
within = [s for s, _, _, dev in dens if abs(dev) <= 2]
v["dens_ok"] = ", ".join(within)

# ---------------------------------------------------------------- figures (SVG, text as text)

plt.rcParams.update({
    "svg.fonttype": "none", "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans"], "font.size": 8.5,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "axes.axisbelow": True, "text.color": INK,
})  # fmt: skip


def svg(fig) -> str:
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight")
    plt.close(fig)
    s = buf.getvalue()
    return s[s.index("<svg") :]


# Fig. 1: the Li+ first shell at 1 M (T2): per seed, and against time from packing
fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.6, 2.25), gridspec_kw={"width_ratios": [1, 1.35]})
for j, (model, col, mk) in enumerate((("M0", BLUE, "o"), ("M1", ORANGE, "s"))):
    runs = [r for r in t2["runs"].values() if r["model"] == model]
    ys = [r["first_shell_0.28nm"]["EC:O:1"] for r in runs]
    a1.scatter([j + 0.16 * (i - 1) for i in range(len(ys))], ys, color=col, marker=mk, s=34, zorder=3,
               edgecolor="white", lw=0.8)  # fmt: skip
    a1.text(j, max(ys) + 0.12, f"{model} {statistics.fmean(ys):.2f}", ha="center", fontsize=7.5)
    wins = [r["convergence"]["EC_first_shell_per_window"] for r in runs]
    t = [x / 1000 + 0.125 for x in runs[0]["convergence"]["window_start_ps"]]
    mean = [statistics.fmean(w) for w in zip(*wins, strict=True)]
    lo, hi = ([fn(w) for w in zip(*wins, strict=True)] for fn in (min, max))
    a2.fill_between(t, lo, hi, color=col, alpha=0.18, lw=0)
    a2.plot(t, mean, color=col, lw=2)
    a2.text(t[-1] + 0.08, mean[-1], model, fontsize=7.5, va="center")
for ax in (a1, a2):
    ax.axhspan(bound - bound_err, bound + bound_err, color=AQUA, alpha=0.35, lw=0)
    ax.set_ylim(0, 2.5)
a1.text(0.5, bound - bound_err - 0.08, "bound from dielectric\nspectroscopy", fontsize=7, ha="center", va="top")
a1.set_xticks([0, 1], ["M0\n(LigParGen EC)", "M1\n(OPLS-AA EC)"], fontsize=7)
a1.set_xlim(-0.5, 1.5)
a1.set_ylabel("EC carbonyl O per Li⁺")
a1.set_title("(a) last 4 ns, one point per run", fontsize=8, loc="left")
a1.grid(axis="x", visible=False)
a2.set_xlim(0, 5.5)
a2.set_xlabel("time from packing (ns)")
a2.set_title("(b) 250 ps windows: mean and range of 3 runs", fontsize=8, loc="left")
fig.subplots_adjust(wspace=0.22)
v["fig_shell"] = svg(fig)

# Fig. 2: EC − EMC binding difference, one Li+ and one solvent molecule
fig, ax = plt.subplots(figsize=(6.2, 2.1))
rows = [("MP2/aug-cc-pVTZ (reference)", d_mp2, AQUA)]
rows += [(NAMES[r["functional"]], r["ec_minus_emc_kcalmol"], MUTED) for r in t6["ranking"]]
rows += [("force field M1 (OPLS-AA EC)", d_m1, ORANGE), ("force field M0 (LigParGen EC)", d_m0, BLUE)]
for i, (lab, val, col) in enumerate(reversed(rows)):
    ax.barh(i, val, color=col, height=0.58)
    ax.text(val + (-0.1 if val < 0 else 0.1), i, f(val) if val < 0 else sf(val, 2), va="center",
            ha="right" if val < 0 else "left", fontsize=7.5)  # fmt: skip
ax.set_yticks(range(len(rows)), [r[0] for r in reversed(rows)], fontsize=7.5)
ax.axvline(0, color=MUTED, lw=0.8)
ax.set_xlim(-7.6, 1.8)
ax.set_xlabel("E_bind(EC) − E_bind(EMC)  (kcal/mol); negative: Li⁺ prefers EC")
ax.grid(axis="y", visible=False)
v["fig_binding"] = svg(fig)

# Fig. 3: kappa with the pass window; t+ frame by frame
fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.8, 2.5), gridspec_kw={"width_ratios": [1, 1.1]})
rows = [("experiment [1]", kappa_exp, 0, AQUA, "D"),
        ("M0: κ_NE", kne["mean"], kne["sem"], BLUE, "s"),
        ("M0: κ (Onsager)", k["mean"], k["sem"], BLUE, "o")]  # fmt: skip
a1.axvspan(0.85 * kappa_exp, 1.15 * kappa_exp, color=AQUA, alpha=0.2, lw=0)
a1.text(kappa_exp, 2.68, "pass window ±15 %", fontsize=7, ha="center", va="bottom")
for i, (lab, m, s, col, mk) in enumerate(reversed(rows)):
    a1.errorbar(m, i, xerr=s or None, fmt=mk, color=col, ms=6, capsize=3, lw=1.2)
    a1.text(m, i + 0.2, f"{m:.2f}", ha="center", fontsize=7.5)
a1.set_yticks(range(len(rows)), [r[0] for r in reversed(rows)], fontsize=7.5)
a1.set_xlim(0, 1.1)
a1.set_ylim(-0.5, 3.0)
a1.set_xlabel("κ at 1 M, 20 °C (S/m)")
a1.grid(axis="y", visible=False)
groups = [
    ("SOL", [("M0", ts["SOL"], BLUE, "o"), ("Lehnert MD", le_sol, MUTED, "v"),
             ("[1] fit", tl["fit"], AQUA, "d"), ("[1] measured", tl["measured"], AQUA, "D")]),
    ("VOL", [("M0", ts["VOL_A"], BLUE, "o"), ("Lehnert MD", tle["md"], MUTED, "v"),
             ("Lehnert eNMR", tle["enmr"], AQUA, "^")]),
    ("COM", [("M0", ts["COM"], BLUE, "o"), ("Lehnert MD", le_com, MUTED, "v")]),
]  # fmt: skip
y, ticks, labs = 0.0, [], []
for frame, items in reversed(groups):
    for lab, val, col, mk in reversed(items):
        m, s = (val["mean"], val["sem"]) if isinstance(val, dict) else (val, None)
        a2.errorbar(m, y, xerr=s, fmt=mk, color=col, ms=5.5, capsize=3, lw=1.2)
        a2.text(0.615, y, f"{m:.2f}", fontsize=7, va="center", ha="right")
        ticks.append(y)
        labs.append(f"{frame}: {lab}")
        y += 1
    y += 0.6
a2.set_yticks(ticks, labs, fontsize=7)
a2.set_xlim(0, 0.63)
a2.set_xlabel("t₊ at 1 M, 20 °C, by reference frame")
a2.grid(axis="y", visible=False)
fig.subplots_adjust(wspace=0.55)
v["fig_transport"] = svg(fig)

# ---------------------------------------------------------------- page

git = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short=12", "HEAD"],
                     capture_output=True, text=True, check=True).stdout.strip()  # fmt: skip
dirty = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "docs/research/summary_261123"],
                       capture_output=True, text=True, check=True).stdout.strip()  # fmt: skip
v["date"] = date.today().isoformat()
v["build_id"] = git + (" + local changes" if dirty else "")
v["pending_note"] = (
    "Still running when this was built: " + "; ".join(pending) + "." if pending else ""
)
html = Template((HERE / "template.html").read_text(encoding="utf-8")).substitute(v)
OUT.mkdir(exist_ok=True)
(OUT / "summary.html").write_text(html, encoding="utf-8")
chrome = shutil.which("chromium") or shutil.which("google-chrome")
if chrome is None:
    sys.exit("no chromium found; out/summary.html is written")
subprocess.run(
    [chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
     f"--print-to-pdf={OUT / 'summary.pdf'}", (OUT / "summary.html").as_uri()],
    check=True, capture_output=True,
)  # fmt: skip
json.dump({"values": {k2: v[k2] for k2 in v if not k2.startswith("fig_")}, "pending": pending},
          (OUT / "values.json").open("w"), indent=1, ensure_ascii=False)  # fmt: skip
print(f"wrote {OUT / 'summary.pdf'}; pending: {pending or 'none'}")
