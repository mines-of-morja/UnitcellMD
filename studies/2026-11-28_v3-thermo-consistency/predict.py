"""V-3: predictions from data that existed before any V-3 run (no V-3 output is read here).

    ucmd-analysis/.venv/bin/python studies/2026-11-28_v3-thermo-consistency/predict.py [OUT.json]

Theory (README, "Why"): velocity Verlet samples, to O(dt^2), the canonical ensemble of its shadow Hamiltonian
H~ = H + dt^2 [ p.M^-1 U'' M^-1 p / 12 - U'.M^-1 U' / 24 ]. Its on-step kinetic temperature is lower than the
temperature T* of the slow degrees of freedom by (2/3) dT_half, where dT_half = dt^2 <sum F^2/(4m)>/(N_dof k)
is the half-step minus on-step kinetic temperature (tconf.py writes it at dt = 1 fs). A thermostat that pins
the on-step kinetic energy at T0 (the engine's and the bridge's Nose-Hoover chain) therefore holds the slow
modes at T* = T0 + (2/3) dT_half. Langevin BAOAB samples configurations at T0 (exact for harmonic modes) and
shows an on-step temperature T0 - dT_half. OpenMM's MonteCarloBarostat accepts with the target T0, so with
the slow modes at T* it holds the true pressure at P0 + rho_mol k (T* - T0). C-rescale with the molecular
pressure (engine main) uses the centre-of-mass kinetic energy, which is at T*: no such term. The atomic
on-step pressure is low by N_dof k dT_half / (3V) (SC-3).
"""

from __future__ import annotations

import json
import statistics as st
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
TCONF = ROOT / "docs/research/timestep/tconf"
# CODATA 2018 (exact SI values)
K_B = 1.380649e-23 * 6.02214076e23 / 1000.0  # kJ mol-1 K-1
BAR_PER_KJMOL_NM3 = 1000.0 / 6.02214076e23 / 1e-27 / 1e5  # 16.6054 bar
GRAM_PER_AMU = 1e-3 / 6.02214076e23 * 1e3  # g per amu (1 g/mol / N_A)

SYSTEMS = {  # name: (tconf prefix, NPT runs at 1 fs whose volumes give kappa_T, target T in K)
    "1M": ("1M", [f"studies/2026-11-24_parameter-sensitivity-1M/runs/base_s{k}/T20C" for k in (1, 2, 3)], 293.15),
    "emc": ("emc", [f"studies/2026-11-25_timestep-emc-1fs/runs/emc_500_s{k}/T25C" for k in (1, 2, 3)], 298.15),
    "water": ("water", [f"studies/2026-11-25_water-npt-gpu/runs/spcfw_512_s{k}/T25.01C" for k in (1, 2, 3)], 298.16),
}  # fmt: skip
SKIP_PS = {"1M": 1500.0, "emc": 500.0, "water": 200.0}  # the skips of SC-1


def thermo(path: Path) -> dict[str, np.ndarray]:
    with path.open() as fh:
        names = fh.readline().lstrip("# ").strip().split("\t")
        rows = np.loadtxt(fh)
    return {n: rows[:, i] for i, n in enumerate(names)}


def package_counts(run_dir: Path) -> tuple[int, int, float]:
    """(atoms, molecules, total mass in amu) of the run's package."""
    toml = (run_dir / "run.toml").read_text()
    rel = next(line.split("=", 1)[1].strip().strip('"') for line in toml.splitlines() if line.startswith("system"))
    doc = json.loads((run_dir / rel / "system.json").read_text())
    types = doc["molecule_types"]
    n_mol = sum(c["count"] for c in doc["components"])
    n_atoms = sum(c["count"] * len(types[c["molecule_type"]]["atoms"]) for c in doc["components"])
    mass = sum(c["count"] * sum(a["mass_amu"] for a in types[c["molecule_type"]]["atoms"]) for c in doc["components"])
    return n_atoms, n_mol, mass


def half_step(prefix: str, step: str) -> list[float]:
    """dT_half at dt = 1 fs from tconf.py, one value per seed."""
    return [json.loads(f.read_text())["half-step minus on-step T (dt=1fs)"][0]
            for f in sorted(TCONF.glob(f"{prefix}_{step}_s*.json"))]  # fmt: skip


def main() -> None:
    out: dict = {}
    for name, (prefix, runs, t0) in SYSTEMS.items():
        hb1 = half_step(prefix, "1fs")
        hb05 = [x / 4.0 for x in half_step(prefix, "0p5fs")]  # written at dt = 1 fs from the 0.5 fs frames
        kappas, vols, rho_mol = [], [], []
        for r in runs:
            d = thermo(ROOT / r / "out/thermo.tsv")
            keep = (d["time_ps"] >= SKIP_PS[name]) & np.isfinite(d["volume_nm3"])
            v = d["volume_nm3"][keep]
            n_atoms, n_mol, mass = package_counts(ROOT / r)
            kappas.append(float(v.var(ddof=1) / (K_B * t0 * v.mean()) / BAR_PER_KJMOL_NM3))
            vols.append(float(v.mean()))
            rho_mol.append(n_mol / float(v.mean()))
        n_dof = 3 * n_atoms - 3
        kappa, vol, rmol = st.fmean(kappas), st.fmean(vols), st.fmean(rho_mol)
        row = {"atoms": n_atoms, "molecules": n_mol, "volume_nm3": vol, "kappa_T_per_bar": kappa,
               "kappa_T_seeds": kappas, "density_g_cm3": mass * GRAM_PER_AMU / (vol * 1e-21)}  # fmt: skip
        for label, hb in (("1fs", hb1), ("0p5fs", hb05)):
            h = st.fmean(hb)
            tstar = 2.0 / 3.0 * h
            row[label] = {
                "dT_half_K": h,
                "dT_half_seeds_K": hb,
                "T_slow_minus_T_onstep_K (NHC, NVE)": tstar,
                "T_onstep_minus_T0_K (BAOAB)": -h,
                "P_atomic_minus_P_molecular_bar": -n_dof * K_B * h / (3.0 * vol) * BAR_PER_KJMOL_NM3,
                "P_true_minus_P0_bar (MC barostat, NHC)": rmol * K_B * tstar * BAR_PER_KJMOL_NM3,
            }
        out[name] = row
    # SC-3 water arms (all at 1 fs, NHC tau 0.1 ps, same T0): density differences from the barostat's pressure alone
    w = out["water"]
    k = w["kappa_T_per_bar"]
    out["water_arms_prediction"] = {
        "rho_cpu_atomic_minus_cpu_molecular_pct": 100 * k * -w["1fs"]["P_atomic_minus_P_molecular_bar"],
        "rho_gpu_mc_minus_cpu_molecular_pct": 100 * k * w["1fs"]["P_true_minus_P0_bar (MC barostat, NHC)"],
        "note": "first order in kappa_T; C-rescale atomic holds the on-step atomic pressure at P0, so the true "
        "pressure is higher by -(P_atomic - P_molecular); the MC barostat accepts with T0 while the slow "
        "modes are at T*; C-rescale molecular uses the centre-of-mass kinetic energy (at T*)",
    }
    # 1 fs -> 0.5 fs density shift from T* and the MC term, with the model's own thermal expansion
    sc4 = json.loads((ROOT / "docs/research/density-c-T/sc4.json").read_text())
    rep = json.loads((ROOT / "docs/research/report/data.json").read_text())["solvent_densities"]
    alpha = {
        "1M": -sc4["drho_dT"]["value"] / out["1M"]["density_g_cm3"],
        "emc": -(rep["emc_40_on"]["rho"] - rep["emc_25_on"]["rho"]) / 15.0 / rep["emc_25_on"]["rho"],
    }
    for name, a in alpha.items():
        r = out[name]
        dts = r["1fs"]["T_slow_minus_T_onstep_K (NHC, NVE)"] - r["0p5fs"]["T_slow_minus_T_onstep_K (NHC, NVE)"]
        dp = r["1fs"]["P_true_minus_P0_bar (MC barostat, NHC)"] - r["0p5fs"]["P_true_minus_P0_bar (MC barostat, NHC)"]
        r["alpha_per_K"] = a
        r["rho_0p5_minus_1fs_pct"] = {"from_T_slow": 100 * a * dts, "from_MC_term": -100 * r["kappa_T_per_bar"] * dp,
                                      "total": 100 * (a * dts - r["kappa_T_per_bar"] * dp), "dT_slow_K": dts}  # fmt: skip
    # the target shift for the transport protocol test: T_set = T0 - (2/3) dT_half(1 fs) of the 1 M box
    out["1M"]["nhc_target_shift_T_set_K"] = 293.15 - out["1M"]["1fs"]["T_slow_minus_T_onstep_K (NHC, NVE)"]
    text = json.dumps(out, indent=1)
    print(text)
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(text + "\n")


if __name__ == "__main__":
    main()
