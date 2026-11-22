"""Trial T6, stage 2: fit option A (one Li⁺ σ) and option B (Li–O(carbonyl) pair terms) to the
DFT clusters. Plan and weights: docs/research/trials/T6-li-carbonyl-correction.md (amendment 2).

Run from the workspace root with the oracle venv (OpenMM, numpy):

    tools/oracle/.venv/bin/python docs/research/trials/T6/t6_fit.py \
        --pkg PKGDIR --clusters clusters_F.json --dimers dimers_F.json --out OUT.json

PKGDIR holds the packages of tools/ffcheck/build_cluster_packages.sh (li_ecN_emcM.ucsys).
clusters_F.json and dimers_F.json come from tools/qm/cluster_dft.py with the chosen functional F.

Force-field side: gas phase, no cutoff, Reference platform, q_Li = 0.75 (production), PF₆⁻ absent
(decoupled and 100 nm away; all its internal pairs are excluded, so nothing internal changes).
Each cluster is minimized from its DFT geometry; free solvents from their lowest DFT geometry,
100 nm apart. Exchange energies ΔE_n = E(n) − E(0) − n [E(EC) − E(EMC)].
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import math
import sys
from pathlib import Path

import numpy as np
import openmm as mm

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools/ffcheck"))
from li_binding import FAR_NM, KCAL_IN_KJ, _minimize, _package_info, build_system
from oracle import load_topology

KJMOL_PER_HARTREE = 4.3597447222071e-18 * 6.02214076e23 / 1e3  # CODATA 2018
NM_PER_ANGSTROM = 0.1  # exact
Q_LI = 0.75
FLOOR_D, FLOOR_E = 0.01, 0.3  # Å, kcal/mol (amendment 2)
MP2 = ROOT / "tools/qm/results/li_binding_mp2_aug-cc-pvtz.json"


@dataclasses.dataclass
class Cluster:
    n_ec: int
    top: object
    li: int
    pf6: list[int]
    molecules: list[tuple[list[int], int, str]]  # (global atoms, carbonyl O, name)


def carbonyl(mt: dict) -> int:
    nb: dict[int, int] = {i: 0 for i in range(len(mt["atoms"]))}
    for b in mt["bonds"]:
        for i in b["atoms"]:
            nb[i] += 1
    (o,) = [i for i, a in enumerate(mt["atoms"]) if a["element"] == "O" and nb[i] == 1]
    return o


def load_cluster(path: Path, n_ec: int) -> Cluster:
    top = load_topology(path)
    info = _package_info(path)
    mols = []
    for name, (idx, mt) in info.items():
        if name in ("Li", "PF6"):
            continue
        n, o = len(mt["atoms"]), carbonyl(mt)
        for k in range(len(idx) // n):
            g = idx[k * n : (k + 1) * n]
            mols.append((g, g[o], name))
    return Cluster(n_ec, top, info["Li"][0][0], info["PF6"][0], mols)


def system_for(c: Cluster, params: dict, *, li_on: bool = True) -> mm.System:
    """params: {"sigma_li": nm} (A) or {"pairs": {"EC": (σ nm, ε kJ/mol), "EMC": (...)}} (B)."""
    t = c.top
    q, eps, sig = t.charges_e.copy(), t.epsilon_kjmol.copy(), t.sigma_nm.copy()
    q[c.pf6], eps[c.pf6] = 0.0, 0.0
    q[c.li] = Q_LI if li_on else 0.0
    if not li_on:
        eps[c.li] = 0.0
    if "sigma_li" in params:
        sig[c.li] = params["sigma_li"]
    system = build_system(
        dataclasses.replace(t, cell_nm=None, charges_e=q, epsilon_kjmol=eps, sigma_nm=sig)
    )
    pairs = params.get("pairs")
    if pairs and li_on:
        (lj,) = [f for f in system.getForces() if isinstance(f, mm.CustomNonbondedForce)]
        bond = mm.CustomBondForce("4*eps*((sig/r)^12-(sig/r)^6)")
        bond.addPerBondParameter("sig")
        bond.addPerBondParameter("eps")
        for _, o, name in c.molecules:
            s, e = pairs[name]
            lj.addExclusion(c.li, o)
            bond.addBond(c.li, o, [float(s), float(e)])
        system.addForce(bond)
    return system


def positions(c: Cluster, xyz: list, spread: bool = False) -> np.ndarray:
    """Package-order positions from a DFT geometry (Li⁺ first, then the solvents in package
    order). With spread, each solvent is moved 100 nm from the others."""
    pos = c.top.positions_nm.copy()
    order = [c.li] + [i for g, _, _ in c.molecules for i in g]
    pos[order] = np.array([r[1:] for r in xyz]) * NM_PER_ANGSTROM
    pos[c.pf6] = pos[c.pf6] - pos[c.pf6].mean(axis=0) + np.array([0.0, 0.0, -FAR_NM])
    if spread:
        for k, (g, _, _) in enumerate(c.molecules):
            pos[g] += np.array([FAR_NM * (k + 1), 0.0, 0.0])
        pos[c.li] = np.array([0.0, FAR_NM, 0.0])
    return pos


def evaluate(clusters: list[Cluster], dft: dict[int, dict], e_free: float, params: dict) -> dict:
    """Force-field Li–O distances (Å, per molecule) and ΔE_n (kcal/mol) for the given params."""
    energy, dist = {}, {}
    for c in clusters:
        e, p = _minimize(system_for(c, params), positions(c, dft[c.n_ec]["complex_xyz"]))
        energy[c.n_ec] = e / KCAL_IN_KJ
        dist[c.n_ec] = [
            float(np.linalg.norm(p[o] - p[c.li])) / NM_PER_ANGSTROM for _, o, _ in c.molecules
        ]
    de = {n: energy[n] - energy[0] - n * e_free for n in energy if n > 0}
    return {"li_o_angstrom": dist, "delta_e_kcalmol": de}


def free_difference(clusters: list[Cluster], alone: dict[str, list]) -> float:
    """Force-field E(EC) − E(EMC) (kcal/mol), each minimized alone from its DFT minimum."""
    e = {}
    for name in ("EC", "EMC"):
        c = next(c for c in clusters if all(m[2] == name for m in c.molecules))
        xyz = [["Li", 0.0, 0.0, 0.0]] + [r for _ in c.molecules for r in alone[name]]
        en, _ = _minimize(system_for(c, {}, li_on=False), positions(c, xyz, spread=True))
        e[name] = en / KCAL_IN_KJ / len(c.molecules)
    return e["EC"] - e["EMC"]


def dft_targets(rows: list[dict]) -> tuple[dict, dict, dict]:
    """Per n_ec: the DFT row; ΔE_n (kcal/mol, CP); lowest free-solvent geometries."""
    by_n = {r["solvents"].count("EC"): r for r in rows}
    alone, e_alone = {}, {}
    for r in rows:
        for s in r["solvent_alone"]:
            if s["name"] not in e_alone or s["e_alone_hartree"] < e_alone[s["name"]]:
                e_alone[s["name"]], alone[s["name"]] = s["e_alone_hartree"], s["xyz_alone"]
    k = KJMOL_PER_HARTREE / KCAL_IN_KJ
    e_cp = {}
    for n, r in by_n.items():
        bsse = r["e_bind_cp_kcalmol"] - r["e_bind_kcalmol"]
        e_cp[n] = r["e_complex_hartree"] * k + bsse
    de = {n: e_cp[n] - e_cp[0] - n * (e_alone["EC"] - e_alone["EMC"]) * k for n in by_n if n > 0}
    return by_n, de, alone


def uncertainties(dimers: list[dict]) -> tuple[float, float, dict]:
    mp2 = {r["start"].split("_q")[0]: r for r in json.loads(MP2.read_text())}
    err_d, err_e, rows = [], [], {}
    for r in dimers:
        m = mp2[r["start"].removesuffix(".xyz")]
        dd = r["li_o_carbonyl"][0]["li_o_angstrom"] - m["li_o_angstrom"]
        de = r["e_bind_kcalmol"] - m["e_bind_kcalmol"]
        dc = r["e_int_cp_at_complex_kcalmol"] - m["e_int_cp_at_complex_kcalmol"]
        err_d.append(abs(dd))
        err_e += [abs(de), abs(dc)]
        rows[r["start"]] = {"d_li_o": dd, "e_bind": de, "e_int_cp": dc}
    return max(max(err_d), FLOOR_D), max(max(err_e), FLOOR_E), rows


def residuals(ff: dict, dft: dict, de_dft: dict, s_d: float, s_e: float, energies: bool):
    r = []
    for n, row in dft.items():
        ref = [x["li_o_angstrom"] for x in row["li_o_carbonyl"]]
        r += [(a - b) / s_d for a, b in zip(ff["li_o_angstrom"][n], ref, strict=True)]
    if energies:
        r += [(ff["delta_e_kcalmol"][n] - de_dft[n]) / s_e for n in de_dft]
    return np.array(r)


def golden(f, lo: float, hi: float, tol: float = 1e-5) -> float:
    g = (math.sqrt(5) - 1) / 2
    a, b = lo, hi
    c, d = b - g * (b - a), a + g * (b - a)
    fc, fd = f(c), f(d)
    while b - a > tol:
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - g * (b - a)
            fc = f(c)
        else:
            a, c, fc = c, d, fd
            d = a + g * (b - a)
            fd = f(d)
    return 0.5 * (a + b)


def nelder_mead(f, x0: np.ndarray, step: np.ndarray, iters: int = 600) -> np.ndarray:
    pts = [x0] + [x0 + np.eye(len(x0))[i] * step[i] for i in range(len(x0))]
    vals = [f(p) for p in pts]
    for _ in range(iters):
        idx = np.argsort(vals)
        pts, vals = [pts[i] for i in idx], [vals[i] for i in idx]
        if abs(vals[-1] - vals[0]) < 1e-9 * (1 + abs(vals[0])):
            break
        centre = np.mean(pts[:-1], axis=0)
        xr = centre + (centre - pts[-1])
        fr = f(xr)
        if fr < vals[0]:
            xe = centre + 2 * (centre - pts[-1])
            fe = f(xe)
            pts[-1], vals[-1] = (xe, fe) if fe < fr else (xr, fr)
        elif fr < vals[-2]:
            pts[-1], vals[-1] = xr, fr
        else:
            xc = centre + 0.5 * (pts[-1] - centre)
            fc = f(xc)
            if fc < vals[-1]:
                pts[-1], vals[-1] = xc, fc
            else:
                pts = [pts[0]] + [pts[0] + 0.5 * (p - pts[0]) for p in pts[1:]]
                vals = [vals[0]] + [f(p) for p in pts[1:]]
    return pts[int(np.argmin(vals))]


def combined(c: Cluster, name: str, sigma_li: float | None = None) -> tuple[float, float]:
    """The combination-rule (geometric) σ, ε of Li with the carbonyl O of `name`."""
    t = c.top
    _, o, _ = next(m for m in c.molecules if m[2] == name)
    s_li = t.sigma_nm[c.li] if sigma_li is None else sigma_li
    return math.sqrt(s_li * t.sigma_nm[o]), math.sqrt(t.epsilon_kjmol[c.li] * t.epsilon_kjmol[o])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--pkg", type=Path, required=True)
    ap.add_argument("--clusters", type=Path, required=True)
    ap.add_argument("--dimers", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--max-iter", type=int, default=600, help="Nelder–Mead iterations (B)")
    args = ap.parse_args()
    clusters = [load_cluster(args.pkg / f"li_ec{n}_emc{4 - n}.ucsys", n) for n in range(5)]
    dft, de_dft, alone = dft_targets(json.loads(args.clusters.read_text()))
    s_d, s_e, dimer_err = uncertainties(json.loads(args.dimers.read_text()))
    e_free = free_difference(clusters, alone)
    c4 = clusters[4]
    sigma0 = float(c4.top.sigma_nm[c4.li])

    # consistency: B with the combination-rule pair values must equal the unmodified model
    base = evaluate(clusters, dft, e_free, {})
    same = evaluate(clusters, dft, e_free, {"pairs": {n: combined(c4 if n == "EC" else clusters[0], n) for n in ("EC", "EMC")}})  # fmt: skip
    check = max(abs(base["delta_e_kcalmol"][n] - same["delta_e_kcalmol"][n]) for n in range(1, 5))
    assert check < 1e-3, f"pair override does not reproduce the combination rule ({check})"
    print(f"check: pair override = combination rule to {check:.1e} kcal/mol", flush=True)

    def cost_a(s: float) -> float:
        ff = evaluate(clusters, dft, e_free, {"sigma_li": s})
        return float(np.sum(residuals(ff, dft, de_dft, s_d, s_e, energies=False) ** 2))

    sigma_a = golden(cost_a, 0.5 * sigma0, 1.1 * sigma0, tol=1e-4)
    print(f"A: sigma_li = {sigma_a:.4f} nm (from {sigma0:.4f})", flush=True)
    ff_a = evaluate(clusters, dft, e_free, {"sigma_li": sigma_a})

    ec0, emc0 = combined(c4, "EC"), combined(clusters[0], "EMC")

    def unpack(x: np.ndarray) -> dict:
        return {"pairs": {"EC": (x[0], math.exp(x[1])), "EMC": (x[2], math.exp(x[3]))}}

    def cost_b(x: np.ndarray) -> float:
        if min(x[0], x[2]) <= 0.05:
            return 1e12
        ff = evaluate(clusters, dft, e_free, unpack(x))
        return float(np.sum(residuals(ff, dft, de_dft, s_d, s_e, energies=True) ** 2))

    x0 = np.array([ec0[0], math.log(ec0[1]), emc0[0], math.log(emc0[1])])
    xb = nelder_mead(cost_b, x0, np.array([0.02, 1.0, 0.02, 1.0]), args.max_iter)
    ff_b = evaluate(clusters, dft, e_free, unpack(xb))

    def summary(ff: dict, energies: bool) -> dict:
        r = residuals(ff, dft, de_dft, s_d, s_e, energies)
        return {
            **ff,
            "weighted_rms": float(np.sqrt(np.mean(r**2))),
            "rms_with_energies": float(
                np.sqrt(np.mean(residuals(ff, dft, de_dft, s_d, s_e, True) ** 2))
            ),
        }

    result = {
        "plan": "docs/research/trials/T6-li-carbonyl-correction.md",
        "q_li": Q_LI,
        "s_d_angstrom": s_d,
        "s_e_kcalmol": s_e,
        "dft_vs_mp2_single": dimer_err,
        "dft": {
            "li_o_angstrom": {
                n: [x["li_o_angstrom"] for x in r["li_o_carbonyl"]] for n, r in dft.items()
            },
            "delta_e_kcalmol": de_dft,
        },
        "ff_free_EC_minus_EMC_kcalmol": e_free,
        "M1": summary(base, False),
        "A": {"sigma_li_nm": sigma_a, "sigma_li_0_nm": sigma0, **summary(ff_a, False)},
        "B": {
            "pairs": {
                k: {"sigma_nm": v[0], "epsilon_kjmol": v[1]} for k, v in unpack(xb)["pairs"].items()
            },
            "combination_rule": {"EC": ec0, "EMC": emc0},
            **summary(ff_b, True),
        },
    }
    args.out.write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps({k: result[k] for k in ("s_d_angstrom", "s_e_kcalmol")}, indent=1))
    for k in ("M1", "A", "B"):
        r = result[k]
        print(k, {n: round(v, 2) for n, v in r["delta_e_kcalmol"].items()},
              "rms(d)", round(r["weighted_rms"], 2), "rms(all)", round(r["rms_with_energies"], 2))  # fmt: skip
    print("DFT", {n: round(v, 2) for n, v in de_dft.items()})


if __name__ == "__main__":
    main()
