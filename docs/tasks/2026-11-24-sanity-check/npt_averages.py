import glob
import json
import os
import tomllib
from pathlib import Path

import numpy as np

R = "studies/"
AMU = 1.66053906660e-24
kB = 0.00831446261815324


def mass(run):

    cfg = tomllib.loads(Path(run, "run.toml").read_text())
    p = os.path.normpath(os.path.join(run, cfg["system"])) + "/system.json"
    j = json.loads(Path(p).read_text())
    t = (
        {m["name"]: m for m in j["molecule_types"]}
        if isinstance(j["molecule_types"], list)
        else j["molecule_types"]
    )
    M = 0
    n = 0
    nm = 0
    for c in j["components"]:
        a = t[c["molecule_type"]]["atoms"]
        M += c["count"] * sum(x["mass_amu"] for x in a)
        n += c["count"] * len(a)
        nm += c["count"]
    return M, n, nm, cfg


def blk(x, nb=8):
    x = x[~np.isnan(x)]
    b = np.array([c.mean() for c in np.array_split(x, nb)])
    return x.mean(), b.std(ddof=1) / nb**0.5


def cfgtau(cfg):
    return cfg


rows = []
for f in sorted(glob.glob(R + "*/runs/*/*/out/thermo.tsv")):
    run = f[: -len("/out/thermo.tsv")]
    try:
        M, n, nm, cfg = mass(run)
    except (OSError, KeyError, ValueError) as e:
        print("ERR", run, e)
        continue
    if "barostat" not in cfg:
        continue
    hdr = Path(f).read_text().split("\n", 1)[0].lstrip("# ").split()
    a = np.genfromtxt(f, comments="#")
    c = {h: a[:, i] for i, h in enumerate(hdr)}
    t = c["time_ps"]
    tot = t[-1]
    if tot < 200:
        continue
    sk = max(0.3 * tot, 100)
    m = t >= sk
    V = c["volume_nm3"][m]
    rho = M * AMU / (V * 1e-21)
    T = c["temperature_K"][m]
    P = c["pressure_bar"][m]
    T0 = cfg["thermostat"]["temperature_K"]
    r, sr = blk(rho)
    Tm, sT = blk(T)
    Pm, sP = blk(P)
    kap = V.var() / (kB * T0 * V.mean()) / 16.6053906660  # nm3/(kJ/mol) -> /bar
    # kJ/mol/nm3 = 16.605 bar
    print(
        f"{run[8:]:75s} {tot:6.0f}ps T {Tm:7.2f}±{sT:.2f} (set {T0}) sT/exp {T.std() / (T0 * (2 / (3 * n - 3)) ** 0.5):.3f} P {Pm:6.1f}±{sP:.1f} rho {r:.4f}±{sr:.4f} kT {kap * 1e5:.1f}e-5"
    )
