"""Build the results summary of 2026-11-26 (out1/summary.pdf in this folder).

    HDF5_USE_FILE_LOCKING=FALSE ucmd-analysis/.venv/bin/python docs/research/summary_261126/build.py

What every finished simulation says about densities and transport against experiment. Dated successor
of docs/research/summary_261125, which stays unchanged. Sources, all read here: the literature ledger,
the report's data.json, the trial results (T1, T2), the scan data of the 25 November summary, the water
results (wu2006-spcfw-water), SC-1's sc1.json at its commit, the study indexes (local), and quoted.json
(checked verbatim at its commit). No number is typed into the text. Held under decision 12 of
publication.md: built, not sent.
"""

from __future__ import annotations

import io
import json
import math
import shutil
import statistics as st
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
R = ROOT / "docs/research"
OUT = HERE / "out1"
SC1_REF = "9eda5bd"  # SC-1 result commit (sc1.json and README "Result")
A17_REF = "1045065"  # ucmd-analysis: A1.7 target 1, result.json and REPORT.md
# validated categorical palette (dataviz validator, light surface): M0, M1, water
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, MUTED, GRID, BAND = "#1f1f1e", "#6b6a63", "#e4e3de", "#efeee9"
LIT = json.loads((R / "summary/literature.json").read_text())["entries"]
v: dict[str, str] = {}


def git_show(ref: str, path: str) -> str:
    cmd = ["git", "-C", str(ROOT), "show", f"{ref}:{path}"]
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def f(x: float, nd: int = 2) -> str:
    return f"{x:.{nd}f}".replace("-", "−")


def sf(x: float, nd: int = 1) -> str:
    return ("+" if x > 0 else "") + f(x, nd)


def mean_se(xs: list[float]) -> tuple[float, float]:
    return st.fmean(xs), st.stdev(xs) / math.sqrt(len(xs))


def pm(m: float, s: float, nd: int = 2) -> str:
    return f"{f(m, nd)} ± {f(s, nd)}"


# quotes, checked verbatim at their commit
Q = json.loads((HERE / "quoted.json").read_text())
for key, q in Q["quotes"].items():
    text = git_show(Q["ref"], q["path"])
    if q["context"] not in text or q["value"] not in q["context"]:
        sys.exit(f"quoted.json {key}: not verbatim in {q['path']}")
    v["q_" + key] = q["value"]

# ---------------------------------------------------------------- densities
rep = json.loads((R / "report/data.json").read_text())
sd = rep["solvent_densities"]
dens_rows: list[tuple[str, str, float, float, str, str]] = []  # label, model, dev %, se %, ref, note
table = ""
for s in ("EC", "PC", "DMC", "EMC", "MP"):
    cells = []
    for T in ("25", "40"):
        key = f"rho_{s.lower()}_{T}"
        sim = sd[f"{s.lower()}_{T}_on"]
        if key not in Q["quotes"]:
            cells.append(f"<td class='n'>{f(sim['rho'], 4)}</td><td class='n note'>"
                         f"{'supercooled' if s == 'EC' else 'not measured'}</td>")  # fmt: skip
            continue
        meas = float(Q["quotes"][key]["value"])
        dev = 100 * (sim["rho"] / meas - 1)
        # the README's rounded deviation must agree with the one computed here
        stated = next(p for p in Q["quotes"][key]["context"].split("|") if Q["quotes"][key]["value"] in p)
        if f"{abs(dev):.1f} %" not in stated:
            sys.exit(f"{key}: computed {dev:.2f} % does not match the README cell {stated!r}")
        bold = abs(dev) > 2
        cells.append(f"<td class='n'>{f(sim['rho'], 4)}</td><td class='n'>"
                     f"{'<b>' if bold else ''}{sf(dev)} %{'</b>' if bold else ''}</td>")  # fmt: skip
        dens_rows.append((f"{s}, {T} °C", "M0", dev, 100 * sim["rho_sem"] / meas, "measured", ""))
    table += f"<tr><td>{s}</td>{''.join(cells)}</tr>"
v["solvent_rows"] = table

ec_idx = json.loads((ROOT / "studies/2026-11-20_ec-opls-test/index.json").read_text())["runs"]
ec_m1 = next(r for r in ec_idx if r["system"] == "ec_oplsaa_1000")["density_g_cm3"]
ec_m0 = next(r for r in ec_idx if r["system"] == "ec_ligpargen_1000")["density_g_cm3"]
cal = LIT["caleman2012_ec_oplsaa"]["value"]
v["ec_m1"], v["ec_m0_39"], v["ec_exp39"] = f(ec_m1, 4), f(ec_m0, 4), f(cal["rho_exp"] / 1000, 4)
v["ec_m1_dev"] = sf(100 * (ec_m1 / (cal["rho_exp"] / 1000) - 1))
v["ec_m0_dev39"] = sf(100 * (ec_m0 / (cal["rho_exp"] / 1000) - 1))
dens_rows.append(("EC, 39 °C (M1)", "M1", 100 * (ec_m1 / (cal["rho_exp"] / 1000) - 1), 0.0, "measured", ""))

lf = LIT["landesfeind2019_density_fit_ec_emc_3_7"]["value"]
rho_lf = lf["p1"] + lf["p2"] * 1.0 + lf["p3"] * 293.15
v["rho_lf"] = f(rho_lf, 3)
t2 = json.loads((R / "trials/T2/t2_result.json").read_text())
scan = json.loads((R / "summary_261125/data/scan.json").read_text())
sc1 = json.loads(git_show(SC1_REF, "docs/research/timestep/sc1.json"))
el: list[tuple[str, str, float, float, int, str]] = []
gpu = rep["electrolyte_npt"]["gpu"]["rho"]
el.append(("M0, first NPT run (GPU, 3 ns)", "M0", gpu[0], gpu[1], 1, "1 fs"))
for m in ("M0", "M1"):
    xs = [r["density"]["density_g_cm3"]["mean"] for r in t2["runs"].values() if r["model"] == m]
    el.append((f"{m}, trial T2 (5 ns)", m, *mean_se(xs), len(xs), "1 fs"))
xs = [r["density"] for r in scan["runs"].values() if r["knob"] == "base"]
el.append(("M1, scan baselines (5 ns)", "M1", *mean_se(xs), len(xs), "1 fs"))
xs = [r["rho"] for r in sc1["density"]["1M"]["runs"]["0.5"]]
el.append(("M1, SC-1 (5 ns)", "M1", *mean_se(xs), len(xs), "0.5 fs"))
rows = ""
for label, m, rho, se, n, dt in el:
    dev = 100 * (rho / rho_lf - 1)
    rows += (f"<tr><td>{label}</td><td class='n'>{dt}</td><td class='n'>{n}</td>"
             f"<td class='n'>{pm(rho, se, 4)}</td><td class='n'>{sf(dev, 2)} %</td></tr>")  # fmt: skip
    dens_rows.append((f"1 M: {label.split(' (')[0]}", m, dev, 100 * se / rho_lf, "fit", dt))
v["el_rows"] = rows
v["n_el"] = {4: "four", 5: "five", 6: "six"}.get(len(el), str(len(el)))
m1_t2 = next(r for r in el if r[0].startswith("M1, trial T2"))
v["m1_el_dev"] = sf(100 * (m1_t2[2] / rho_lf - 1), 1)
m0_devs = {r[0]: r[2] for r in dens_rows if r[1] == "M0"}
v["m0_max_dense"] = f(max(m0_devs.values()), 1)
v["m0_ec_light"] = f(-m0_devs["EC, 40 °C"], 1)
v["el_lo"] = sf(min(100 * (r[2] / rho_lf - 1) for r in el), 1)
v["el_hi"] = sf(max(100 * (r[2] / rho_lf - 1) for r in el), 1)

for key, label in (("1M", "1 M box"), ("EMC", "pure EMC"), ("water", "water")):
    d = sc1["density"][key]
    v[f"sc1_{key}"] = f"{sf(d['diff_pct'], 2)} ± {f(d['se_pct'], 2)} %"

wr = json.loads((R / "results/wu2006-spcfw-water/data/results.json").read_text())
wl = json.loads((R / "results/wu2006-spcfw-water/literature.json").read_text())["entries"]
wt = wl["wu2006_spcfw_table2"]["value"]
rho_w = wr["density_g_cm3"]
v["w_rho"], v["w_rho_wu"] = pm(rho_w["mean"], rho_w["sem"], 4), f(wt["rho_g_cm3"]["value"], 3)
v["w_rho_dev"] = sf(100 * (rho_w["mean"] / wt["rho_g_cm3"]["value"] - 1), 2)
dens_rows.append(("SPC/Fw water, 25 °C", "W", 100 * (rho_w["mean"] / wt["rho_g_cm3"]["value"] - 1),
                  100 * rho_w["sem"] / wt["rho_g_cm3"]["value"], "Wu 2006 (model)", "1 fs"))  # fmt: skip

# ---------------------------------------------------------------- transport
p = LIT["landesfeind2019_kappa_eq15_ec_emc"]["value"]
e = math.exp(1000.0 / 293.15)
k_exp = p["p1"] * (1 + 293.15 - p["p2"]) * (1 + p["p3"] + p["p4"] * (1 + p["p5"] * e)) / (1 + p["p6"] * e) / 10
v["k_exp"], v["k_lo"], v["k_hi"] = f(k_exp), f(0.85 * k_exp), f(1.15 * k_exp)
tr = json.loads((ROOT / "studies/2026-11-19_transport-pilot/runs/ec-emc_3-7w_1.0M/T20C/transport.repaired.json").read_text())
kap: list[tuple[str, str, str, float, float, int]] = []  # label, model, kind, value, se, runs
kap.append(("pilot, 20 ns NVT", "M0", "κ", tr["kappa_S_per_m"]["mean"], tr["kappa_S_per_m"]["sem"], 1))
kap.append(("pilot, 20 ns NVT", "M0", "κ_NE", tr["kappa_NE_S_per_m"]["mean"], tr["kappa_NE_S_per_m"]["sem"], 1))
for m in ("M0", "M1"):
    xs = [r["reported_only"]["kappa_NE_S_per_m"]["mean"] for r in t2["runs"].values() if r["model"] == m]
    kap.append(("trial T2, 3 × 5 ns NPT", m, "κ_NE", *mean_se(xs), len(xs)))
xs = [r["kappa_NE"] for r in scan["runs"].values() if r["knob"] == "base"]
kap.append(("scan baselines, 3 × 5 ns NPT", "M1", "κ_NE", *mean_se(xs), len(xs)))
best = max((r for r in scan["runs"].values() if r["knob"] != "base"), key=lambda r: r["kappa_NE"])
best_name = next(k for k, r in scan["runs"].items() if r is best)
noise = scan["noise_sd_ln"]["kappa_NE"]
kap.append((f"largest scan probe ({best_name.replace('_', ' ')})", "M1", "κ_NE", best["kappa_NE"],
            best["kappa_NE"] * noise, 1))  # fmt: skip
rows = ""
for label, m, kind, val, se, n in kap:
    kind_html = "κ<sub>NE</sub>" if kind == "κ_NE" else "κ"
    rows += (f"<tr><td>{label}</td><td>{m}</td><td>{kind_html}</td><td class='n'>{n}</td>"
             f"<td class='n'>{pm(val, se)}</td><td class='n'>{f(val / k_exp, 2)}</td></tr>")  # fmt: skip
v["k_rows"] = rows
v["k_ratio_m1"] = f(k_exp / kap[3][3], 1)
v["k_ratio_pilot"] = f(k_exp / kap[0][3], 1)
v["k_ratio_lo"] = f(min(k_exp / r[3] for r in kap[:-1]), 1)  # model runs, not the probe
v["noise_k"] = f"{100 * noise:.0f}"
v["best_k"], v["best_name"] = f(best["kappa_NE"]), best_name.replace("_", " ")
v["best_frac"] = f"{100 * best['kappa_NE'] / k_exp:.0f}"
v["best_rho_dev"] = sf(100 * (best["density"] / rho_lf - 1), 1)
v["best_in_band"] = "inside" if abs(best["kappa_NE"] / k_exp - 1) <= 0.15 else "outside"

t1 = json.loads((R / "trials/T1/t1_result.json").read_text())["stats"]
tl = LIT["landesfeind2019_tplus_1M_20C_ec_emc"]["value"]
lv = LIT["lehnert2025_tplus_vol_ec_emc"]["value"]
lcs = LIT["lehnert2025_tplus_com_sol_fit_ec_emc"]["value"]
v["tp_sol"], v["tp_com"] = pm(t1["SOL"]["mean"], t1["SOL"]["sem"]), pm(t1["COM"]["mean"], t1["COM"]["sem"])
v["tp_vol"] = f"{pm(t1['VOL_A']['mean'], t1['VOL_A']['sem'])} / {f(t1['VOL_B']['mean'])}"
v["tp_lf"], v["tp_lf_fit"] = f(tl["measured"]), f(tl["fit"])
v["tp_l_vol_md"], v["tp_l_vol_nmr"] = f(lv["md"], 3), f(lv["enmr"], 3)
v["tp_l_sol"] = f(lcs["SOL"]["t0"] + lcs["SOL"]["t1"] * 1.0, 3)
v["tp_l_com"] = f(lcs["COM"]["t0"] + lcs["COM"]["t1"] * 1.0, 3)
v["tp_sol_z"] = f((t1["SOL"]["mean"] - tl["measured"]) / t1["SOL"]["sem"], 1)

drows = ""
D = [("pilot (M0, 1 run)", {k: tr[f"D_{k}_m2_per_s"]["mean"] for k in ("Li", "PF6", "EC", "EMC")})]
for m in ("M0", "M1"):
    runs = [r["reported_only"] for r in t2["runs"].values() if r["model"] == m]
    D.append((f"T2 {m} (3 runs)", {k: st.fmean(r[f"D_{k}_m2_per_s"]["mean"] for r in runs) for k in ("Li", "PF6", "EC", "EMC")}))
base = [r for r in scan["runs"].values() if r["knob"] == "base"]
D.append(("scan M1 (3 runs)", {k: st.fmean(r[f"D_{k}"] for r in base) for k in ("Li", "PF6", "EC", "EMC")}))
for label, dd in D:
    drows += f"<tr><td>{label}</td>" + "".join(f"<td class='n'>{f(dd[k] * 1e11, 1)}</td>" for k in ("Li", "PF6", "EC", "EMC")) + "</tr>"
v["d_rows"] = drows
sd1 = sc1["D"]["1M"]
v["sc1_d_lo"] = f(min(100 * (math.exp(sd1[k]["diff"]) - 1) for k in sd1), 0)
v["sc1_d_hi"] = f(max(100 * (math.exp(sd1[k]["diff"]) - 1) for k in sd1), 0)

dw = wr["D_pbc_1e-5_cm2_s"]
fs = wr["D_finite_size_1e-5_cm2_s"]
eta = wr["viscosity_mPa_s"]
v["w_d"], v["w_d_wu"] = pm(dw["mean"], dw["sem"]), f(wt["Ds_1e-5_cm2_s"]["value"])
v["w_d_exp_box"] = f(fs["D_expected_in_wu_box"])
v["w_eta"], v["w_eta_wu"] = pm(eta["mean"], eta["sem"], 3), f(wt["eta_cP_at_300.2_K"]["value"])
v["w_eta_inacc"] = f(wt["eta_cP_at_300.2_K"]["inaccuracy"])

# A1.7 target 1 (ucmd-analysis, pinned commit)
a17 = json.loads(subprocess.run(["git", "-C", str(ROOT / "ucmd-analysis"), "show", f"{A17_REF}:validation/a17-lj/result.json"],
                                capture_output=True, text=True, check=True).stdout)  # fmt: skip
c17 = a17["criterion"]
v["a17_verdict"], v["a17_value"], v["a17_diff"], v["a17_bound"] = c17["verdict"], pm(c17["value"], c17["se"], 4), sf(c17["difference"], 4), f(c17["bound"], 4)
v["a17_dmu"] = pm(*a17["npt"]["dmu_dlnx"]["matrix_0.2"], 3)
v["a17_nvt"] = f(a17["nvt_minus_npt_in_se"], 2)
v["a17_ref"] = A17_REF
src = subprocess.run(["git", "-C", str(ROOT / "ucmd-analysis"), "show", f"{A17_REF}:validation/a17-lj/analyze.py"],
                     capture_output=True, text=True, check=True).stdout  # fmt: skip
line = next(x for x in src.splitlines() if x.startswith("TARGET, TARGET_ERR = "))
tgt, tgt_err = (float(x) for x in line.split("=")[1].split("#")[0].split(","))
v["a17_target"] = pm(tgt, tgt_err, 3)
v["a17_word"] = {"pass": "passed", "FAIL": "failed"}.get(c17["verdict"], c17["verdict"])

# runs behind the numbers (study indexes, local)
STUDIES = [
    ("2026-11-17_solvent-densities-tail-on", "pure solvents, 25 and 40 °C"),
    ("2026-11-20_ec-opls-test", "pure EC, 39 °C, M0 and M1"),
    ("2026-11-17_electrolyte-npt-gpu", "1 M, first NPT run"),
    ("2026-11-19_transport-pilot", "1 M, transport pilot (NVT)"),
    ("2026-11-21_trial-t2-ec-model-1M", "1 M, trial T2, M0 and M1"),
    ("2026-11-24_parameter-sensitivity-1M", "1 M, sensitivity scan"),
    ("2026-11-25_timestep-1M-0p5fs", "1 M, SC-1 at 0.5 fs"),
    ("2026-11-25_timestep-emc-1fs", "pure EMC, SC-1 at 1 fs"),
    ("2026-11-25_timestep-emc-0p5fs", "pure EMC, SC-1 at 0.5 fs"),
    ("2026-11-20_water-spcfw-wu", "water, Wu protocol (NPT)"),
    ("2026-11-20_water-spcfw-viscosity-cpu", "water, Green–Kubo η (NVT, CPU)"),
    ("2026-11-25_water-npt-gpu", "water, 1 fs (SC-1 reference)"),
    ("2026-11-25_timestep-water-0p5fs", "water, SC-1 at 0.5 fs"),
    ("2026-11-25_timestep-water-0p25fs", "water, SC-1 at 0.25 fs"),
]
rows, total_ns, total_runs = "", 0.0, 0
for name, what in STUDIES:
    idx = json.loads((ROOT / "studies" / name / "index.json").read_text())
    done = [r for r in idx["runs"] if r["state"] == "done"]
    ns = sum((r.get("summary") or {}).get("last_time_ps", 0.0) for r in done) / 1000
    atoms = sorted({r["atoms"] for r in done})
    total_ns += ns
    total_runs += len(done)
    rows += (f"<tr><td>{what}</td><td class='n'>{len(done)}</td><td class='n'>{ns:.1f}</td>"
             f"<td class='n'>{', '.join(str(a) for a in atoms)}</td><td class='note'>{name}</td></tr>")  # fmt: skip
v["run_rows"], v["total_ns"], v["total_runs"] = rows, f"{total_ns:.0f}", str(total_runs)

# ---------------------------------------------------------------- figures
plt.rcParams.update({"svg.fonttype": "none", "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans"],
    "font.size": 8.5, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False, "axes.grid": True,
    "axes.grid.axis": "x", "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "text.color": INK})  # fmt: skip
COL = {"M0": BLUE, "M1": ORANGE, "W": AQUA}
NAME = {"M0": "M0 (LigParGen solvents)", "M1": "M1 (OPLS-AA EC)", "W": "SPC/Fw water"}


def svg(fig) -> str:
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight")
    plt.close(fig)
    s = buf.getvalue()
    return s[s.index("<svg") :]


fig, ax = plt.subplots(figsize=(6.6, 3.5))
ax.axvspan(-2, 2, color=BAND, zorder=0, lw=0)
ax.axvline(0, color=MUTED, lw=0.8)
n = len(dens_rows)
for i, (label, m, dev, se, ref, _dt) in enumerate(dens_rows):
    y = n - 1 - i
    ax.errorbar(dev, y, xerr=2 * se if se else None, fmt="o", ms=6.5, color=COL[m], mec="white",
                mew=1.2, elinewidth=1.4, capsize=0, zorder=3)  # fmt: skip
ax.set_yticks(range(n))
ax.set_yticklabels([r[0] for r in reversed(dens_rows)])
ax.set_xlabel("simulated density − reference (%)")
ax.set_xlim(-4.2, 4.2)
ax.text(1.95, n - 0.35, "±2 % (solvent criterion)", ha="right", va="bottom", fontsize=7.5, color=MUTED)
for m in ("M0", "M1", "W"):
    ax.plot([], [], "o", ms=6.5, color=COL[m], mec="white", label=NAME[m])
ax.legend(frameon=False, fontsize=7.5, loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=3)
ax.set_ylim(-0.7, n - 0.1)
v["fig_density"] = svg(fig)

fig, ax = plt.subplots(figsize=(6.6, 2.4))
ax.axvspan(0.85 * k_exp, 1.15 * k_exp, color=BAND, zorder=0, lw=0)
ax.axvline(k_exp, color=INK, lw=1.2)
ax.text(1.15 * k_exp + 0.01, len(kap) - 0.45, f"measured {f(k_exp)} S/m\n±15 % criterion", ha="left", va="bottom",
        fontsize=7.5, color=INK)  # fmt: skip
for i, (label, m, kind, val, se, _n) in enumerate(kap):
    y = len(kap) - 1 - i
    filled = kind == "κ"
    ax.errorbar(val, y, xerr=2 * se, fmt="D" if filled else "o", ms=6.5, color=COL[m],
                mfc=COL[m] if filled else "white", mec=COL[m], mew=1.6, elinewidth=1.4, capsize=0, zorder=3)  # fmt: skip
ax.set_yticks(range(len(kap)))
ax.set_yticklabels([f"{r[0]} — {'κ' if r[2] == 'κ' else 'κ_NE'}" for r in reversed(kap)])
ax.set_xlabel("conductivity at 1 M, 20 °C (S/m); bars ±2 SE")
ax.set_xlim(0, 1.2)
ax.set_ylim(-0.6, len(kap) + 0.1)
for m in ("M0", "M1"):
    ax.plot([], [], "o", ms=6.5, color=COL[m], label=NAME[m])
ax.plot([], [], "D", ms=6, color=MUTED, label="κ (Onsager, all correlations)")
ax.plot([], [], "o", ms=6, mfc="white", mec=MUTED, mew=1.6, label="κ_NE (no correlations)")
ax.legend(frameon=False, fontsize=7.3, loc="lower left", bbox_to_anchor=(0.0, 1.08), ncol=4)
v["fig_kappa"] = svg(fig)

# ---------------------------------------------------------------- page
git = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short=12", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
v["date"], v["build_id"], v["sc1_ref"] = date.today().isoformat(), git, SC1_REF
html = Template((HERE / "template.html").read_text(encoding="utf-8")).substitute(v)
OUT.mkdir(exist_ok=True)
(OUT / "summary.html").write_text(html, encoding="utf-8")
chrome = shutil.which("chromium") or sys.exit("no chromium; summary.html is written")
subprocess.run([chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={OUT / 'summary.pdf'}",
                (OUT / "summary.html").as_uri()], check=True, capture_output=True)  # fmt: skip
print("wrote", OUT / "summary.pdf")
