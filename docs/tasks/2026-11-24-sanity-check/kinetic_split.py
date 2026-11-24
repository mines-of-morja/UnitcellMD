import sys

import h5py
import numpy as np

kB = 0.00831446261815324
BAR = 16.6053906660
f = sys.argv[1]
dt = float(sys.argv[2]) * 1e-3
skip = float(sys.argv[3])
h = h5py.File(f, "r")
p = h["particles/all"]
m = p["mass"][:]
t = p["velocity/time"][:]
mi = p["molecule_index"][:]
n = len(m)
nm = mi.max() + 1
M = np.bincount(mi, m)
V = h["observables/volume/value"][0] if "volume" in h["observables"] else None
import numpy as np

ed = p["box/edges/value"]
V = abs(np.linalg.det(ed[0] if ed.ndim == 3 else ed[:]))
sel = np.where(t >= skip)[0]
R = []
for i in sel:
    v = p["velocity/value"][i]
    F = p["force/value"][i]
    x = p["position/value"][i]
    vc = np.stack([np.bincount(mi, m * v[:, k]) for k in range(3)], 1) / M[:, None]
    xc = np.stack([np.bincount(mi, m * x[:, k]) for k in range(3)], 1) / M[:, None]
    K = (m[:, None] * v**2).sum()
    Kc = (M[:, None] * vc**2).sum()
    Tcom = Kc / (3 * nm - 3) / kB
    Tint = (K - Kc) / (3 * n - 3 * nm) / kB
    Ttot = K / (3 * n - 3) / kB
    Fc = np.stack([np.bincount(mi, F[:, k]) for k in range(3)], 1)
    b = (dt**2 * F**2 / (4 * m[:, None])).sum()
    bc = (dt**2 * Fc**2 / (4 * M[:, None])).sum()
    xr = x - xc[mi]
    d = ((K - Kc) + (xr * F).sum()) / (3 * V) * BAR  # atomic minus molecular pressure, direct
    R.append(
        (
            Ttot,
            Tcom,
            Tint,
            -(b - bc) / (3 * V) * BAR,
            d,
            b / (3 * n - 3) / kB,
            bc / (3 * nm - 3) / kB,
        )
    )
R = np.array(R)
nb = 5
for k, l in enumerate(
    [
        "T total (what the log shows)",
        "T of molecule centres",
        "T internal",
        "predicted P_atomic-P_molecular (bar)",
        "direct   P_atomic-P_molecular (bar)",
        "half-step minus on-step T, all atoms",
        "same, molecule centres",
    ]
):
    b = np.array([c.mean() for c in np.array_split(R[:, k], nb)])
    print(f"{l:42s} {R[:, k].mean():8.2f} +- {b.std(ddof=1) / nb**0.5:.2f}")
print("frames", len(R), "V", V)
