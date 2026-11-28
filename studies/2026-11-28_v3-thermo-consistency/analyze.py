"""V-3 analysis: kinetic temperatures, the half-step temperature, atomic minus molecular pressure, drift, density.

    HDF5_USE_FILE_LOCKING=FALSE ucmd-analysis/.venv/bin/python studies/2026-11-28_v3-thermo-consistency/analyze.py \
        [OUT.json]                     # every arm that has output; criteria of README "Criteria"

Per frame (positions, on-step velocities and forces of the H5MD trajectory, canonical order):
- T_on   = sum m (v - V_sys)^2 / (N_dof k), N_dof = 3N - 3 - N_constraints (the displayed temperature);
- T_com  = sum_I M_I (V_I - V_sys)^2 / ((3 N_mol - 3) k), the molecule centres (slow degrees of freedom);
- dT_half = dt^2 sum F^2/(4m) / (N_dof k), the half-step minus on-step kinetic temperature (with constraints the
  provider forces plus an approximate constraint force, see `constraint_forces`);
- P_atomic - P_molecular = [2 K_int + sum_i (r_i - R_I).F_i] / (3V), molecules unwrapped around their first atom,
  and its prediction -dt^2 [sum F_i^2/(4 m_i) - sum F_I^2/(4 M_I)] / (3V) (README "Why").
Errors: SE of the mean from BLOCKS contiguous blocks of the frames after the skip.
Numpy and h5py only (the ucmd-analysis venv).
"""

from __future__ import annotations

import json
import math
import sys
import tomllib
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from arms import ARMS, T0_K

# CODATA 2018 (exact SI values)
K_B = 1.380649e-23 * 6.02214076e23 / 1000.0  # kJ mol-1 K-1
BAR_PER_KJMOL_NM3 = 1000.0 / 6.02214076e23 / 1e-27 / 1e5
G_PER_AMU = 1.0 / 6.02214076e23
SKIP_PS = 100.0  # fresh velocities at t = 0 (README "Analysis")
SKIP_NPT_PS = 500.0
BLOCKS = 10


# -- pure functions (tested) --------------------------------------------------------------------------------------


def block_se(x: np.ndarray, blocks: int = BLOCKS) -> tuple[float, float]:
    """Mean and the SE of the mean from `blocks` contiguous blocks."""
    x = np.asarray(x, dtype=float)
    parts = np.array_split(x, blocks)
    means = np.array([p.mean() for p in parts if len(p)])
    return float(x.mean()), float(means.std(ddof=1) / math.sqrt(len(means)))


def molecules(mol: np.ndarray) -> tuple[int, np.ndarray]:
    n = int(mol.max()) + 1
    first = np.array([int(np.argmax(mol == k)) for k in range(n)])
    return n, first


def unwrap(x: np.ndarray, box_diag: np.ndarray, mol: np.ndarray, first: np.ndarray) -> np.ndarray:
    """Each molecule whole around its first atom (minimum image, orthorhombic cell)."""
    ref = x[first[mol]]
    return ref + (x - ref) - box_diag * np.round((x - ref) / box_diag)


def constraint_forces(x: np.ndarray, f: np.ndarray, m: np.ndarray, pairs: np.ndarray) -> np.ndarray:
    """Approximate constraint forces: each constraint on its own cancels the relative acceleration of its two atoms
    along the bond (the centripetal term and the coupling of constraints that share an atom are neglected). Used only
    for the dT_half and pressure estimates of the constrained arms, which are reported, not judged."""
    g = np.zeros_like(f)
    if len(pairs) == 0:
        return g
    i, j = pairs[:, 0], pairs[:, 1]
    u = x[j] - x[i]
    u /= np.linalg.norm(u, axis=1)[:, None]
    a_rel = ((f[j] / m[j, None] - f[i] / m[i, None]) * u).sum(1)
    mu = m[i] * m[j] / (m[i] + m[j])
    lam = -mu * a_rel
    np.add.at(g, j, lam[:, None] * u)
    np.add.at(g, i, -lam[:, None] * u)
    return g


def frame_stats(x, v, f, box_diag, m, mol, n_mol, first, dt_ps, pairs=None) -> dict:
    """The per-frame quantities of the module docstring (nm, ps, amu, kJ/mol; temperatures in K, pressures in bar)."""
    x, v, f = (np.asarray(a, dtype=float) for a in (x, v, f))
    n = len(m)
    n_c = 0 if pairs is None else len(pairs)
    if n_c:
        f = f + constraint_forces(x, f, m, pairs)
    n_dof = 3 * n - 3 - n_c
    msum = m.sum()
    v = v - (m[:, None] * v).sum(0) / msum
    M = np.bincount(mol, m, n_mol)
    V = np.stack([np.bincount(mol, m * v[:, k], n_mol) for k in range(3)], 1) / M[:, None]
    F = np.stack([np.bincount(mol, f[:, k], n_mol) for k in range(3)], 1)
    xu = unwrap(x, box_diag, mol, first)
    R = np.stack([np.bincount(mol, m * xu[:, k], n_mol) for k in range(3)], 1) / M[:, None]
    two_k = float((m[:, None] * v * v).sum())
    two_k_com = float((M[:, None] * V * V).sum())
    w_int = float(((xu - R[mol]) * f).sum())
    vol = float(np.prod(box_diag))
    s_atoms = float((f * f / (4.0 * m[:, None])).sum())
    s_com = float((F * F / (4.0 * M[:, None])).sum())
    return {
        "T_on": two_k / (n_dof * K_B),
        "T_com": two_k_com / ((3 * n_mol - 3) * K_B),
        "dT_half": dt_ps**2 * s_atoms / (n_dof * K_B),
        "dP_atomic_minus_molecular_bar": (two_k - two_k_com + w_int) / (3.0 * vol) * BAR_PER_KJMOL_NM3,
        "dP_predicted_bar": -(dt_ps**2) * (s_atoms - s_com) / (3.0 * vol) * BAR_PER_KJMOL_NM3,
        "volume_nm3": vol,
    }


def drift_K_per_ns(t_ps: np.ndarray, e_kjmol: np.ndarray, n_dof: int) -> float:
    """Slope of the conserved energy as a temperature rate, 2 dE/dt / (N_dof k), in K/ns."""
    slope = np.polyfit(np.asarray(t_ps, float), np.asarray(e_kjmol, float), 1)[0]  # kJ/mol/ps
    return float(2.0 * slope * 1000.0 / (n_dof * K_B))


def density_g_cm3(total_mass_amu: float, volume_nm3: np.ndarray) -> np.ndarray:
    return total_mass_amu * G_PER_AMU / (np.asarray(volume_nm3, float) * 1e-21)


def constraint_pairs(system: dict) -> np.ndarray:
    """Global atom pairs of every constraint, in canonical order (spec system-package.md section 4)."""
    out, offset = [], 0
    for comp in system["components"]:
        mt = system["molecule_types"][comp["molecule_type"]]
        na = len(mt["atoms"])
        for _ in range(comp["count"]):
            out += [(offset + c["atoms"][0], offset + c["atoms"][1]) for c in mt.get("constraints", [])]
            offset += na
    return np.array(out, dtype=int).reshape(-1, 2)


# -- reading one arm ----------------------------------------------------------------------------------------------


def read_thermo(path: Path) -> dict[str, np.ndarray]:
    with path.open() as fh:
        names = fh.readline().lstrip("# ").strip().split("\t")
        rows = np.loadtxt(fh, ndmin=2)
    return {n: rows[:, i] for i, n in enumerate(names)}


def analyze_arm(d: Path, skip_ps: float = SKIP_PS) -> dict:
    import h5py

    cfg = tomllib.loads((d / "run.toml").read_text())
    dt_ps = cfg["run"]["timestep_fs"] * 1e-3
    th = cfg.get("thermostat")
    target = th["temperature_K"] if th else None
    out: dict = {"dt_fs": cfg["run"]["timestep_fs"], "thermostat": th, "barostat": "barostat" in cfg}
    thermo = read_thermo(d / "out/thermo.tsv")
    with h5py.File(d / "out/trajectory.h5", "r") as h:
        p = h["particles/all"]
        m = np.asarray(p["mass"][:], float)
        m = m if m.ndim == 1 else m[0]
        mol = np.asarray(p["molecule_index"][:], int)
        system = json.loads(h["parameters/ucmd/system_json"][()])
        pairs = constraint_pairs(system)
        n_dof = 3 * len(m) - 3 - len(pairs)
        out["n_dof"], out["constraints"] = n_dof, len(pairs)
        keep_t = thermo["time_ps"] >= (SKIP_NPT_PS if out["barostat"] else skip_ps)
        out["T_displayed_K"] = block_se(thermo["temperature_K"][keep_t])
        out["frames"] = 0
        if "velocity" in p and "force" in p:
            n_mol, first = molecules(mol)
            t = p["position/time"][:]
            idx = np.where(t >= skip_ps)[0]
            rows = []
            for i in idx:
                box = np.asarray(p["box/edges/value"][i], float)
                rows.append(frame_stats(p["position/value"][i], p["velocity/value"][i], p["force/value"][i],
                                        np.diag(box), m, mol, n_mol, first, dt_ps, pairs if len(pairs) else None))  # fmt: skip
            out["frames"] = len(rows)
            series = {k: np.array([r[k] for r in rows]) for k in rows[0]}
            for k in ("T_on", "T_com", "dT_half", "dP_atomic_minus_molecular_bar", "dP_predicted_bar"):
                out[k] = block_se(series[k])
            # paired per-frame differences (their noise is smaller than the sum of the two)
            out["T_com_minus_T_on"] = block_se(series["T_com"] - series["T_on"])
            out["T_com_minus_T_on_minus_two_thirds_dT_half"] = block_se(
                series["T_com"] - series["T_on"] - 2.0 / 3.0 * series["dT_half"]
            )
            if target is not None:
                out["T_com_minus_target"] = block_se(series["T_com"] - target)
                out["T_on_minus_target_plus_dT_half"] = block_se(series["T_on"] - target + series["dT_half"])
            out["dP_minus_predicted_bar"] = block_se(
                series["dP_atomic_minus_molecular_bar"] - series["dP_predicted_bar"]
            )
            half = len(rows) // 2
            out["T_com_halves"] = [float(series["T_com"][:half].mean()), float(series["T_com"][half:].mean())]
        if th is None:
            out["drift_K_per_ns"] = drift_K_per_ns(thermo["time_ps"][keep_t], thermo["conserved_energy_kjmol"][keep_t],
                                                   n_dof)  # fmt: skip
        if out["barostat"]:
            rho = density_g_cm3(float(m.sum()), thermo["volume_nm3"][keep_t])
            out["density_g_cm3"] = block_se(rho)
            out["density_halves"] = [float(rho[: len(rho) // 2].mean()), float(rho[len(rho) // 2 :].mean())]
    return out


# -- criteria (README "Criteria") ---------------------------------------------------------------------------------


def within(x: tuple[float, float], target: float = 0.0, k: float = 2.0) -> bool:
    return abs(x[0] - target) <= k * x[1]


def diff(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    return a[0] - b[0], math.hypot(a[1], b[1])


def criteria(res: dict) -> dict:
    c: dict = {}
    get = res.get
    # C1 integrator: NVE shows the offset (2/3) dT_half with no thermostat
    for name in ("nve-1fs", "nve-0p5fs"):
        if name in res and res[name].get("frames"):
            r = res[name]
            c[f"C1 {name}: T_com - T_on = (2/3) dT_half"] = {
                "measured": r["T_com_minus_T_on"], "predicted": 2 / 3 * r["dT_half"][0],
                "pass": within(r["T_com_minus_T_on_minus_two_thirds_dT_half"]),
                "offset_resolved": r["T_com_minus_T_on"][0] > 2 * r["T_com_minus_T_on"][1]}  # fmt: skip
    # C2 coupling strength: the Nose-Hoover arms agree with each other and with (2/3) dT_half
    nhc = [n for n in ("nhc-tau0p025", "nhc-tau0p1", "nhc-tau1", "nhc-shift") if get(n, {}).get("frames")]
    for n in nhc:
        r = res[n]
        c[f"C2 {n}: T_com - T_on - (2/3) dT_half = 0"] = {
            "measured": r["T_com_minus_T_on_minus_two_thirds_dT_half"],
            "pass": within(r["T_com_minus_T_on_minus_two_thirds_dT_half"])}  # fmt: skip
    if get("nhc-tau0p1", {}).get("frames"):
        ref = res["nhc-tau0p1"]["T_com_minus_T_on"]
        for n in ("nhc-tau0p025", "nhc-tau1"):
            if get(n, {}).get("frames"):
                dd = diff(res[n]["T_com_minus_T_on"], ref)
                c[f"C2 {n} minus nhc-tau0p1 (T_com - T_on)"] = {"measured": dd, "pass": within(dd) or abs(dd[0]) < 0.5}
    # coupling part: mean residual of the Nose-Hoover arms at 1 fs (inverse-variance weights)
    xs = [res[n]["T_com_minus_T_on_minus_two_thirds_dT_half"] for n in ("nhc-tau0p025", "nhc-tau0p1", "nhc-tau1")
          if get(n, {}).get("frames")]  # fmt: skip
    if xs:
        w = np.array([1 / s**2 for _, s in xs])
        mean = float((w * np.array([x for x, _ in xs])).sum() / w.sum())
        c["coupling part (Nose-Hoover arms, 1 fs), K"] = {"measured": (mean, float(1 / math.sqrt(w.sum())))}
    # C3 BAOAB: slow modes at the target, on-step temperature low by dT_half
    for n in ("baoab-g1", "baoab-g0p1"):
        if get(n, {}).get("frames"):
            r = res[n]
            c[f"C3 {n}: T_com = T0"] = {"measured": r["T_com_minus_target"], "pass": within(r["T_com_minus_target"])}
            c[f"C3 {n}: T_on = T0 - dT_half"] = {"measured": r["T_on_minus_target_plus_dT_half"],
                                                  "pass": within(r["T_on_minus_target_plus_dT_half"])}  # fmt: skip
    # C4 the step: 0.5 fs Nose-Hoover
    if get("nhc-tau0p1-0p5fs", {}).get("frames"):
        r = res["nhc-tau0p1-0p5fs"]
        c["C4 nhc 0.5 fs: T_com - T_on = (2/3) dT_half"] = {
            "measured": r["T_com_minus_T_on"], "predicted": 2 / 3 * r["dT_half"][0],
            "pass": within(r["T_com_minus_T_on_minus_two_thirds_dT_half"])}  # fmt: skip
    # C5 the shifted target: slow modes at T0
    if get("nhc-shift", {}).get("frames"):
        r = res["nhc-shift"]
        dd = (r["T_com"][0] - T0_K, r["T_com"][1])
        c["C5 nhc-shift: T_com = 293.15 K"] = {"measured": dd, "pass": within(dd)}
    # C6 density with BAOAB + MC barostat against SC-1 (1 fs Nose-Hoover, 0.5 fs, extrapolated)
    npt = [res[n]["density_g_cm3"][0] for n in ("baoab-g1-npt-s1", "baoab-g1-npt-s2", "baoab-g1-npt-s3")
           if "density_g_cm3" in get(n, {})]  # fmt: skip
    sc1 = sc1_densities()
    if len(npt) == 3 and sc1:
        b = (float(np.mean(npt)), float(np.std(npt, ddof=1) / math.sqrt(3)))
        r1, r05 = sc1["1"], sc1["0.5"]
        zero = (r05[0] + (r05[0] - r1[0]) / 3.0, math.hypot(4 / 3 * r05[1], 1 / 3 * r1[1]))
        d1, d0 = diff(b, r1), diff(b, zero)
        c["C6 BAOAB NPT density"] = {
            "baoab": b, "nhc_1fs": r1, "nhc_0p5fs": r05, "extrapolated_dt0": zero,
            "baoab_minus_nhc_1fs_pct": (100 * d1[0] / r1[0], 100 * d1[1] / r1[0]),
            "baoab_minus_dt0_pct": (100 * d0[0] / zero[0], 100 * d0[1] / zero[0]),
            "changes_density": d1[0] > 2 * d1[1], "equals_dt0": within(d0)}  # fmt: skip
    # pressure: atomic minus molecular as predicted (unconstrained arms)
    for n, r in res.items():
        if r.get("frames") and not r.get("constraints"):
            c[f"P {n}: atomic - molecular = predicted"] = {
                "measured": r["dP_atomic_minus_molecular_bar"], "predicted": r["dP_predicted_bar"][0],
                "pass": within(r["dP_minus_predicted_bar"])}  # fmt: skip
    # pooled over the unconstrained 1 fs arms (one frame's noise is about 900 bar)
    pool = [r["dP_minus_predicted_bar"] for r in res.values()
            if r.get("frames") and not r.get("constraints") and r["dt_fs"] == 1.0]  # fmt: skip
    if pool:
        w = np.array([1 / s**2 for _, s in pool])
        mean = float((w * np.array([x for x, _ in pool])).sum() / w.sum())
        se = float(1 / math.sqrt(w.sum()))
        c["P pooled 1 fs arms: atomic - molecular - predicted = 0"] = {"measured": (mean, se), "arms": len(pool),
                                                                         "pass": within((mean, se))}  # fmt: skip
    return c


def sc1_densities() -> dict | None:
    """SC-1's per-seed NPT densities of the 1 M box (docs/research/timestep/sc1.json): mean and SE per step."""
    path = HERE.parents[1] / "docs/research/timestep/sc1.json"
    if not path.exists():
        return None
    runs = json.loads(path.read_text())["density"]["1M"]["runs"]
    out = {}
    for step in ("1", "0.5"):
        rho = [r["rho"] for r in runs[step]]
        out[step] = (float(np.mean(rho)), float(np.std(rho, ddof=1) / math.sqrt(len(rho))))
    return out


def main() -> None:
    res = {}
    for arm in ARMS:
        d = HERE / "arms" / arm.name
        if (d / "out/thermo.tsv").exists() and (d / "out/trajectory.h5").exists():
            res[arm.name] = analyze_arm(d)
    out = {"arms": res, "criteria": criteria(res)}
    text = json.dumps(out, indent=1, default=float)
    print(text)
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(text + "\n")


if __name__ == "__main__":
    main()
