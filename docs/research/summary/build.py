"""Build the results summary (docs/research/summary/out/summary.pdf).

    HDF5_USE_FILE_LOCKING=FALSE ucmd-analysis/.venv/bin/python docs/research/summary/build.py

Every number in the summary comes from one of three places, never typed into the text
(docs/research/publication.md, rule 6):
- the study data in studies/ (local, not in git), analysed here with ucmd-analyze;
- literature.json, the literature ledger (rule 3);
- quoted.json, numbers stated in our own validation reports, checked verbatim against them.
Runs that are missing or unfinished are left out and the text says how many were used.
The PDF is printed by headless Chromium from out/summary.html.
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
OUT = HERE / "out"
ANALYZE = ROOT / "ucmd-analysis" / ".venv" / "bin" / "ucmd-analyze"
LIT = json.loads((HERE / "literature.json").read_text(encoding="utf-8"))["entries"]
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


# Fig. 1: solvent densities, deviation from the reference
fig, ax = plt.subplots(figsize=(3.3, 2.1))
names = [f"{d[0]}\n{d[1]} °C" for d in dens]
devs = [d[3] for d in dens]
ax.axhspan(-2, 2, color=GRID, alpha=0.6, lw=0)
ax.bar(names, devs, color=BLUE, width=0.55)
for i, dv in enumerate(devs):
    ax.text(i, dv + (0.25 if dv > 0 else -0.25), f"{dv:+.1f}", ha="center",
            va="bottom" if dv > 0 else "top", fontsize=7.5, color=INK)  # fmt: skip
ax.axhline(0, color=MUTED, lw=0.8)
ax.set_ylabel("ρ deviation (%)")
ax.set_ylim(-4.6, 4.0)
ax.tick_params(axis="x", labelsize=7)
ax.grid(axis="x", visible=False)
ax.text(len(devs) - 0.6, -1.8, "±2 %", fontsize=7, color=MUTED, ha="right", va="bottom")
v["fig_density"] = svg(fig)

# Fig. 2: kappa and t+
fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.4, 2.2), gridspec_kw={"width_ratios": [1, 1.25]})
rows = [("experiment (Landesfeind 2019, Eq. 15)", kappa_exp, 0, AQUA, "D"),
        ("this work: κ (Onsager)", k["mean"], k["sem"], BLUE, "o"),
        ("this work: κ_NE (Nernst–Einstein)", kne["mean"], kne["sem"], BLUE, "s")]  # fmt: skip
for i, (lab, m, s, col, mk) in enumerate(rows):
    a1.errorbar(m, i, xerr=s or None, fmt=mk, color=col, ms=6, capsize=3, lw=1.2)
    a1.text(m, i + 0.32, f"{m:.2f}", ha="center", fontsize=7.5)
a1.set_yticks(range(len(rows)), [r[0] for r in rows], fontsize=7)
a1.set_xlim(0, 1.0)
a1.set_ylim(-0.6, len(rows) - 0.3)
a1.set_xlabel("κ at 1 M, 20 °C (S/m)")
a1.grid(axis="y", visible=False)
rows = [("Landesfeind 2019, measured", tl["measured"], 0, AQUA, "D"),
        ("Landesfeind 2019, fit", tl["fit"], 0, AQUA, "d"),
        ("Lehnert 2025, eNMR (VOL)", tle["enmr"], 0, AQUA, "^"),
        ("Lehnert 2025, MD (VOL)", tle["md"], 0, MUTED, "v"),
        ("this work, MD (COM)", tp["mean"], tp["sem"], BLUE, "o")]  # fmt: skip
for i, (lab, m, s, col, mk) in enumerate(rows):
    a2.errorbar(m, i, xerr=s or None, fmt=mk, color=col, ms=6, capsize=3, lw=1.2)
    a2.text(m + 0.015, i + 0.3, f"{m:.2f}", fontsize=7.5)
a2.set_yticks(range(len(rows)), [r[0] for r in rows], fontsize=7)
a2.yaxis.tick_right()
a2.set_xlim(0, 0.6)
a2.set_ylim(-0.6, len(rows) - 0.3)
a2.set_xlabel("t₊ at 1 M, 20 °C")
a2.grid(axis="y", visible=False)
fig.subplots_adjust(wspace=0.15)
v["fig_transport"] = svg(fig)

# Fig. 3: Li+ shell. (a) EC per Li+ at 1 M; (b) EC share of the first-shell carbonyl O, per run
fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.4, 2.3), gridspec_kw={"width_ratios": [1, 1]})
bars = [("this work (M0)", pil["EC:O:1"], BLUE),
        ("Lehnert's model", sh["EC"], MUTED),
        ("DRS estimate", drs_ec, AQUA)]  # fmt: skip
for i, (lab, val, col) in enumerate(bars):
    a1.bar(i, val, color=col, width=0.55)
    a1.text(i, val + 0.08, f"{val:.1f}", ha="center", fontsize=7.5)
a1.errorbar(2, drs_ec, yerr=drs_ec_err, fmt="none", ecolor=INK, capsize=3, lw=1)
a1.set_xticks(range(3), [b[0] for b in bars], fontsize=7)
a1.set_ylabel("EC carbonyl O per Li⁺")
a1.set_ylim(0, 3.0)
a1.set_title("(a) 1 M LiPF₆ in EC:EMC 3:7, 20 °C", fontsize=8, loc="left")
a1.grid(axis="x", visible=False)
for j, (model, col, mk) in enumerate((("M0", BLUE, "o"), ("M1", ORANGE, "s"))):
    vals = pref[model]["first"]
    xs = [j + 0.12 * (i - (len(vals) - 1) / 2) for i in range(len(vals))]
    a2.scatter(xs, vals, color=col, marker=mk, s=28, zorder=3, edgecolor="white", lw=0.8)
    if len(vals) > 1:
        m, s = mean_sem(vals)
        a2.errorbar(j + 0.33, m, yerr=s, fmt="_", color=INK, ms=12, capsize=3, lw=1.2)
        a2.text(j + 0.42, m, f"{v[f'{model}_first']} %", fontsize=7.5, va="center")  # as in the text
a2.axhline(50, color=MUTED, lw=0.8, ls="--")
a2.text(1.75, 51, "EC share of the molecules", fontsize=7, color=MUTED, ha="right", va="bottom")
a2.set_xticks([0, 1], ["M0 (LigParGen EC)", "M1 (OPLS-AA EC)"], fontsize=7)
a2.set_xlim(-0.5, 1.8)
a2.set_ylim(0, 60)
a2.set_ylabel("EC share, first shell (%)")
a2.set_title("(b) one LiPF₆ in EC:EMC 1:1 (mol), per run", fontsize=8, loc="left")
a2.grid(axis="x", visible=False)
fig.subplots_adjust(wspace=0.35)
v["fig_shell"] = svg(fig)

# Fig. 4: gas-phase binding energies
sols = [s for s in ("EC", "DMC", "EMC", "PC") if s in qm or ("m0", s) in ffb]
fig, ax = plt.subplots(figsize=(6.4, 2.0))
w = 0.26
series = [(f"QM, {qm_level}", lambda s: qm.get(s), AQUA),
          ("M0 (LigParGen)", lambda s: ffb.get(("m0", s)), BLUE),
          ("M1 (OPLS-AA EC)", lambda s: ffb.get(("m1", s)), ORANGE)]  # fmt: skip
for j, (lab, get, col) in enumerate(series):
    for i, s in enumerate(sols):
        val = get(s)
        if val is None:
            continue
        x = i + (j - 1) * w
        ax.bar(x, val, width=w - 0.03, color=col, label=lab if i == 0 or s == "EC" else None)
        ax.text(x, val - 0.8, f"{val:.1f}", ha="center", va="top", fontsize=6.8)
handles, labels = ax.get_legend_handles_labels()
uniq = dict(zip(labels, handles, strict=True))
ax.legend(uniq.values(), uniq.keys(), fontsize=7, frameon=False, loc="lower right", ncol=3,
          bbox_to_anchor=(1.0, 1.0))  # fmt: skip
ax.set_xticks(range(len(sols)), [f"Li⁺–{s}" for s in sols])
ax.set_ylabel("E_bind (kcal/mol)")
ax.set_ylim(-56, 0)
ax.axhline(0, color=MUTED, lw=0.8)
ax.grid(axis="x", visible=False)
v["fig_binding"] = svg(fig)

# ---------------------------------------------------------------- page

git = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short=12", "HEAD"],
                     capture_output=True, text=True, check=True).stdout.strip()  # fmt: skip
dirty = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "docs/research/summary"],
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
