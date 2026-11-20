"""Figures and numbers of the research report (docs/research/report/report.md).

    HDF5_USE_FILE_LOCKING=FALSE ucmd-analysis/.venv/bin/python docs/research/report/figures.py

Reads the studies in studies/ (local data, not in git) and writes figures/*.png and data.json
next to this file. Runs that are missing or unfinished are skipped and reported as pending.
Every number in the report comes from data.json.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from ucmd_analysis import constants as c
from ucmd_analysis.io import read_h5md

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
STUDIES = ROOT / "studies"
FIG = HERE / "figures"
# Manufacturer densities, Lehnert 2025 SI Table S2 (g/ml; temperature not stated, EC as liquid)
TABLE_S2 = {"ec": 1.321, "emc": 1.006, "dmc": 1.069, "pc": 1.204, "mp": 0.915}
# Lehnert's 1 M EC:EMC box: 47 ion pairs tuned to 1.0 M at 20 °C → V = 47/(1 mol/L·N_A)
LEHNERT_VOLUME_NM3 = 47 / (c.AVOGADRO_PER_MOL * 1e-24)
data: dict = {}


def thermo(path: Path) -> tuple[list[str], np.ndarray] | None:
    if not path.is_file():
        return None
    with path.open() as fh:
        names = fh.readline().lstrip("# ").strip().split("\t")
        rows = np.loadtxt(fh, ndmin=2)
    return names, rows


def col(t: tuple[list[str], np.ndarray], name: str) -> np.ndarray:
    return t[1][:, t[0].index(name)]


def block_mean(x: np.ndarray, n: int = 5) -> tuple[float, float]:
    x = x[np.isfinite(x)]
    b = np.array([v.mean() for v in np.array_split(x, n)])
    return float(b.mean()), float(b.std(ddof=1) / math.sqrt(n))


def mass_g(study: str, system: str) -> float:
    s = json.loads((STUDIES / study / "systems" / system / "status.json").read_text())
    return s["mass_amu"] * c.AMU_IN_G


def density(study: str, system: str, label: str) -> dict | None:
    run = STUDIES / study / "runs" / system / label
    t = thermo(run / "out/thermo.tsv")
    status = json.loads((run / "status.json").read_text()) if (run / "status.json").is_file() else {}
    if t is None or status.get("state") != "done":
        return None
    time = col(t, "time_ps")
    w = time >= time[-1] / 2
    rho = mass_g(study, system) / (col(t, "volume_nm3")[w] * c.NM3_IN_CM3)
    mean, sem = block_mean(rho)
    p_mean, p_sem = block_mean(col(t, "pressure_bar")[w])
    return {"rho": mean, "rho_sem": sem, "p_bar": p_mean, "p_sem": p_sem,
            "window_ps": [float(time[-1] / 2), float(time[-1])]}  # fmt: skip


# -- 1. pure-solvent densities ------------------------------------------------------------------
solv = {}
for tail, study in (("off", "2026-11-17_pure-solvent-densities"),
                    ("on", "2026-11-17_solvent-densities-tail-on")):  # fmt: skip
    for s in TABLE_S2:
        for temp in (25, 40):
            r = density(study, f"{s}_pure", f"T{temp}C")
            solv[f"{s}_{temp}_{tail}"] = r
data["solvent_densities"] = solv
data["table_s2"] = TABLE_S2

fig, ax = plt.subplots(figsize=(7, 3.6))
names = list(TABLE_S2)
x = np.arange(len(names))
for k, (tail, temp, colour) in enumerate((("on", 25, "#1f77b4"), ("on", 40, "#ff7f0e"),
                                          ("off", 25, "#9e9e9e"))):  # fmt: skip
    dev = [100 * (solv[f"{s}_{temp}_{tail}"]["rho"] / TABLE_S2[s] - 1)
           if solv.get(f"{s}_{temp}_{tail}") else np.nan for s in names]  # fmt: skip
    ax.bar(x + (k - 1) * 0.26, dev, 0.26, color=colour,
           label=f"{temp} °C, tail correction {tail}")  # fmt: skip
ax.axhline(0, color="k", lw=0.8)
ax.axhspan(-2, 2, color="green", alpha=0.08, label="±2 % (validation plan, level 1)")
ax.set_xticks(x, [n.upper() for n in names])
ax.set_ylabel("ρ_sim / ρ_Table S2 − 1 (%)")
ax.set_title("Pure solvents, NPT 1 atm (EC: Table S2 is the liquid near 40 °C)")
ax.legend(fontsize=7, loc="upper right")
fig.tight_layout()
FIG.mkdir(exist_ok=True)
fig.savefig(FIG / "fig2_solvent_densities.png", dpi=150)
plt.close(fig)

# -- 2. pressure at the reference density (NVT, CPU) --------------------------------------------
ref = {}
fig, ax = plt.subplots(figsize=(7, 3.4))
for system, label, colour in (("ec-emc_3-7w_1.0M", "1 M EC:EMC at Lehnert's density", "#d62728"),
                              ("emc_pure", "pure EMC at 1.006 g/cm³", "#1f77b4")):  # fmt: skip
    t = thermo(STUDIES / "2026-11-17_pressure-at-reference-density/runs" / system / "T20C/out/thermo.tsv")
    if t is None:
        continue
    time, p = col(t, "time_ps"), col(t, "pressure_bar")
    ax.plot(time, p, color=colour, alpha=0.25, lw=0.5)
    k = np.convolve(p, np.ones(50) / 50, mode="valid")
    ax.plot(time[49:], k, color=colour, lw=1.6, label=label + " (1 ps mean)")
    w = time >= 50
    ref[system] = dict(zip(("p_bar", "p_sem"), block_mean(p[w]), strict=True))
ax.axhline(0, color="k", lw=0.8)
ax.set_xlabel("t (ps)")
ax.set_ylabel("P (bar)")
ax.set_ylim(-1500, 9000)
ax.set_title("NVT at 20 °C, tail correction off (adds ≈ −160 bar)")
ax.legend(fontsize=7)
fig.tight_layout()
fig.savefig(FIG / "fig1_pressure_reference_density.png", dpi=150)
plt.close(fig)
data["pressure_at_reference_density_50_100ps"] = ref

# -- 3. electrolyte NPT density -----------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7, 3.4))
elec = {}
for backend, colour in (("cpu", "#2ca02c"), ("gpu", "#9467bd")):
    study = f"2026-11-17_electrolyte-npt-{backend}"
    t = thermo(STUDIES / study / "runs/ec-emc_3-7w_1.0M/T20C/out/thermo.tsv")
    if t is None:
        continue
    time = col(t, "time_ps")
    rho = mass_g(study, "ec-emc_3-7w_1.0M") / (col(t, "volume_nm3") * c.NM3_IN_CM3)
    ax.plot(time, rho, color=colour, lw=0.7, label=f"{backend.upper()} backend")
    w = time >= max(200.0, time[-1] / 2)
    elec[backend] = {"rho": block_mean(rho[w]), "until_ps": float(time[-1])}
ax.axhline(c.AMU_IN_G * 0 + mass_g("2026-11-17_electrolyte-npt-cpu", "ec-emc_3-7w_1.0M")
           / (LEHNERT_VOLUME_NM3 * c.NM3_IN_CM3), color="k", ls="--", lw=1,
           label="Lehnert's force field (box tuned to 1.0 M)")  # fmt: skip
ax.set_xscale("symlog", linthresh=10)
ax.set_xlim(left=0)
ax.set_xlabel("t (ps)")
ax.set_ylabel("ρ (g/cm³)")
ax.set_title("1 M LiPF₆ in EC:EMC 3:7, NPT 1 atm, 20 °C, tail correction on")
ax.legend(fontsize=7)
fig.tight_layout()
fig.savefig(FIG / "fig3_electrolyte_density.png", dpi=150)
plt.close(fig)
data["electrolyte_npt"] = elec
data["lehnert_density"] = mass_g("2026-11-17_electrolyte-npt-cpu", "ec-emc_3-7w_1.0M") / (
    LEHNERT_VOLUME_NM3 * c.NM3_IN_CM3
)


# -- 4. Li+ first shell over time ---------------------------------------------------------------
def shell_counts(path: Path, stride: int) -> dict:
    traj = read_h5md(path, stride=stride)
    sys = traj.system
    li = sys.atoms_where("Li", "Li")
    groups = {
        "EC O=C": (sys.atoms_where("EC", "O", bonded=1), 0.28),
        "EMC O=C": (sys.atoms_where("EMC", "O", bonded=1), 0.29),
        "PF6 F": (sys.atoms_where("PF6", "F"), 0.26),
    }
    out = {"t_ps": traj.times_ps.tolist()}
    for name, (atoms, r_cut) in groups.items():
        n = []
        for x, h in zip(traj.positions_nm, traj.boxes_nm, strict=True):
            d = x[li][:, None, :] - x[atoms][None, :, :]
            s = d @ np.linalg.inv(h)
            s -= np.round(s)
            r = np.linalg.norm(s @ h, axis=-1)
            n.append(float((r < r_cut).sum(axis=1).mean()))
        out[name] = n
    return out


shells = {}
fig, ax = plt.subplots(figsize=(7, 3.4))
for backend, stride, ls in (("cpu", 5, ":"), ("gpu", 2, "-")):
    path = STUDIES / f"2026-11-17_electrolyte-npt-{backend}/runs/ec-emc_3-7w_1.0M/T20C/out/trajectory.h5"
    if not path.is_file():
        continue
    sc = shell_counts(path, stride)
    shells[backend] = {k: (v[-1] if k != "t_ps" else v[-1]) for k, v in sc.items()}
    for name, colour in (("EC O=C", "#1f77b4"), ("EMC O=C", "#ff7f0e"), ("PF6 F", "#2ca02c")):
        ax.plot(sc["t_ps"], sc[name], ls=ls, color=colour, label=f"{name} ({backend.upper()})")
ax.set_xlabel("t (ps)")
ax.set_ylabel("neighbours per Li⁺ (first shell)")
ax.set_title("Li⁺ first shell after packing (EC is 34 % of the solvent molecules)")
ax.legend(fontsize=7, ncol=2)
fig.tight_layout()
fig.savefig(FIG / "fig4_li_shell.png", dpi=150)
plt.close(fig)
data["li_shell_last_frame"] = shells

(HERE / "data.json").write_text(json.dumps(data, indent=1, default=float))
print(json.dumps({k: data[k] for k in ("electrolyte_npt", "pressure_at_reference_density_50_100ps",
                                       "li_shell_last_frame")}, indent=1, default=float))  # fmt: skip
print({k: (round(v["rho"], 4) if v else None) for k, v in solv.items()})
