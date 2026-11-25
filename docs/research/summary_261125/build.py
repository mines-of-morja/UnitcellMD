"""Build the results summary of 2026-11-25 (out1/summary.pdf in this folder).

    HDF5_USE_FILE_LOCKING=FALSE ucmd-analysis/.venv/bin/python docs/research/summary_261125/build.py

Dated successor of docs/research/summary_261123, which stays unchanged. Sources: data/scan.json
(output of the sensitivity scan's analyze.py), data/t6_geometries.json (extract_t6.py), the committed
trial results and the literature ledger, and quoted.json (checked verbatim at its commit). No number
is typed into the text. While the scan is unfinished, data/scan.json says so and the page says PRELIMINARY.
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
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
R = ROOT / "docs/research"
OUT = HERE / "out1"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, MUTED, GRID = "#1f1f1e", "#6b6a63", "#e4e3de"
LIT = json.loads((R / "summary/literature.json").read_text())["entries"]
v: dict[str, str] = {}


def f(x: float, nd: int = 2) -> str:
    return f"{x:.{nd}f}".replace("-", "−")


def sf(x: float, nd: int = 2) -> str:
    return ("+" if x > 0 else "") + f(x, nd)


# quotes, checked verbatim
Q = json.loads((HERE / "quoted.json").read_text())
for key, q in Q["quotes"].items():
    text = subprocess.run(["git", "-C", str(ROOT), "show", f"{Q['ref']}:{q['path']}"],
                          capture_output=True, text=True, check=True).stdout  # fmt: skip
    if q["context"] not in text or q["value"] not in q["context"]:
        sys.exit(f"quoted.json {key}: not verbatim in {q['path']}")
    v["q_" + key] = q["value"]

# experiment, transport pilot, T1, T2
p = LIT["landesfeind2019_kappa_eq15_ec_emc"]["value"]
e = math.exp(1000.0 / 293.15)
k_exp = p["p1"] * (1 + 293.15 - p["p2"]) * (1 + p["p3"] + p["p4"] * (1 + p["p5"] * e)) / (1 + p["p6"] * e) / 10
v["kappa_exp"], v["kappa_lo"], v["kappa_hi"] = f(k_exp), f(0.85 * k_exp), f(1.15 * k_exp)
tr = json.loads((ROOT / "studies/2026-11-19_transport-pilot/runs/ec-emc_3-7w_1.0M/T20C/transport.repaired.json").read_text())
v["kappa_m0"] = f"{f(tr['kappa_S_per_m']['mean'])} ± {f(tr['kappa_S_per_m']['sem'])}"
t1 = json.loads((R / "trials/T1/t1_result.json").read_text())["stats"]
v["tp_sol"] = f"{f(t1['SOL']['mean'])} ± {f(t1['SOL']['sem'])}"
v["tp_exp"] = f(LIT["landesfeind2019_tplus_1M_20C_ec_emc"]["value"]["measured"])
t2 = json.loads((R / "trials/T2/t2_result.json").read_text())
ec = {m: t2["summary_mean_se"][m]["first_shell_0.28nm_EC:O:1"] for m in ("M0", "M1")}
v["ec_m0"], v["ec_m1_shell"] = (f"{f(ec[m][0])} ± {f(ec[m][1])}" for m in ("M0", "M1"))
v["frac_bound"] = f"{100 * ec['M1'][0] / t2['drs_bound'][0]:.0f}"
v["kappa_ratio"] = f(k_exp / tr["kappa_S_per_m"]["mean"], 1)
v["bound"], v["bound_err"] = f(t2["drs_bound"][0], 1), f(t2["drs_bound"][1], 1)
lf = LIT["landesfeind2019_density_fit_ec_emc_3_7"]["value"]
v["rho_lf"] = f(lf["p1"] + lf["p2"] + lf["p3"] * 293.15, 3)

# sensitivity scan
d = json.loads((HERE / "data/scan.json").read_text())
runs, missing = d["runs"], d["not_finished"]
base = [r for r in runs.values() if r["knob"] == "base"]
k0 = math.exp(st.fmean(math.log(r["kappa_NE"]) for r in base))
v["n_done"], v["n_total"] = str(len(runs)), str(len(runs) + len(missing))
v["n_base"] = str(len(base))
v["prelim"] = f"<b>Preliminary: {len(missing)} of the {len(runs) + len(missing)} runs are not in it ({', '.join(missing)}).</b>" if missing else ""
v["prelim_word"] = "Preliminary" if missing else "Final"
v["rule_line"] = (
    "The reading rule is applied when all runs are in; the column shows what it gives now."
    if missing else "All runs are in; the rule fixed before the runs gives:"
)
v["noise_k"] = f"{100 * d['noise_sd_ln']['kappa_NE']:.0f}"
v["k_base"] = f(k0)
v["k_base_lo"], v["k_base_hi"] = f(min(r["kappa_NE"] for r in base)), f(max(r["kappa_NE"] for r in base))
v["t2_lo"], v["t2_hi"] = (f(fn(r["kappa_NE"] for r in d["t2_m1"].values())) for fn in (min, max))
NAMES = {"zeta": "ζ, ion charge scale", "sigmaLi": "σ of Li⁺", "epsEMC": "ε of EMC"}
rows = ""
for knob, name in NAMES.items():
    t = d["trends"][knob]
    pts = [r for r in runs.values() if r["knob"] == knob]
    lo, hi = min(r["x"] for r in pts), max(r["x"] for r in pts)
    probe_rho = [r["density"] for r in pts]
    ec_probe = [r["n_EC_028"] for r in pts]
    c = t["kappa_NE"]
    rows += (
        f"<tr><td>{name}<br><span class='note'>factor {f(lo)} to {f(hi)}, {len(pts)} probes</span></td>"
        f"<td class='n'>{sf(c['exponent'], 1)} ± {f(c['exponent_se'], 1)}</td>"
        f"<td class='n'>{sf(c['ln_change_over_range'])} ± {f(c['ln_change_se'])}</td>"
        f"<td class='n'>{sf(t['D_Li']['exponent'], 1)} ± {f(t['D_Li']['exponent_se'], 1)}</td>"
        f"<td class='n'>{sf(t['D_EMC']['exponent'], 1)} ± {f(t['D_EMC']['exponent_se'], 1)}</td>"
        f"<td class='n'>{f(min(probe_rho), 3)}–{f(max(probe_rho), 3)}</td>"
        f"<td class='n'>{f(min(ec_probe))}–{f(max(ec_probe))}</td>"
        f"<td><b>{'moves' if c['matters'] else 'not resolved'}</b></td></tr>"
    )
    v[f"s_{knob}_change"] = sf(c["ln_change_over_range"])
    v[f"s_{knob}_se"] = f(c["ln_change_se"])
    v[f"s_{knob}_lo2"], v[f"s_{knob}_hi2"] = (
        sf(c["ln_change_over_range"] + z * 2 * c["ln_change_se"]) for z in (-1, 1))
v["scan_rows"] = rows
v["n_runs_word"] = f"{len(runs)}"
v["emc_dens_lo"] = f(min(r["density"] for r in runs.values() if r["knob"] == "epsEMC"), 3)
v["sig_ec_lo"], v["sig_ec_hi"] = (f(fn(r["n_EC_028"] for r in runs.values() if r["knob"] == "sigmaLi")) for fn in (min, max))
v["scan_verdict"] = (
    "So far: " if missing else "")
v["last_xe"] = f(max(r["x"] for r in runs.values() if r["knob"] == "epsEMC"))

# T6 geometries
g = json.loads((HERE / "data/t6_geometries.json").read_text())["clusters"]
v["t6_rows"] = "".join(
    f"<tr><td>Li⁺(EC)<sub>{c['n_ec']}</sub>(EMC)<sub>{4 - c['n_ec']}</sub></td><td class='n'>{c['steps']}</td>"
    f"<td class='n'>{c['wall_h']:.1f}</td>"
    f"<td class='n'>{', '.join(f(x['li_o_angstrom']) for x in c['li_o'] if x['solvent'] == 'EC') or '–'}</td>"
    f"<td class='n'>{', '.join(f(x['li_o_angstrom']) for x in c['li_o'] if x['solvent'] == 'EMC') or '–'}</td></tr>"
    for c in g
)
v["t6_wall"] = f"{sum(c['wall_h'] for c in g):.0f}"
allO = [x["li_o_angstrom"] for c in g for x in c["li_o"]]
v["t6_lo"], v["t6_hi"] = f(min(allO)), f(max(allO))
v["t6_steps_min"], v["t6_steps_max"] = str(min(c["steps"] for c in g)), str(max(c["steps"] for c in g))

# figures
plt.rcParams.update({"svg.fonttype": "none", "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans"],
    "font.size": 8.5, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "axes.axisbelow": True, "text.color": INK})  # fmt: skip


def svg(fig) -> str:
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight")
    plt.close(fig)
    s = buf.getvalue()
    return s[s.index("<svg") :]


LAB = {"zeta": ("ion charge scale ζ", 0.75), "sigmaLi": ("σ(Li⁺) factor", 1.0), "epsEMC": ("ε(EMC) factor", 1.0)}
fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.35), sharey=True)
for ax, (knob, (lab, x0)) in zip(axes, LAB.items(), strict=True):
    pts = [r for r in runs.values() if r["knob"] == knob]
    for r in d["t2_m1"].values():
        ax.plot(x0, r["kappa_NE"], "o", ms=6, mfc="white", mec=MUTED, zorder=3)
    for r in base:
        ax.plot(x0, r["kappa_NE"], "o", ms=6.5, color=MUTED, mec="white", zorder=4)
    ax.plot([r["x"] * x0 for r in pts], [r["kappa_NE"] for r in pts], "o", ms=7, color=BLUE, mec="white", zorder=5)
    x = np.linspace(min(r["x"] for r in pts) * 0.985, max(r["x"] for r in pts) * 1.015, 60)
    c = d["trends"][knob]["kappa_NE"]
    b = c["exponent"]
    # the line passes through the centroid of ln y, ln x of the fitted points (probes and baselines)
    fp = pts + base
    a = st.fmean(math.log(r["kappa_NE"]) for r in fp) - b * st.fmean(math.log(r["x"]) for r in fp)
    ax.plot(x * x0, np.exp(a + b * np.log(x)), "-", lw=2, color=BLUE, alpha=0.65)
    ax.set_yscale("log")
    ax.set_xlabel(lab)
    ax.set_title(f"exponent {f(b, 1)} ± {f(c['exponent_se'], 1)}", fontsize=8, loc="left")
    ax.set_yticks([0.3, 0.4, 0.5, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["0.3", "0.4", "0.5", "0.6", "0.8", "1.0"])
    ax.minorticks_off()
axes[0].set_ylabel("κ_NE at 1 M, 20 °C (S/m)")
axes[0].set_ylim(0.28, 1.15)
fig.subplots_adjust(wspace=0.12)
v["fig_scan"] = svg(fig)

fig, ax = plt.subplots(figsize=(6.2, 1.7))
for name, col, mk, off in (("EC", BLUE, "o", -0.1), ("EMC", ORANGE, "s", 0.1)):
    xs = [c["n_ec"] + off for c in g for x in c["li_o"] if x["solvent"] == name]
    ys = [x["li_o_angstrom"] for c in g for x in c["li_o"] if x["solvent"] == name]
    ax.plot(xs, ys, mk, ms=6.5, color=col, mec="white", label=f"Li–O({name})")
ax.set_xticks(range(5))
ax.set_xlabel("number of EC in the cluster (4 − n are EMC)")
ax.set_ylabel("Li–O (Å)")
ax.legend(frameon=False, fontsize=7.5, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.2))
ax.set_ylim(1.86, 2.06)
v["fig_t6"] = svg(fig)

# page
git = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short=12", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
v["date"], v["build_id"] = date.today().isoformat(), git
html = Template((HERE / "template.html").read_text(encoding="utf-8")).substitute(v)
OUT.mkdir(exist_ok=True)
(OUT / "summary.html").write_text(html, encoding="utf-8")
chrome = shutil.which("chromium") or sys.exit("no chromium; summary.html is written")
subprocess.run([chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={OUT / 'summary.pdf'}",
                (OUT / "summary.html").as_uri()], check=True, capture_output=True)  # fmt: skip
print("wrote", OUT / "summary.pdf", "missing:", missing)
