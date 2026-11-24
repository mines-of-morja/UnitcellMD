import h5py
import numpy as np

kB = 0.00831446261815324
for lab, f, nm, T, sk in [
    (
        "CPU NVT 1.0fs 300.2K",
        "studies/2026-11-20_water-spcfw-viscosity-cpu/runs/spcfw_512/T27.05C/out/trajectory.h5",
        512,
        300.2,
        200,
    ),
    (
        "CPU NPT 0.5fs 298.15K",
        "studies/2026-11-20_water-spcfw-cpu/runs/spcfw_500/T25C/out/trajectory.h5",
        500,
        298.15,
        50,
    ),
]:
    h = h5py.File(f, "r")
    o = h["observables"]
    t = o["energy_terms/bond/time"][:]
    m = t >= sk
    for k in ("bond", "angle"):
        x = o["energy_terms/" + k + "/value"][:][m] / nm / (kB * T)
        b = np.array([c.mean() for c in np.array_split(x, 8)])
        print(lab, k, "<U>/kT per molecule", x.mean(), "+-", b.std(ddof=1) / 8**0.5)
    # bond-length variance
    X = h["particles/all/position/value"]
    fr = np.where(m)[0][:: max(1, m.sum() // 200)]
    v = []
    for i in fr:
        p = X[i].reshape(nm, 3, 3)
        d = np.linalg.norm(p[:, 1:] - p[:, :1], axis=2).ravel()
        v.append((d.mean(), d.var()))
    v = np.array(v)
    print(
        "   r_OH mean",
        v[:, 0].mean(),
        "var/kT",
        v[:, 1].mean() / (kB * T),
        "+-",
        v[:, 1].std() / len(v) ** 0.5 / (kB * T),
    )
