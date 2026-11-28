"""V-2: box-size series of the 1 M M1 box. D at infinite box size, eta from the Yeh-Hummer slope, kappa against L.

    HDF5_USE_FILE_LOCKING=FALSE ucmd-analysis/.venv/bin/python studies/2026-11-28_box-size-1M/analyze.py OUT.json
    ... analyze.py OUT.json --partial      # whatever runs are done, marked PRELIMINARY (no verdicts)

Everything here is fixed in README.md ("Analysis, fixed before the runs"). Per NVT run: molecular centres of mass in
the barycentric frame, the self-MSD of each species averaged over time origins, D = slope / 6 of a straight line over
the lag window [0.5, 2.5] ns (check window [1, 4] ns), the collective conductivity from the MSD of
sum(r_Li) - sum(r_PF6) over the same window (formal charges +-1), kappa_NE from D_Li + D_PF6. Across runs: one joint
Yeh-Hummer fit D_i(L) = Dinf_i - S/L with a slope S common to all species, weights proportional to the atom count,
errors by the jackknife over runs (all species of a run left out together). eta = xi k_B T / (6 pi S).
"""

from __future__ import annotations

import json
import math
import statistics as st
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
STUDIES = HERE.parent
sys.path.insert(0, str(STUDIES.parent / "ucmd-analysis/src"))
from ucmd_analysis import constants as c  # noqa: E402
from ucmd_analysis.io import system_from_json  # noqa: E402
from ucmd_analysis.msd import msd_series, self_msd  # noqa: E402
from ucmd_analysis.transport import FitWindow  # noqa: E402
from ucmd_analysis.transport import slope as fraction_slope  # noqa: E402
from ucmd_analysis.uncertainty import blocks  # noqa: E402

T_K = 293.15
SPECIES = ("Li", "PF6", "EC", "EMC")
CATION, ANION = "Li", "PF6"
SKIP_PS = 500.0  # of each NVT production
WINDOW_PS = (500.0, 2500.0)  # primary fit window (lags)
CHECK_PS = (1000.0, 4000.0)  # convergence check
HALF_WINDOW_PS = (250.0, 1250.0)  # drift check: the same window on each half and on the whole
BLOCKS = 5  # collective kappa: the trials' block estimator
N1_ATOMS = 7036
# the plan: (NVT study, system) per run; sizes from the atom counts
NVT = {
    "1x": ("2026-11-28_box-size-1M-nvt1x", ("m1_1x_s1", "m1_1x_s2", "m1_1x_s3")),
    "2x": ("2026-11-28_box-size-1M-nvt2x", ("m1_2x_s1", "m1_2x_s2")),
    "8x": ("2026-11-28_box-size-1M-nvt8x", ("m1_8x_s1", "m1_8x_s2")),
}
NPT = {  # density by size (reported): (study, run, skip ps, end ps)
    "1x": [("2026-11-24_parameter-sensitivity-1M", f"base_s{k}", 1500.0, 5000.0) for k in (1, 2, 3)],
    "2x": [("2026-11-28_box-size-1M", f"m1_2x_s{k}", 1000.0, 3000.0) for k in (1, 2)],
    "8x": [("2026-11-28_box-size-1M", f"m1_8x_s{k}", 1000.0, 3000.0) for k in (1, 2)],
}
RESOLVED_SIGMA = 3.0  # README: eta is "resolved" if S >= 3 SE
CHI2_95 = {1: 3.841, 2: 5.991, 3: 7.815}  # chi-square 95 % points (species consistency of the slope)


# -- per run --------------------------------------------------------------------------------------------------------


def barycentric_coms(path: Path, skip_ps: float, chunk: int = 200) -> dict:
    """Centres of mass (frames, molecules, 3) nm per species, barycentric, read in chunks of frames."""
    import h5py

    with h5py.File(path, "r") as fh:
        raw = fh["parameters/ucmd/system_json"][()]
        sysm = system_from_json(json.loads(raw.decode() if isinstance(raw, bytes) else str(raw)))
        pos = fh["particles/all/position"]
        t = np.asarray(pos["time"][()], dtype=np.float64)
        k0 = int(np.searchsorted(t, t[0] + skip_ps - 1e-6))
        steps = np.asarray(pos["step"][()])
        box_steps = np.asarray(fh["particles/all/box/edges/step"][()])
        box_all = np.asarray(fh["particles/all/box/edges/value"][()], dtype=np.float64)
        box = box_all[np.clip(np.searchsorted(box_steps, steps[k0:]), 0, len(box_all) - 1)]
        w_all = sysm.masses / sysm.masses.sum()
        parts: dict[str, list[np.ndarray]] = {n: [] for n in sysm.species}
        for a in range(k0, len(t), chunk):
            x = np.asarray(pos["value"][a : min(a + chunk, len(t))], dtype=np.float64)
            centre = np.einsum("fad,a->fd", x, w_all)
            for name, mol in sysm.species.items():
                w = mol.masses / mol.masses.sum()
                parts[name].append(np.einsum("fmad,a->fmd", x[:, mol.atoms, :], w) - centre[:, None, :])
    vols = np.abs(np.linalg.det(box))
    return {
        "times_ps": t[k0:],
        "coms": {n: np.concatenate(p) for n, p in parts.items()},
        "volume_nm3": float(vols.mean()),
        "volume_ptp_rel": float(np.ptp(vols) / vols.mean()),
        "n_atoms": sysm.n_atoms,
        "counts": {n: m.count for n, m in sysm.species.items()},
        "formal": {n: m.formal_charge for n, m in sysm.species.items()},
    }


def slope(lags_ps: np.ndarray, y: np.ndarray, window_ps: tuple[float, float]) -> float:
    """Least-squares slope of y against the lag over lags in [lo, hi] (y per ps)."""
    sel = (lags_ps >= window_ps[0] - 1e-9) & (lags_ps <= window_ps[1] + 1e-9)
    if sel.sum() < 3:
        raise ValueError(f"fewer than 3 lags in {window_ps} ps")
    return float(np.polyfit(lags_ps[sel], y[sel], 1)[0])


def beta(lags_ps: np.ndarray, msd: np.ndarray, window_ps: tuple[float, float]) -> float:
    """d ln MSD / d ln t across the window (1 if diffusive)."""
    i0, i1 = (int(np.argmin(np.abs(lags_ps - w))) for w in window_ps)
    return float(math.log(msd[i1] / msd[i0]) / math.log(lags_ps[i1] / lags_ps[i0]))


def diffusion(com: np.ndarray, dt_ps: float, window_ps: tuple[float, float]) -> float:
    """m2/s from the time-origin averaged self-MSD of (frames, molecules, 3) in nm."""
    m = self_msd(com)
    return slope(np.arange(len(m)) * dt_ps, m, window_ps) / 6.0 * c.NM2_PER_PS_IN_M2_PER_S


def kappa_blocks(com_cat: np.ndarray, com_an: np.ndarray, dt_ps: float, volume_nm3: float,
                 n_blocks: int = BLOCKS) -> dict:  # fmt: skip
    """The transport trials' estimator (ucmd-analyze transport defaults: 5 blocks, a straight line over 10-50 % of
    a block's lags, formal charges +-1), block means: kappa = e^2/(6 k_B T V) d/dt <|Delta(sum r_+ - sum r_-)|^2>,
    kappa_NE from the blocks' D_+ + D_-, and the blocks' D_+ and D_-."""
    kt = c.BOLTZMANN_J_PER_K * T_K
    vol_m3 = volume_nm3 * c.NM_IN_M**3
    window = FitWindow()
    k, kne, dc, da = [], [], [], []
    for b in blocks(len(com_cat), n_blocks):
        lags = np.arange(b.stop - b.start) * dt_ps
        m = msd_series(com_cat[b].sum(axis=1) - com_an[b].sum(axis=1))
        k.append(c.ELEMENTARY_CHARGE_C**2 * fraction_slope(lags, m, window) * c.NM2_PER_PS_IN_M2_PER_S
                 / (6.0 * kt * vol_m3))  # fmt: skip
        d = [fraction_slope(lags, self_msd(x[b]), window) / 6.0 * c.NM2_PER_PS_IN_M2_PER_S for x in (com_cat, com_an)]
        dc.append(d[0])
        da.append(d[1])
        kne.append(kappa_ne(com_cat.shape[1] / vol_m3, d[0], d[1]))
    return {"kappa": st.fmean(k), "kappa_NE": st.fmean(kne), "D_cat": st.fmean(dc), "D_an": st.fmean(da)}


def kappa_ne(pairs_per_m3: float, d_cat: float, d_an: float) -> float:
    """S/m, formal charges +-1."""
    return c.ELEMENTARY_CHARGE_C**2 * pairs_per_m3 * (d_cat + d_an) / (c.BOLTZMANN_J_PER_K * T_K)


def run_metrics(path: Path) -> dict:
    data = barycentric_coms(path, SKIP_PS)
    t, coms, vol = data["times_ps"], data["coms"], data["volume_nm3"]
    dt = float(np.median(np.diff(t)))
    lags = np.arange(len(t)) * dt
    out = {"n_atoms": data["n_atoms"], "L_nm": vol ** (1 / 3), "volume_nm3": vol,
           "volume_ptp_rel": data["volume_ptp_rel"], "analysed_ps": float(t[-1] - t[0]), "frame_ps": dt,
           "pairs_per_m3": data["counts"][CATION] / (vol * c.NM_IN_M**3)}  # fmt: skip
    half = len(t) // 2
    for n in SPECIES:
        m = self_msd(coms[n])
        out[f"D_{n}"] = slope(lags, m, WINDOW_PS) / 6.0 * c.NM2_PER_PS_IN_M2_PER_S
        out[f"D_{n}_check"] = slope(lags, m, CHECK_PS) / 6.0 * c.NM2_PER_PS_IN_M2_PER_S
        out[f"beta_{n}"] = beta(lags, m, WINDOW_PS)
        d_all = diffusion(coms[n], dt, HALF_WINDOW_PS)
        d1, d2 = diffusion(coms[n][:half], dt, HALF_WINDOW_PS), diffusion(coms[n][half:], dt, HALF_WINDOW_PS)
        out[f"drift_{n}_pct"] = 100.0 * (d2 - d1) / d_all
    out["kappa_NE"] = kappa_ne(out["pairs_per_m3"], out[f"D_{CATION}"], out[f"D_{ANION}"])  # primary window
    kb = kappa_blocks(coms[CATION], coms[ANION], dt, vol)
    out["kappa"], out["kappa_NE_blocks"] = kb["kappa"], kb["kappa_NE"]
    out[f"D_{CATION}_blocks"], out[f"D_{ANION}_blocks"] = kb["D_cat"], kb["D_an"]
    return out


def trial_protocol(path: Path) -> dict:
    """The 1x runs analysed as the transport trials were (ucmd-analyze transport defaults: 5 blocks, fit 10-50 %
    of a block), for comparison with the NPT numbers of the scan's base runs; reported, not used."""
    from ucmd_analysis.io import read_h5md
    from ucmd_analysis.transport import transport

    head = read_h5md(path, stop=2)
    k = int(np.ceil(SKIP_PS / float(head.times_ps[1] - head.times_ps[0])))
    tr = transport(read_h5md(path, start=k), T_K, CATION, ANION)
    keys = [f"D_{n}_m2_per_s" for n in SPECIES] + ["kappa_NE_S_per_m", "kappa_S_per_m"]
    return {key: tr[key]["mean"] for key in keys}


# -- across runs ----------------------------------------------------------------------------------------------------


def joint_fit(runs: list[dict], species=SPECIES) -> dict:
    """D_i,r = A_i - S x_r (x = 1/L in 1/nm) with S common to all species. Weights w_r = N_atoms / 7036 (per-run
    variance taken as proportional to 1/N), scaled per species by 1/s_i^2, s_i^2 the weighted residual variance of
    that species' own line. S in m2/s nm, A_i in m2/s."""
    x = np.array([1.0 / r["L_nm"] for r in runs])
    w = np.array([r["n_atoms"] / N1_ATOMS for r in runs])
    if len(set(np.round(x, 6))) < 2 or len(runs) < 3:
        raise ValueError("the fit needs at least two box sizes and three runs")
    own, num, den = {}, 0.0, 0.0
    for n in species:
        y = np.array([r[f"D_{n}"] for r in runs])
        xm, ym = np.average(x, weights=w), np.average(y, weights=w)
        sxx = float((w * (x - xm) ** 2).sum())
        s_i = -float((w * (x - xm) * (y - ym)).sum()) / sxx
        res = y - (ym + s_i * xm) + s_i * x
        dof = len(runs) - 2
        var = float((w * res**2).sum()) / dof if dof > 0 else float("nan")
        own[n] = {"S": s_i, "A": ym + s_i * xm, "resid_var": var, "xm": xm, "ym": ym, "sxx": sxx}
        scale = 1.0 / var if var > 0 and math.isfinite(var) else 1.0
        num += -scale * float((w * (x - xm) * (y - ym)).sum())
        den += scale * sxx
    s_joint = num / den
    return {"S": s_joint, "A": {n: own[n]["ym"] + s_joint * own[n]["xm"] for n in species},
            "S_own": {n: own[n]["S"] for n in species}, "A_own": {n: own[n]["A"] for n in species}}  # fmt: skip


def jackknife(runs: list[dict], estimator) -> tuple[dict, dict]:
    """Estimate on all runs and its jackknife SE (leave one run out); `estimator` returns a flat dict of floats."""
    full = estimator(runs)
    loo = []
    for k in range(len(runs)):
        try:
            loo.append(estimator(runs[:k] + runs[k + 1 :]))
        except ValueError:  # a leave-one-out set with a single size: that run cannot be left out
            continue
    n = len(loo)
    se = {}
    for key in full:
        vals = [d[key] for d in loo]
        mean = sum(vals) / n
        se[key] = math.sqrt((n - 1) / n * sum((v - mean) ** 2 for v in vals)) if n > 1 else float("nan")
    return full, se


def flat_estimates(runs: list[dict]) -> dict:
    """Every across-run number whose error the jackknife gives."""
    f = joint_fit(runs)
    out = {"S": f["S"], **{f"Dinf_{n}": f["A"][n] for n in SPECIES}, **{f"S_own_{n}": f["S_own"][n] for n in SPECIES}}
    n_pairs = st.fmean(r["pairs_per_m3"] for r in runs)
    out["kappa_NE_inf"] = kappa_ne(n_pairs, f["A"][CATION], f["A"][ANION])
    k = kappa_line(runs)
    out["kappa_intercept"], out["kappa_slope"] = k["intercept"], k["slope"]
    out["kappa_mean"] = st.fmean(r["kappa"] for r in runs)
    # kappa / kappa_NE with both from the same block estimator; kappa_NE corrected by the fitted Yeh-Hummer shift
    # of D_+ and D_- (2 S / L: the shift does not depend on the species or, at these lags, on the window)
    kt = c.BOLTZMANN_J_PER_K * T_K
    ne_inf = [r["kappa_NE_blocks"] + c.ELEMENTARY_CHARGE_C**2 * r["pairs_per_m3"] * 2 * f["S"] / r["L_nm"] / kt
              for r in runs]  # fmt: skip
    out["kappa_NE_blocks_inf"] = st.fmean(ne_inf)
    out["ratio_uncorrected"] = out["kappa_mean"] / st.fmean(r["kappa_NE_blocks"] for r in runs)
    out["ratio_corrected"] = out["kappa_mean"] / out["kappa_NE_blocks_inf"]
    out["ratio_corrected_intercept"] = out["kappa_intercept"] / out["kappa_NE_blocks_inf"]
    return out


def kappa_line(runs: list[dict]) -> dict:
    """kappa = kappa_0 + b / L, unweighted (the collective noise does not fall with N)."""
    x = np.array([1.0 / r["L_nm"] for r in runs])
    y = np.array([r["kappa"] for r in runs])
    if len(set(np.round(x, 6))) < 2:
        raise ValueError("needs two sizes")
    b, a = np.polyfit(x, y, 1)
    return {"intercept": float(a), "slope": float(b)}


def eta_from_slope(s_m2_s_nm: float, se: float) -> dict:
    """eta = xi k_B T / (6 pi S), S in m3/s; mPa s, with the interval from S -+ 2 SE (upper end open if S - 2 SE
    <= 0)."""
    kt = c.BOLTZMANN_J_PER_K * T_K

    def eta(s: float) -> float:
        return c.YEH_HUMMER_XI_CUBIC * kt / (6.0 * math.pi * s * c.NM_IN_M) * 1e3

    lo_s, hi_s = s_m2_s_nm - 2 * se, s_m2_s_nm + 2 * se
    return {
        "eta_mPa_s": eta(s_m2_s_nm) if s_m2_s_nm > 0 else float("inf"),
        "eta_low_mPa_s": eta(hi_s) if hi_s > 0 else float("inf"),
        "eta_high_mPa_s": eta(lo_s) if lo_s > 0 else float("inf"),
        "rel_se": se / s_m2_s_nm if s_m2_s_nm > 0 else float("inf"),
        "resolved": s_m2_s_nm >= RESOLVED_SIGMA * se,
    }


def species_chi2(est: dict, se: dict) -> dict:
    """Are the per-species slopes consistent with the common one?"""
    chi2 = sum(((est[f"S_own_{n}"] - est["S"]) / se[f"S_own_{n}"]) ** 2 for n in SPECIES)
    dof = len(SPECIES) - 1
    return {"chi2": chi2, "dof": dof, "consistent": chi2 <= CHI2_95[dof]}


def size_of(run: dict) -> str:
    k = round(run["n_atoms"] / N1_ATOMS)
    return f"{k}x"


def per_size(runs: list[dict]) -> dict:
    out = {}
    for size in sorted({size_of(r) for r in runs}, key=lambda s: int(s[:-1])):
        rs = [r for r in runs if size_of(r) == size]
        row = {"runs": len(rs), "L_nm": st.fmean(r["L_nm"] for r in rs)}
        for key in [f"D_{n}" for n in SPECIES] + [f"D_{n}_check" for n in SPECIES] + ["kappa", "kappa_NE",
                                                                                        "kappa_NE_blocks"]:
            v = [r[key] for r in rs]
            row[key] = {"mean": st.fmean(v), "se": st.stdev(v) / math.sqrt(len(v)) if len(v) > 1 else float("nan")}
        out[size] = row
    return out


def npt_density(study: str, run: str, skip: float, end: float) -> dict | None:
    """g/cm3 from the thermo volumes and the package masses; None if the run is not done."""
    base = STUDIES / study
    status = base / "runs" / run / "T20C/status.json"
    if not status.exists() or json.loads(status.read_text()).get("state") != "done":
        return None
    pkg = base / "systems" / run / "minimized.ucsys"
    if not pkg.exists():
        return None
    doc = json.loads((pkg / "system.json").read_text())
    mass = sum(k["count"] * sum(a["mass_amu"] for a in doc["molecule_types"][k["molecule_type"]]["atoms"])
               for k in doc["components"])  # fmt: skip
    rows: dict[int, float] = {}
    with (base / "runs" / run / "T20C/out/thermo.tsv").open() as fh:
        names = fh.readline().lstrip("# ").strip().split("\t")
        i_step, i_t, i_v = (names.index(n) for n in ("step", "time_ps", "volume_nm3"))
        for line in fh:
            f = line.split("\t")
            if float(f[i_t]) > skip:
                rows[int(f[i_step])] = float(f[i_v])
    v = [rows[k] for k in sorted(rows)]
    rho = [mass * c.AMU_IN_G / (x * c.NM3_IN_CM3) for x in v]
    half = len(rho) // 2
    return {"rho": st.fmean(rho), "halves_pct": 100 * (st.fmean(rho[half:]) / st.fmean(rho[:half]) - 1)}


def main(out_path: str, partial: bool) -> None:
    runs, missing = [], []
    for size, (study, systems) in NVT.items():
        for s in systems:
            run = STUDIES / study / "runs" / s / "T20C"
            status = run / "status.json"
            if not status.exists() or json.loads(status.read_text()).get("state") != "done":
                missing.append(f"{study}/{s}")
                continue
            r = run_metrics(run / "out/trajectory.h5")
            r.update({"run": f"{study}/{s}", "size": size})
            if size == "1x":
                r["trial_protocol"] = trial_protocol(run / "out/trajectory.h5")
            runs.append(r)
            print(f"{r['run']}: L {r['L_nm']:.4f} nm  D_Li {r['D_Li'] * 1e11:.2f}  D_EMC {r['D_EMC'] * 1e11:.2f}  "
                  f"kappa {r['kappa']:.3f}  kappa_NE {r['kappa_NE']:.3f}", flush=True)  # fmt: skip
    if missing and not partial:
        raise SystemExit(f"not finished: {missing} (use --partial for a PRELIMINARY look)")
    result = {"preliminary": bool(missing), "not_finished": missing, "runs": runs, "per_size": per_size(runs),
              "density_npt": {size: [npt_density(*a) for a in args] for size, args in NPT.items()},
              "windows_ps": {"fit": WINDOW_PS, "check": CHECK_PS, "drift": HALF_WINDOW_PS, "skip": SKIP_PS}}  # fmt: skip
    try:
        est, se = jackknife(runs, flat_estimates)
    except ValueError as exc:
        result["fit"] = f"no fit: {exc}"
    else:
        result["fit"] = {"estimate": est, "jackknife_se": se, "eta": eta_from_slope(est["S"], se["S"]),
                         "species": species_chi2(est, se),
                         "kappa_size": {"slope_per_inv_nm": est["kappa_slope"], "se": se["kappa_slope"],
                                        "resolved": abs(est["kappa_slope"]) > 2 * se["kappa_slope"]}}  # fmt: skip
        e = result["fit"]["eta"]
        print(f"S = {est['S']:.3e} +- {se['S']:.3e} m2/s nm -> eta = {e['eta_mPa_s']:.2f} mPa s "
              f"[{e['eta_low_mPa_s']:.2f}, {e['eta_high_mPa_s']:.2f}] (2 SE), resolved: {e['resolved']}")  # fmt: skip
        for n in SPECIES:
            print(f"Dinf_{n} = {est[f'Dinf_{n}'] * 1e11:.2f} +- {se[f'Dinf_{n}'] * 1e11:.2f} e-11 m2/s"
                  f"  (own slope {est[f'S_own_{n}']:.2e} +- {se[f'S_own_{n}']:.2e})")  # fmt: skip
        print(f"kappa_NE_inf = {est['kappa_NE_inf']:.3f} +- {se['kappa_NE_inf']:.3f} S/m; kappa mean "
              f"{est['kappa_mean']:.3f} +- {se['kappa_mean']:.3f}; kappa/kappa_NE {est['ratio_uncorrected']:.2f}, "
              f"corrected {est['ratio_corrected']:.2f} +- {se['ratio_corrected']:.2f}")  # fmt: skip
    Path(out_path).write_text(json.dumps(result, indent=1, default=float) + "\n")
    print("PRELIMINARY, not finished:" if missing else "all runs done", missing)


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3) or (len(sys.argv) == 3 and sys.argv[2] != "--partial"):
        raise SystemExit(__doc__)
    main(sys.argv[1], len(sys.argv) == 3)
