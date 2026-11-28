"""p(T), Delta_vap H and T_b from the Antoine fits of Goldberg, Herdegen, Braeuer (SC-7, publication rule 3).

    python3 goldberg_dh.py [T_K]

Source: J. Chem. Eng. Data 71, 4756 (2026), doi 10.1021/acs.jced.6c00429, Table 4 (p. 4762):
log10(p/Pa) = A - B/(T/K + C). The parameters are copied as printed; the ledger entries are
`goldberg2026_table4_antoine_emc` and `goldberg2026_table4_antoine_dmc` in
docs/research/summary/literature.json.

Delta_vap H comes from the ideal-gas Clausius-Clapeyron relation (liquid volume and gas
non-ideality neglected): Delta_vap H = R ln(10) B T^2 / (T + C)^2. It is derived here, not printed in
the paper. 298.15 K lies inside the fitted range of both EMC (292.7 to 380.6 K) and DMC (285.8 to
428.2 K), but only 5.5 K above the lowest EMC point.

Standard library only.
"""

from __future__ import annotations

import math
import sys

R = 8.314462618  # J/(mol K), CODATA 2018

# (A, B, C, T_min/K, T_max/K) for log10(p/Pa)
ANTOINE = {
    "EMC": (9.3661, 1433.59, -52.250, 292.7, 380.6),
    "DMC": (9.4256, 1406.12, -45.145, 285.8, 428.2),
}

# Kozlova et al., J. Chem. Thermodyn. 40, 1136 (2008), Table 1: transpiration, 274.2 to 304.1 K
KOZLOVA_DMC_DH = (38.02, 0.19)  # kJ/mol


def pressure_pa(solvent: str, t_k: float) -> float:
    a, b, c, _, _ = ANTOINE[solvent]
    return 10.0 ** (a - b / (t_k + c))


def dh_vap_kj_mol(solvent: str, t_k: float) -> float:
    _, b, c, _, _ = ANTOINE[solvent]
    return R * math.log(10.0) * b * t_k**2 / (t_k + c) ** 2 / 1000.0


def boiling_point_k(solvent: str, p_pa: float = 101325.0) -> float:
    a, b, c, _, _ = ANTOINE[solvent]
    return b / (a - math.log10(p_pa)) - c


def in_range(solvent: str, t_k: float) -> bool:
    return ANTOINE[solvent][3] <= t_k <= ANTOINE[solvent][4]


def main(argv: list[str]) -> int:
    t_k = float(argv[1]) if len(argv) > 1 else 298.15
    for s in ANTOINE:
        note = "" if in_range(s, t_k) else "  (outside the fitted range: extrapolation)"
        print(
            f"{s}: p({t_k:.2f} K) = {pressure_pa(s, t_k) / 1000:.4f} kPa, "
            f"dH_vap = {dh_vap_kj_mol(s, t_k):.2f} kJ/mol, "
            f"T_b(101.325 kPa) = {boiling_point_k(s):.2f} K{note}"
        )
    d = dh_vap_kj_mol("DMC", 298.15) - KOZLOVA_DMC_DH[0]
    print(
        f"DMC check at 298.15 K: Goldberg route minus Kozlova ({KOZLOVA_DMC_DH[0]} +/- "
        f"{KOZLOVA_DMC_DH[1]}) = {d:+.2f} kJ/mol"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
