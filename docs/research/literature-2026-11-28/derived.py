"""Derived numbers of the V-5 literature note (our arithmetic, not published values).

Reads only the literature ledger (docs/research/summary/literature.json), writes derived.json
next to this file. Run: python3 docs/research/literature-2026-11-28/derived.py
"""

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
LED = json.loads((HERE.parent / "summary/literature.json").read_text(encoding="utf-8"))["entries"]

R = 8.314462618  # J/(mol K), CODATA 2018 (exact)
KB = 1.380649e-23  # J/K, exact
M_LIPF6 = 151.905  # g/mol (as used in docs/research/ion-model/README.md)
M_EC, M_EMC = 88.062, 104.104  # g/mol, IUPAC conventional atomic weights
XI_YH = 2.837297  # Yeh-Hummer constant for a cubic box


def landesfeind_rho(c, t_c):
    p = LED["landesfeind2019_density_fit_ec_emc_3_7"]["value"]
    return p["p1"] + p["p2"] * c + p["p3"] * (t_c + 273.15)


out = {}

# 1. Lehnert's Arrhenius fit of Logan's viscosities, evaluated.
s8 = LED["lehnert2025_table_s8_eta_fit_logan"]["value"]
out["lehnert_s8_eta_cP"] = {
    str(c): {str(t): round(e0 * math.exp(ea / (R * (t + 273.15))), 3) for t in (10, 20, 25, 30, 40)}
    for c, e0, ea in zip(s8["c_m"], s8["eta0_cP"], s8["Ea_J_per_mol"])
}
lg = LED["logan2018a21_eta_ec_emc_3_7"]["value"]
out["lehnert_fit_over_logan_a21_1m"] = {
    str(t): round(out["lehnert_s8_eta_cP"]["1.0"][str(t)] / e - 1, 3)
    for t, e in zip(lg["T_C"], lg["1.0 m_cP"])
}

# 2. Gruber: slopes and activation energy (reproduces Jo's section 6).
g = LED["gruber2026_si1_eta_rho_ec_dmc_emc_vc"]["value"]
rho20 = dict(zip(g["c_M"], g["rho_gcm3_20C"]))
out["gruber_drho_dc_20C"] = {
    "0.25-1": round((rho20[1.0] - rho20[0.25]) / 0.75, 4),
    "1-2": round(rho20[2.0] - rho20[1.0], 4),
    "1.5-3": round((rho20[3.0] - rho20[1.5]) / 1.5, 4),
}
cs, rs = g["c_M"], g["rho_gcm3_20C"]
n = len(cs)
cm, rm = sum(cs) / n, sum(rs) / n
slope = sum((c - cm) * (r - rm) for c, r in zip(cs, rs)) / sum((c - cm) ** 2 for c in cs)
icpt = rm - slope * cm
out["gruber_line_20C"] = {
    "slope": round(slope, 4),
    "intercept": round(icpt, 4),
    "line_minus_data_percent": {str(c): round(100 * ((icpt + slope * c) / r - 1), 2) for c, r in zip(cs, rs)},
}
e1 = dict(zip(g["1M_T_C"], g["1M_eta_mPas"]))
out["gruber_Ea_eta_1M_15_25C_kJ"] = round(
    R * math.log(e1[15] / e1[25]) / (1 / 288.15 - 1 / 298.15) / 1000, 2
)
out["gruber_eta_3M_over_1M_20C"] = round(
    dict(zip(g["c_M"], g["eta_mPas_20C"]))[3.0] / e1[20], 1
)

# 3. Bergstrom densities against Landesfeind's fit at 30 C.
b = LED["bergstrom2021_table1_ec_emc_3_7_30C"]["value"]
out["bergstrom_rho_vs_landesfeind_30C"] = {
    str(c): round(r[0] / 1000 / landesfeind_rho(c, 30.0) - 1, 4) for c, r in zip(b["molarity_M"], b["rho_gL"])
}
out["bergstrom_drho_dc_gcm3_per_M"] = round(
    (b["rho_gL"][-1][0] - b["rho_gL"][0][0]) / 1000 / (b["molarity_M"][-1] - b["molarity_M"][0]), 3
)

# 4. Nyman's partial molar volumes: what density and slope they imply.
ny = LED["nyman2008_partial_molar_volumes_ec_emc"]["value"]
m_solv = 1 / (0.3 / M_EC + 0.7 / M_EMC)  # mean molar mass of 3:7 w:w EC:EMC
rho0_ny = m_solv / ny["V_solvent_cm3_per_mol"]
rho0_lf25 = landesfeind_rho(0.0, 25.0)
out["nyman_implied"] = {
    "M_solvent_g_per_mol": round(m_solv, 2),
    "rho0_gcm3": round(rho0_ny, 4),
    "rho0_landesfeind_25C": round(rho0_lf25, 4),
    "rho0_ratio_minus_1": round(rho0_ny / rho0_lf25 - 1, 4),
    "drho_dc_with_own_rho0": round((M_LIPF6 - ny["V_LiPF6_cm3_per_mol"] * rho0_ny) / 1000, 4),
    "drho_dc_with_landesfeind_rho0": round((M_LIPF6 - ny["V_LiPF6_cm3_per_mol"] * rho0_lf25) / 1000, 4),
}
k = LED["nyman2008_kappa_eq22_ec_emc_25C"]["value"]
out["nyman_kappa_1M_S_per_m"] = round(0.1 * (k["A1"][0] + k["A2"][0] + k["A3"][0]), 4)

# 5. Yeh-Hummer correction for our 1 M box (L = 4.28 nm, 20 C) at a given viscosity: orientation only.
L, T = 4.28e-9, 293.15
out["yeh_hummer_dD_1e-11_m2s_for_eta_mPas"] = {
    str(eta): round(XI_YH * KB * T / (6 * math.pi * eta * 1e-3 * L) / 1e-11, 2) for eta in (3.0, 3.3, 5.0, 7.0)
}

(HERE / "derived.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
print(json.dumps(out, indent=1))
