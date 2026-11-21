"""Trial T1 (docs/research/trials/T1-tplus-frames.md): t+ in the COM, SOL, EC, EMC and VOL frames.

Run from the workspace root with the ucmd-analysis venv:

    HDF5_USE_FILE_LOCKING=FALSE ucmd-analysis/.venv/bin/python \
        docs/research/trials/T1/t1_frames.py TRAJ.h5 OUT.json

Same blocks, fit window and estimator as ucmd_analysis.transport.transport(); the script first
checks that its COM value equals transport()'s, block by block.

A frame with reference velocity v_ref changes the collective ion displacement to
X_i = sum_a dr_a - N_i dR_ref, where dR_ref is the displacement of the reference: the centre of
mass of the solvent (SOL), of the EC molecules (EC) or of the EMC molecules (EMC). The Onsager
coefficients of the frame follow from the same Einstein slopes, and
t+ = (L++ - L+-) / (L++ + L-- - 2 L+-) for z = +-1.
"""

from __future__ import annotations

import json
import sys

import numpy as np
from ucmd_analysis.io import read_h5md
from ucmd_analysis.molecules import barycentric
from ucmd_analysis.msd import cross_msd, msd_series
from ucmd_analysis.transport import FitWindow, slope, transport
from ucmd_analysis.uncertainty import blocks, mean_sem

T_K = 293.15
N_BLOCKS = 5
NU_E = 55.7  # cm3/mol, LiPF6 in EC:EMC 3:7 at 20 C, Landesfeind 2019 SI fit (ledger, one reading)
NU_PLUS = {"A": -9.0, "B": 1.1}  # cm3/mol, Marcus & Hefter 2004: TPTB scale (PC) / intrinsic
AVOGADRO = 6.02214076e23  # exact (SI 2019)


def t_plus(xp: np.ndarray, xm: np.ndarray, lags: np.ndarray, w: FitWindow) -> float:
    lpp = slope(lags, msd_series(xp), w)
    lmm = slope(lags, msd_series(xm), w)
    lpm = slope(lags, cross_msd(xp, xm), w)
    return (lpp - lpm) / (lpp + lmm - 2 * lpm)


def main(path: str, out: str, start: int) -> None:
    traj = read_h5md(path, start=start)
    sp = traj.system.species
    w = FitWindow()
    ref = transport(traj, T_K, "Li", "PF6", n_blocks=N_BLOCKS)["t_plus_COM"]
    com = {n: barycentric(traj, sp[n]) for n in ("Li", "PF6", "EC", "EMC")}
    mass = {n: float(sp[n].masses.sum()) for n in com}  # amu per molecule
    count = {n: sp[n].count for n in com}
    m_tot = sum(mass[n] * count[n] for n in com)
    w_minus = mass["PF6"] * count["PF6"] / m_tot
    w_0 = (mass["EC"] * count["EC"] + mass["EMC"] * count["EMC"]) / m_tot
    # reference displacements (frames, 3), in the barycentric frame
    mean = {n: com[n].mean(axis=1) for n in ("EC", "EMC")}
    sol = (mass["EC"] * count["EC"] * mean["EC"] + mass["EMC"] * count["EMC"] * mean["EMC"]) / (
        mass["EC"] * count["EC"] + mass["EMC"] * count["EMC"]
    )
    refs = {"COM": np.zeros_like(sol), "SOL": sol, "EC": mean["EC"], "EMC": mean["EMC"]}
    dt = float(traj.times_ps[1] - traj.times_ps[0])
    rows: dict[str, list[float]] = {}
    for block in blocks(len(traj), N_BLOCKS):
        lags = np.arange(block.stop - block.start) * dt
        s_p = com["Li"][block].sum(axis=1)
        s_m = com["PF6"][block].sum(axis=1)
        vol_cm3 = float(traj.volumes_nm3()[block].mean()) * 1e-21
        c_e = count["Li"] / AVOGADRO / vol_cm3  # mol/cm3
        for name, r in refs.items():
            x_p = s_p - count["Li"] * r[block]
            x_m = s_m - count["PF6"] * r[block]
            rows.setdefault(name, []).append(t_plus(x_p, x_m, lags, w))
        rows.setdefault("SOL_from_Eq2", []).append((rows["COM"][-1] - w_minus) / w_0)
        for conv, nu_p in NU_PLUS.items():
            t_vol = (1 - c_e * NU_E) * rows["SOL"][-1] + c_e * (NU_E - nu_p)
            rows.setdefault(f"VOL_{conv}", []).append(t_vol)
        rows.setdefault("c_e_mol_per_L", []).append(c_e * 1e3)
    stats = {k: dict(zip(("mean", "sem"), mean_sem(v), strict=True)) for k, v in rows.items()}
    eq2 = max(abs(a - b) for a, b in zip(rows["SOL"], rows["SOL_from_Eq2"], strict=True))
    d_ab = [abs(a - b) for a, b in zip(rows["VOL_A"], rows["VOL_B"], strict=True)]
    d_s = [a - b for a, b in zip(rows["EC"], rows["EMC"], strict=True)]
    result = {
        "plan": "docs/research/trials/T1-tplus-frames.md",
        "trajectory": path.split("studies/")[-1],
        "start_frame": start,
        "frames": len(traj),
        "w_minus": w_minus,
        "w_0": w_0,
        "nu_e_cm3_per_mol": NU_E,
        "nu_plus_cm3_per_mol": NU_PLUS,
        "COM_matches_transport": {
            "transport": ref,
            "here": stats["COM"],
            "abs_diff_of_means": abs(stats["COM"]["mean"] - ref["mean"]),
        },
        "blocks": rows,
        "stats": stats,
        "a_delta_AB": dict(zip(("mean", "sem"), mean_sem(d_ab), strict=True)),
        "b_EC_minus_EMC": dict(zip(("mean", "sem"), mean_sem(d_s), strict=True)),
        "c_max_abs_SOL_minus_Eq2": eq2,
    }
    with open(out, "w") as fh:
        json.dump(result, fh, indent=1)
    print(json.dumps({k: v for k, v in result.items() if k != "blocks"}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 501)
