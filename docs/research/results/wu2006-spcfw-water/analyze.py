"""Study data -> data/results.json, data/traces_1ps.csv, data/manifest.json.

    ucmd-analysis/.venv/bin/python docs/research/results/wu2006-spcfw-water/analyze.py

Every number in the summary comes from here (docs/research/publication.md, rule 6). Reads the
local data of three studies (not in git); the results are small and are committed.

  studies/2026-11-20_water-spcfw-wu            512 SPC/Fw, 298.16 K, 1 atm, 6.5 ns (GPU)
  studies/2026-11-20_water-spcfw-viscosity-cpu 512 SPC/Fw, NVT, 300.2 K, rho = 1.012, 4 ns (CPU)
  studies/2026-11-20_water-spcfw-cpu/gas       one molecule, for the Caleman definition of dHvap

Library calls only (ucmd_analysis); nothing is typed in from a paper. Wu's values are in
literature.json.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
from ucmd_analysis import constants as c
from ucmd_analysis.dielectric import dielectric
from ucmd_analysis.hvap import hvap, potential_series
from ucmd_analysis.io import read_h5md
from ucmd_analysis.molecules import barycentric
from ucmd_analysis.msd import self_msd
from ucmd_analysis.transport import FitWindow, slope
from ucmd_analysis.uncertainty import blocks, mean_sem
from ucmd_analysis.viscosity import green_kubo, read_tensor, shear_components

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
WU = ROOT / "studies/2026-11-20_water-spcfw-wu/runs/spcfw_512/T25.01C"
VISC = ROOT / "studies/2026-11-20_water-spcfw-viscosity-cpu/runs/spcfw_512/T27.05C"
GAS = ROOT / "studies/2026-11-20_water-spcfw-cpu/gas/out_dt1.0/thermo.tsv"

T_WU = 298.16  # K, the run's thermostat and barostat temperature (run.toml)
SKIP_PS = 500.0  # equilibration skipped, as in Wu
T_VISC = 300.2  # K, run.toml of the viscosity run
KCAL_KJ = 4.184
DEBYE_CM = 1e-21 / 299792458.0  # 1 D in C m (exact: 1e-21/c)
D_UNIT = 1e9  # m^2/s -> 1e-5 cm^2/s
BOX_WU_NM = 1.855  # 216 molecules at 1.012 g/cm^3, the box of Wu et al.


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 24), b""):
            h.update(chunk)
    return h.hexdigest()


def thermo(path: Path) -> tuple[list[str], np.ndarray]:
    with path.open() as fh:
        names = fh.readline().lstrip("# ").strip().split("\t")
        return names, np.loadtxt(fh, ndmin=2)


def ms(values) -> dict:
    mean, sem = mean_sem(values)
    return {"mean": mean, "sem": sem}


def yeh_hummer_shift(temperature_K: float, eta_Pa_s: float, edge_nm: float) -> float:
    """k_B T xi / (6 pi eta L) in 1e-5 cm^2/s (Yeh & Hummer 2004, cubic box)."""
    return (c.BOLTZMANN_J_PER_K * temperature_K * c.YEH_HUMMER_XI_CUBIC
            / (6 * math.pi * eta_Pa_s * edge_nm * c.NM_IN_M) * D_UNIT)  # fmt: skip


def main() -> None:
    out: dict = {"_about": __doc__.split("\n\n")[0]}

    # ---- thermo of the Wu run: density, U/N, dHvap ----
    names, rows = thermo(WU / "out/thermo.tsv")
    t, u, v = (rows[:, names.index(k)] for k in ("time_ps", "potential_kjmol", "volume_nm3"))
    traj = read_h5md(WU / "out/trajectory.h5", start=int(SKIP_PS / 0.5))
    n_mol = traj.system.species["water"].count
    mass = traj.system.total_mass_amu()
    rho = mass * c.AMU_IN_G / (v * 1e-21)  # g/cm^3 (nm^3 = 1e-21 cm^3)
    keep = t >= SKIP_PS
    out["run"] = {
        "molecules": n_mol, "temperature_K": T_WU, "skip_ps": SKIP_PS,
        "production_ps": float(t[-1] - SKIP_PS), "thermo_rows_used": int(keep.sum()),
        "trajectory_frames_used": len(traj), "frame_interval_ps": float(np.diff(traj.times_ps)[0]),
        "mean_volume_nm3": float(v[keep].mean()), "provenance": traj.provenance,
    }  # fmt: skip
    nb = 10
    out["density_g_cm3"] = {
        **ms([float(rho[keep][s].mean()) for s in blocks(int(keep.sum()), nb)]),
        "blocks": nb,
    }
    wu_def = hvap(u[keep], n_mol, np.zeros(10), T_WU, n_blocks=nb)  # no gas term (Wu)
    h = wu_def["hvap_kj_per_mol"]
    out["hvap_wu_definition"] = {
        "kJ_per_mol": h, "kcal_per_mol": {k: x / KCAL_KJ for k, x in h.items()},
        "u_per_molecule_kJ_per_mol": wu_def["u_liquid_per_molecule_kj_per_mol"],
        "RT_kJ_per_mol": wu_def["RT_kj_per_mol"], "blocks": nb,
    }  # fmt: skip
    if GAS.is_file():
        g = hvap(u[keep], n_mol, potential_series(GAS), T_WU, n_blocks=nb)
        gh = g["hvap_kj_per_mol"]
        out["hvap_caleman_definition"] = {
            "kJ_per_mol": gh, "kcal_per_mol": {k: x / KCAL_KJ for k, x in gh.items()},
            "u_gas_kJ_per_mol": g["u_gas_kj_per_mol"], "gas_source": str(GAS.relative_to(ROOT)),
        }  # fmt: skip

    # ---- geometry and dipole ----
    mol = traj.system.species["water"]
    x = traj.positions_nm[:, mol.atoms, :]  # frames, molecules, (O, H1, H2), 3
    q = traj.system.charges[mol.atoms[0]]
    d1, d2 = x[:, :, 1] - x[:, :, 0], x[:, :, 2] - x[:, :, 0]
    r1, r2 = np.linalg.norm(d1, axis=-1), np.linalg.norm(d2, axis=-1)
    cos = (d1 * d2).sum(-1) / (r1 * r2)
    theta = np.degrees(np.arccos(cos))
    mu = np.linalg.norm(np.einsum("k,fmkd->fmd", q, x - x[:, :, :1]), axis=-1)  # e nm
    per = blocks(len(traj), nb)
    e_nm_in_debye = c.ELEMENTARY_CHARGE_C * c.NM_IN_M / DEBYE_CM
    out["r_OH_angstrom"] = ms([float(0.5 * (r1[s] + r2[s]).mean()) * 10 for s in per])
    out["theta_HOH_deg"] = ms([float(theta[s].mean()) for s in per])
    out["mu_debye"] = ms([float(mu[s].mean()) * e_nm_in_debye for s in per])
    out["geometry_blocks"] = nb
    # standard deviations of the fluctuations, the kind of number in parentheses in Wu's Table II
    # (per molecule and frame for theta and mu; per thermo row for the density)
    out["fluctuation_sd"] = {
        "density_g_cm3": float(rho[keep].std(ddof=1)),
        "theta_HOH_deg": float(theta.std(ddof=1)),
        "mu_debye": float(mu.std(ddof=1) * e_nm_in_debye),
        "density_sd_scaled_to_216_molecules": float(rho[keep].std(ddof=1) * math.sqrt(n_mol / 216)),
        "note": "a standard deviation, not an error of the mean; it scales as 1/sqrt(N)",
    }

    # ---- dielectric constant (conducting boundaries, Wu Eq. 3) ----
    out["epsilon"] = dielectric(traj, T_WU, molecule_types=["water"], blocks=nb)

    # ---- self-diffusion, finite-size correction ----
    com = barycentric(traj, mol)
    dt_frame = float(np.diff(traj.times_ps)[0])
    edge = float(np.cbrt(traj.volumes_nm3().mean()))

    def diffusion(n_blocks: int, window: FitWindow) -> list[float]:
        vals = []
        for s in blocks(len(traj), n_blocks):
            m = self_msd(com[s])
            lags = np.arange(len(m)) * dt_frame
            vals.append(slope(lags, m, window) / 6 * c.NM2_PER_PS_IN_M2_PER_S * D_UNIT)
        return vals

    main_fit = diffusion(5, FitWindow(0.1, 0.5))
    out["D_pbc_1e-5_cm2_s"] = {
        **ms(main_fit),
        "blocks": 5,
        "window_fraction_of_block": [0.1, 0.5],
        "box_edge_nm": edge,
    }
    out["D_pbc_sensitivity_1e-5_cm2_s"] = {
        f"{nb_}blocks_window_{w.start}-{w.stop}": ms(diffusion(nb_, w))["mean"]
        for nb_ in (5, 10) for w in (FitWindow(0.1, 0.5), FitWindow(0.2, 0.6), FitWindow(0.1, 0.3))
    }  # fmt: skip

    # ---- viscosity of the NVT run, Green-Kubo ----
    tv, p, vol = read_tensor(VISC / "out/thermo.tsv", 200.0)
    gk = green_kubo(shear_components(p), float(np.median(np.diff(tv))), vol, T_VISC,
                    n_blocks=5, max_lag_ps=5.0)  # fmt: skip
    eta = gk["viscosity_Pa_s"]
    out["viscosity_mPa_s"] = {
        "mean": eta["mean"] * 1e3, "sem": eta["sem"] * 1e3, "blocks": 5, "max_lag_ps": 5.0,
        "whole_series": gk["viscosity_whole_series_Pa_s"] * 1e3, "skip_ps": 200.0,
        "temperature_K": T_VISC, "samples": gk["samples"], "dt_ps": gk["dt_ps"],
        "density_g_cm3": mass * c.AMU_IN_G / (vol * 1e-21),
    }  # fmt: skip
    eta_pa = eta["mean"]
    shift_ours = yeh_hummer_shift(T_WU, eta_pa, edge)
    shift_wu = yeh_hummer_shift(T_WU, eta_pa, BOX_WU_NM)
    sens = out["D_pbc_sensitivity_1e-5_cm2_s"].values()
    lo, hi = min(sens), max(sens)
    d_inf = out["D_pbc_1e-5_cm2_s"]["mean"] + shift_ours
    out["D_finite_size_1e-5_cm2_s"] = {
        "eta_used_mPa_s": eta_pa * 1e3,
        "yeh_hummer_shift_our_box": shift_ours,
        "D_infinity": d_inf,
        "D_infinity_range_over_fit_choices": [lo + shift_ours, hi + shift_ours],
        "wu_box_edge_nm": BOX_WU_NM, "yeh_hummer_shift_wu_box": shift_wu,
        "D_expected_in_wu_box": d_inf - shift_wu,
        "D_expected_in_wu_box_range": [lo + shift_ours - shift_wu, hi + shift_ours - shift_wu],
        "note": "assumes Wu's D is uncorrected for the box size; the temperature of D (298.16 K) "
                "differs from that of eta (300.2 K)",
    }  # fmt: skip

    # ---- traces for the figure: 1 ps means ----
    step = 10  # thermo rows of 0.1 ps
    k = len(t) // step * step
    tr = np.column_stack([
        t[:k].reshape(-1, step).mean(1), rho[:k].reshape(-1, step).mean(1),
        (u[:k] / n_mol).reshape(-1, step).mean(1)])  # fmt: skip
    np.savetxt(HERE / "data/traces_1ps.csv", tr, delimiter=",", fmt="%.6g",
               header="time_ps,density_g_cm3,potential_per_molecule_kJ_mol", comments="")  # fmt: skip

    # ---- provenance of the inputs ----
    files = [WU / "out/thermo.tsv", WU / "out/trajectory.h5", WU / "run.toml", WU / "status.json",
             VISC / "out/thermo.tsv", VISC / "run.toml", VISC / "status.json", GAS]  # fmt: skip
    manifest = {
        "_about": "Local inputs of analyze.py. Not in git; archive for the production set "
                  "(publication.md, open question 2). Paths are relative to the workspace.",
        "doi": None,
        "files": [{"path": str(f.relative_to(ROOT)), "bytes": f.stat().st_size,
                   "sha256": sha256(f)} for f in files if f.is_file()],
    }  # fmt: skip
    (HERE / "data/manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    out["inputs_manifest"] = "data/manifest.json"
    (HERE / "data/results.json").write_text(json.dumps(out, indent=1) + "\n")
    print(
        json.dumps(
            {
                k: out[k]
                for k in (
                    "density_g_cm3",
                    "hvap_wu_definition",
                    "r_OH_angstrom",
                    "theta_HOH_deg",
                    "mu_debye",
                    "D_pbc_1e-5_cm2_s",
                    "viscosity_mPa_s",
                    "D_finite_size_1e-5_cm2_s",
                )
            },
            indent=1,
        )
    )
    print(
        "epsilon",
        out["epsilon"]["epsilon"],
        out["epsilon"]["epsilon_blocks"]["mean"],
        out["epsilon"]["epsilon_blocks"]["sem"],
    )
    print("caleman", out.get("hvap_caleman_definition", {}).get("kcal_per_mol"))


if __name__ == "__main__":
    main()
