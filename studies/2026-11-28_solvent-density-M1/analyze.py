"""V-4: density of the salt-free M1 solvent and the apparent molar volume of LiPF6 with it (README: plan and reading).

    python3 analyze.py OUT.json        # standard library only

Reads the three runs of this study, SC-4's salt points (studies/2026-11-27_density-concentration-M1), SC-1's 1 M
points at 0.5 fs, the pure-solvent runs for the ideal-mixing estimate and the zeta probes of the 1 M scan. Every
step is fixed in README.md ("Reading, fixed before the runs"). Unfinished runs stop the script: no partial result.
"""

from __future__ import annotations

import importlib.util
import json
import math
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDIES = HERE.parent
ROOT = STUDIES.parent
DCT = ROOT / "docs/research/density-c-T"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sc4 = _load("sc4", STUDIES / "2026-11-27_density-concentration-M1/analyze.py")
av = _load("av", DCT / "apparent_volume.py")

SEEDS = ("m1_solvent_s1", "m1_solvent_s2", "m1_solvent_s3")
COND, SKIP_PS, END_PS = "T20C", 1000.0, 3000.0  # SC-4's window
T_K = 293.15
SETTLE_PCT = sc4.SETTLE_PCT  # 0.3 %, SC-4 criterion 3
# Salt points at 20 C and 0.5 fs (SC-4 and SC-1), as apparent_volume.py takes them
SALT = {
    "0.1 M": [(sc4.C_STUDY, "m1_0.1M", 1000.0, 3000.0)],
    "1 M": [("2026-11-25_timestep-1M-0p5fs", r, 1500.0, 5000.0) for r in ("base_s1", "base_s2", "base_s3")],
    "2 M": [(sc4.C_STUDY, "m1_2.0M", 1000.0, 3000.0)],
    "3 M": [(sc4.C_STUDY, "m1_3.0M", 1000.0, 3000.0)],
}
# Pure solvents for ideal mixing (README, reading 4): model run, its window, measured density (g/cm3)
# EC: model M1 (Caleman types), 39 C, 1 fs, window 0.5-2 ns as in that study; measured 1321.4 g/L at 312.15 K,
#     ledger caleman2012_ec_oplsaa (rho_exp, DIPPR via Caleman's SI).
# EMC: LigParGen, 25 C, 0.5 fs, the three SC-1 runs (docs/research/timestep/sc1.json); measured 1006.88 kg/m3 at
#     298.15 K, ledger density_dmc_emc_ec_fluid2018.
EC_RUN = ("2026-11-20_ec-opls-test", "ec_oplsaa_1000", "T39C", 500.0, 2000.0)
EC_MEASURED = 1.3214
EMC_MEASURED = 1.00688
SC1 = ROOT / "docs/research/timestep/sc1.json"
# zeta at 1 M (README, reading 6): probes of the 1 M scan (1 fs), the only zeta series at 1 M
ZETA_RUNS = {0.65: "zeta_0.65", 0.85: "zeta_0.85"}
SCAN = "2026-11-24_parameter-sensitivity-1M"


def mass_amu(package: Path) -> float:
    doc = json.loads((package / "system.json").read_text())
    return sum(
        c["count"] * sum(a["mass_amu"] for a in doc["molecule_types"][c["molecule_type"]]["atoms"])
        for c in doc["components"]
    )


def density(study: str, run: str, cond: str, skip: float, end: float) -> dict:
    """Mean density (g/cm3) after `skip` and the difference of the two halves (%), from the thermo volumes."""
    base = STUDIES / study
    m = mass_amu(base / "systems" / run / "minimized.ucsys")
    rho = [m * sc4.GRAM_PER_AMU / sc4.CM3_PER_NM3 / v for v in sc4.volumes(base / "runs" / run / cond, skip, end)]
    half = len(rho) // 2
    return {"rho": st.fmean(rho), "halves_pct": 100 * (st.fmean(rho[half:]) / st.fmean(rho[:half]) - 1)}


def settled(p: dict) -> bool:
    return abs(p["halves_pct"]) <= SETTLE_PCT


def mean_se(xs: list[float]) -> tuple[float, float]:
    return st.fmean(xs), (st.stdev(xs) / math.sqrt(len(xs)) if len(xs) > 1 else math.nan)


def line_with_se(xs: list[float], ys: list[float]) -> dict:
    """Least-squares line with the SE of intercept and slope from the residuals."""
    n = len(xs)
    b0, b1 = av.line(xs, ys)
    mx = st.fmean(xs)
    sxx = sum((x - mx) ** 2 for x in xs)
    s2 = sum((y - b0 - b1 * x) ** 2 for x, y in zip(xs, ys, strict=True)) / (n - 2)
    return {"intercept": b0, "slope": b1, "se_intercept": math.sqrt(s2 * (1 / n + mx * mx / sxx)),
            "se_slope": math.sqrt(s2 / sxx)}  # fmt: skip


def ideal_mixing(w_ec: float, ec_model: float, ec_meas: float, emc_model: float, emc_meas: float) -> float:
    """Relative error (%) of an ideal mixture of the model's pure solvents against an ideal mixture of the real
    ones, at weight fraction w_ec: 1/rho = w_EC/rho_EC + w_EMC/rho_EMC. Assumes each solvent's relative error does
    not depend on T (the pure runs are at 39 and 25 C) and equal excess volumes in model and reality."""
    real = 1.0 / (w_ec / ec_meas + (1 - w_ec) / emc_meas)
    model = 1.0 / (w_ec / ec_model + (1 - w_ec) / emc_model)
    return 100 * (model / real - 1)


def v_phi_se(rho: float, se_rho: float, c: float, rho0: float, se_rho0: float, m: float) -> tuple[float, float]:
    """V_phi (cm3/mol) and its SE from the SEs of rho and rho0 (independent runs):
    dV/drho = -1000/(c rho0), dV/drho0 = (1000/c - V)/rho0."""
    v = av.v_phi(rho, c, rho0, m)
    d_rho, d_rho0 = -1000.0 / (c * rho0), (1000.0 / c - v) / rho0
    return v, math.hypot(d_rho * se_rho, d_rho0 * se_rho0)


def salt_points() -> dict:
    """rho, its SE and c of the four 20 C points; single runs get the per-run SD of the three 1 M seeds."""
    raw = {k: [sc4.point(*r[:2], COND, *r[2:]) for r in runs] for k, runs in SALT.items()}
    sd_rel = st.stdev(p["rho"] for p in raw["1 M"]) / st.fmean(p["rho"] for p in raw["1 M"])
    out = {}
    for k, pts in raw.items():
        rho, se = mean_se([p["rho"] for p in pts])
        out[k] = {"rho": rho, "se_rho": se if len(pts) > 1 else rho * sd_rel, "runs": len(pts),
                  "c_mol_l": st.fmean(p["c_mol_l"] for p in pts)}  # fmt: skip
    return out


def main(out_path: str) -> None:
    seeds = {s: density(HERE.name, s, COND, SKIP_PS, END_PS) for s in SEEDS}
    good = [p["rho"] for p in seeds.values() if settled(p)]
    if len(good) < 2:
        raise SystemExit(f"fewer than two settled seeds: {seeds} (README reading 1: unresolved)")
    rho0, se0 = mean_se(good)
    exp0 = sc4.reference(0.0, T_K)
    m_salt = av.salt_molar_mass(av.PACKAGE)
    salt = salt_points()
    keys = list(salt)
    fit = line_with_se([salt[k]["c_mol_l"] for k in keys], [salt[k]["rho"] for k in keys])
    z_line = (rho0 - fit["intercept"]) / math.hypot(se0, fit["se_intercept"])
    # ideal mixing of the model's pure solvents (README reading 4)
    pkg = STUDIES / HERE.name / "systems" / SEEDS[0] / "minimized.ucsys"
    doc = json.loads((pkg / "system.json").read_text())
    per = {c["molecule_type"]: c["count"] * sum(a["mass_amu"] for a in doc["molecule_types"][c["molecule_type"]]["atoms"])
           for c in doc["components"]}  # fmt: skip
    w_ec = per["EC"] / (per["EC"] + per["EMC"])
    ec_model = density(*EC_RUN)["rho"]
    emc_model = st.fmean(r["rho"] for r in json.loads(SC1.read_text())["density"]["EMC"]["runs"]["0.5"])
    ideal_pct = ideal_mixing(w_ec, ec_model, EC_MEASURED, emc_model, EMC_MEASURED)
    dev_pct = 100 * (rho0 / exp0 - 1)
    # V_phi with the measured rho0 (reading 5), and with the extrapolated intercept for comparison
    table = {}
    for k in keys:
        p = salt[k]
        v, se = v_phi_se(p["rho"], p["se_rho"], p["c_mol_l"], rho0, se0, m_salt)
        v_old, _ = v_phi_se(p["rho"], p["se_rho"], p["c_mol_l"], fit["intercept"], 0.0, m_salt)
        table[k] = {**p, "v_phi_cm3_mol": v, "se_v_phi": se, "v_phi_with_intercept_cm3_mol": v_old}
    exp_v = (m_salt - 1000.0 * sc4.P2) / exp0
    # zeta at 1 M (reading 6): V_phi of the 0.5 fs 1 M point, slope from the 1 fs probes, all with the measured rho0
    probes = {z: sc4.point(SCAN, r, COND, 1500.0, 5000.0) for z, r in ZETA_RUNS.items()}
    vz = {z: av.v_phi(p["rho"], p["c_mol_l"], rho0, m_salt) for z, p in probes.items()}
    dv_dz = (vz[0.85] - vz[0.65]) / 0.20
    zeta_star = 0.75 + (exp_v - table["1 M"]["v_phi_cm3_mol"]) / dv_dz
    result = {
        "seeds": {s: {**p, "settled": settled(p)} for s, p in seeds.items()},
        "rho0": {"mean": rho0, "se": se0, "seeds_used": len(good)},
        "landesfeind_c0_20C": exp0,
        "rho0_vs_fit_pct": dev_pct,
        "extrapolated_intercept": fit,
        "rho0_minus_intercept": rho0 - fit["intercept"],
        "rho0_minus_intercept_z": z_line,
        "intercept_consistent": abs(z_line) <= 2.0,
        "ideal_mixing": {"w_EC": w_ec, "EC_model_39C_1fs": ec_model, "EC_measured": EC_MEASURED,
                         "EMC_model_25C_0p5fs": emc_model, "EMC_measured": EMC_MEASURED,
                         "predicted_pct": ideal_pct, "measured_minus_predicted_pct": dev_pct - ideal_pct},
        "salt_molar_mass_g_mol": m_salt,
        "v_phi_experiment_cm3_mol": exp_v,
        "v_phi": table,
        "zeta_1M": {"v_phi_probes_1fs": {f"{z:.2f}": v for z, v in vz.items()}, "dv_phi_dzeta": dv_dz,
                    "v_phi_0p75_0p5fs": table["1 M"]["v_phi_cm3_mol"], "zeta_star": zeta_star},
    }
    Path(out_path).write_text(json.dumps(result, indent=1) + "\n")
    for s, p in seeds.items():
        print(f"{s}: rho {p['rho']:.5f}  halves {p['halves_pct']:+.3f} %  {'settled' if settled(p) else 'NOT settled'}")
    print(f"rho0 = {rho0:.5f} +- {se0:.5f} g/cm3 ({len(good)} seeds); fit at c = 0: {exp0:.5f} ({dev_pct:+.2f} %)")
    print(f"extrapolated intercept {fit['intercept']:.5f} +- {fit['se_intercept']:.5f}: difference "
          f"{rho0 - fit['intercept']:+.5f} ({z_line:+.1f} combined SE)")  # fmt: skip
    print(f"ideal mixing predicts {ideal_pct:+.2f} %, measured {dev_pct:+.2f} %")
    for k, r in table.items():
        print(f"V_phi {k:6s} {r['v_phi_cm3_mol']:6.1f} +- {r['se_v_phi']:.1f} cm3/mol "
              f"(with the intercept {r['v_phi_with_intercept_cm3_mol']:.1f}); experiment {exp_v:.1f}")  # fmt: skip
    print(f"zeta* at 1 M = {zeta_star:.3f} (dV_phi/dzeta {dv_dz:.1f} cm3/mol)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
