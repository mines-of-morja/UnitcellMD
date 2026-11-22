"""T1 addendum (2026-11-22): SOL frame with the solvent velocity weighted by mass or by moles.

Not part of the pre-registered decisions (a)-(c). Newman's t+0 takes EC + EMC as one solvent; its
velocity can be the mass-weighted (as in T1) or the mole-weighted mean of the two solvents. Same
blocks, window and estimator as t1_frames.py.

    HDF5_USE_FILE_LOCKING=FALSE ucmd-analysis/.venv/bin/python \
        docs/research/trials/T1/t1_sol_weighting.py TRAJ.h5 OUT.json [start=501]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from ucmd_analysis.io import read_h5md
from ucmd_analysis.molecules import barycentric
from ucmd_analysis.transport import FitWindow
from ucmd_analysis.uncertainty import blocks, mean_sem

sys.path.insert(0, str(Path(__file__).parent))
from t1_frames import N_BLOCKS, t_plus


def main(path: str, out: str, start: int) -> None:
    traj = read_h5md(path, start=start)
    sp = traj.system.species
    com = {n: barycentric(traj, sp[n]) for n in ("Li", "PF6", "EC", "EMC")}
    n_ec, n_emc = sp["EC"].count, sp["EMC"].count
    m_ec, m_emc = float(sp["EC"].masses.sum()), float(sp["EMC"].masses.sum())
    mean_ec, mean_emc = com["EC"].mean(axis=1), com["EMC"].mean(axis=1)
    weights = {
        "mass": m_ec * n_ec / (m_ec * n_ec + m_emc * n_emc),
        "mole": n_ec / (n_ec + n_emc),
    }
    w = FitWindow()
    dt = float(traj.times_ps[1] - traj.times_ps[0])
    rows: dict[str, list[float]] = {k: [] for k in weights}
    for block in blocks(len(traj), N_BLOCKS):
        lags = np.arange(block.stop - block.start) * dt
        s_p = com["Li"][block].sum(axis=1)
        s_m = com["PF6"][block].sum(axis=1)
        for k, a in weights.items():
            ref = a * mean_ec[block] + (1 - a) * mean_emc[block]
            rows[k].append(t_plus(s_p - sp["Li"].count * ref, s_m - sp["PF6"].count * ref, lags, w))
    diff = [b - a for a, b in zip(rows["mass"], rows["mole"], strict=True)]
    result = {
        "ec_weight": weights,
        "blocks": rows,
        "stats": {k: dict(zip(("mean", "sem"), mean_sem(v), strict=True)) for k, v in rows.items()},
        "mole_minus_mass": dict(zip(("mean", "sem"), mean_sem(diff), strict=True)),
    }
    Path(out).write_text(json.dumps(result, indent=1))
    print(json.dumps({k: v for k, v in result.items() if k != "blocks"}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 501)
