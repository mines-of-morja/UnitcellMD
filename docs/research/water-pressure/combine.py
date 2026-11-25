"""Combine data/*.json (pdecomp.py, tconf.py) into the numbers of the README."""
import json
from pathlib import Path
import numpy as np

H = Path(__file__).parent / "data"
L = lambda n: json.loads((H / f"{n}.json").read_text())
TR, RO = "T configurational, translation of molecules", "T configurational, rotation of molecules"
def wm(xs):
    v, e = np.array(xs).T
    w = 1 / e**2
    return (v * w).sum() / w.sum(), w.sum() ** -0.5, ((v - (v * w).sum() / w.sum()) ** 2 * w).sum() / max(len(v) - 1, 1)
# excess over the run's thermostat set point (the displayed T averages to it; the sampled frames scatter by 0.1-0.6 K)
one = [("water_gpu_rho1000", 298.16), ("water_gpu_rho10072", 298.16), ("water_gpu_rho1012", 298.16), ("water_wu", 298.16), ("water_cpu1", 300.2)]
half = [("water_cpu05", 298.15), ("water_gpu05", 298.15)]
print("excess over the set temperature (K): run, translation, rotation")
for n, t in one + half:
    d = L(n)
    print(f"  {n:22s} {d[TR][0]-t:+5.1f} +- {d[TR][1]:.1f}   {d[RO][0]-t:+5.1f} +- {d[RO][1]:.1f}")
for lab, g in (("1 fs", one), ("0.5 fs", half)):
    for k, s in ((TR, "translation"), (RO, "rotation")):
        m, e, c = wm([(L(n)[k][0] - t, L(n)[k][1]) for n, t in g])
        print(f"  water {lab:6s} {s:12s} {m:+.1f} +- {e:.1f} K (chi2/dof {c:.1f})")
    m, e, c = wm([(L(n)[k][0] - t, L(n)[k][1]) for n, t in g for k in (TR, RO)])
    print(f"  water {lab:6s} both         {m:+.1f} +- {e:.1f} K (chi2/dof {c:.1f})")
E3 = [L(f"electrolyte_m1_s{i}") for i in (1, 2, 3)]
m, e, c = wm([(d["all"][0] - 293.15, d["all"][1]) for d in E3])
hs = np.mean([d["half-step minus on-step T (dt=1fs)"][0] for d in E3])
print(f"electrolyte M1 1 fs, translation {m:+.1f} +- {e:.1f} K (chi2/dof {c:.1f}); half-step minus on-step {hs:.2f} K, 2/3 of it {2*hs/3:.1f} K")
print("pressure components at rho = 1.012, 1 fs (GPU NVT), bar")
for k in ("P ideal, molecule centres at T set", "P Coulomb (molecular)", "P LJ within cutoff (molecular)", "P LJ tail"):
    print(f"  {k:40s}{L('water_gpu_rho1012')[k][0]:10.0f} +- {L('water_gpu_rho1012')[k][1]:.0f}")
for n in ("water_cpu1", "water_wu"):
    d = L(n)
    print(n, {k: [round(x, 1) for x in d[k]] for k in ("P molecular, sum (kinetic at T conf trans)", "P atomic, on-step KE (thermo) + atomic virial", "P atomic - P molecular(T set), internal motion")})
# budget at rho = 1.012, 298.16 K
r = json.loads((Path(__file__).parents[3] / "studies/2026-11-23_water-pressure-vs-density/analysis/results.json").read_text())
P, sP = r["runs"]["spcfw_512_rho1012"]["P_mean_bar"], r["runs"]["spcfw_512_rho1012"]["P_err_bar"]
kap = r["kappa_T_per_bar"]
beta = 4.98e-4 / (4.5e-5 / 1.01325)   # Wu 2006: alpha_P (K^-1) / kappa_T (atm^-1 -> bar^-1)
dT, sT, _ = wm([(L(n)[k][0] - t, L(n)[k][1]) for n, t in one for k in (TR, RO)])
bias, sb = -126.9, 0.4        # docs/tasks/2026-11-24-sanity-check/README.md (predicted, measured -129 +- 9)
print(f"P molecular (GPU)          {P:6.1f} +- {sP:.1f} bar")
print(f"  from the excess T        {dT*beta:6.1f} +- {sT*beta:.1f}  ({dT:.1f} +- {sT:.1f} K x {beta:.1f} bar/K)")
rest, sr = P - dT * beta - 1.01, np.hypot(sP, sT * beta)
print(f"  remainder above 1 atm    {rest:6.1f} +- {sr:.1f}  -> density at 1 atm {1.012*(1-kap*rest):.4f} +- {1.012*kap*sr:.4f}")
print(f"P atomic = P molecular + ({bias}) = {P+bias:.1f} +- {sP:.1f} bar; CPU run 26.1 +- 7.3 at 300.09 K -> {26.1-beta*(300.09-298.16):.1f} at 298.16 K")
