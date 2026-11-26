"""Verdicts of SC-4 (density over concentration and temperature), exactly as README.md fixes them.

    python3 analyze.py OUT.json        # standard library only

Density from the thermo tables (volume) and the package masses; the box's own concentration from the number of
LiPF6 pairs and the same volume. Unfinished runs stop the script: no partial verdict.
"""

from __future__ import annotations

import json
import math
import statistics as st
import sys
from pathlib import Path

STUDIES = Path(__file__).resolve().parents[1]
GRAM_PER_AMU = 1.66053906660e-24  # CODATA 2018
AVOGADRO = 6.02214076e23  # exact (SI 2019)
CM3_PER_NM3, LITRE_PER_NM3 = 1e-21, 1e-24
ZERO_C = 273.15
# Landesfeind & Gasteiger 2019, SI Eq. S1 / Table S1, EC:EMC 3:7 w:w (ledger landesfeind2019_density_fit_ec_emc_3_7)
P1, P2, P3 = 1.41, 0.0912, -0.00109  # g/cm3, g/cm3 per (mol/L), g/cm3 per K
LIMIT_PCT = 1.5  # criterion 1 (author 2026-11-25)
SETTLE_PCT = 0.3  # criterion 3: halves of the analysed window
SKIP_PS = 1000.0
C_STUDY, T_STUDY = "2026-11-27_density-concentration-M1", "2026-11-27_density-temperature-M1"
ANCHOR = ("2026-11-25_timestep-1M-0p5fs", ("base_s1", "base_s2", "base_s3"), "T20C", 1500.0, 5000.0)
POINTS = [  # (label, study, run, condition, skip ps, end ps)
    ("0.1 M, 20 C", C_STUDY, "m1_0.1M", "T20C", SKIP_PS, 3000.0),
    ("2 M, 20 C", C_STUDY, "m1_2.0M", "T20C", SKIP_PS, 3000.0),
    ("3 M, 20 C", C_STUDY, "m1_3.0M", "T20C", SKIP_PS, 3000.0),
    ("1 M, 10 C", T_STUDY, "base_s1", "T10C", SKIP_PS, 3000.0),
    ("1 M, 50 C", T_STUDY, "base_s1", "T50C", SKIP_PS, 3000.0),
]


def reference(c_mol_l: float, t_k: float) -> float:
    return P1 + P2 * c_mol_l + P3 * t_k


def composition(package: Path) -> tuple[float, int]:
    """Mass (amu) and number of LiPF6 pairs (the count of the Li component)."""
    doc = json.loads((package / "system.json").read_text())
    mass = sum(
        c["count"] * sum(a["mass_amu"] for a in doc["molecule_types"][c["molecule_type"]]["atoms"])
        for c in doc["components"]
    )
    pairs = [c["count"] for c in doc["components"] if c["molecule_type"] == "Li"]
    if len(pairs) != 1:
        raise SystemExit(f"{package}: expected one Li component")
    return mass, pairs[0]


def volumes(run: Path, skip_ps: float, end_ps: float) -> list[float]:
    """nm3 of every thermo row after skip_ps; a restarted run may repeat rows (the last one wins)."""
    rows: dict[int, tuple[float, float]] = {}
    with (run / "out/thermo.tsv").open() as fh:
        names = fh.readline().lstrip("# ").strip().split("\t")
        step, time, vol = (names.index(n) for n in ("step", "time_ps", "volume_nm3"))
        for line in fh:
            f = line.split("\t")
            rows[int(f[step])] = (float(f[time]), float(f[vol]))
    ordered = [rows[k] for k in sorted(rows)]
    if not ordered or ordered[-1][0] < end_ps - 1e-3:
        raise SystemExit(f"{run}: not finished")
    v = [x for t, x in ordered if t > skip_ps]
    if not v or not all(map(math.isfinite, v)):
        raise SystemExit(f"{run}: no finite volumes")
    return v


def point(study: str, run: str, cond: str, skip: float, end: float) -> dict:
    base = STUDIES / study
    mass, pairs = composition(base / "systems" / run / "minimized.ucsys")
    v = volumes(base / "runs" / run / cond, skip, end)
    rho = [mass * GRAM_PER_AMU / CM3_PER_NM3 / x for x in v]
    half = len(rho) // 2
    t_k = float(cond[1:-1]) + ZERO_C
    c = pairs / AVOGADRO / (st.fmean(v) * LITRE_PER_NM3)
    r, ref = st.fmean(rho), reference(c, t_k)
    return {"rho": r, "c_mol_l": c, "T_K": t_k, "ref": ref, "dev_pct": 100 * (r / ref - 1),
            "halves_pct": 100 * (st.fmean(rho[half:]) / st.fmean(rho[:half]) - 1)}  # fmt: skip


def anchor() -> dict:
    """1 M, 20 C: the three 0.5 fs runs of SC-1 (5 ns, first 1.5 ns skipped), averaged."""
    study, runs, cond, skip, end = ANCHOR
    pts = [point(study, r, cond, skip, end) for r in runs]
    out = {k: st.fmean(q[k] for q in pts) for k in ("rho", "c_mol_l", "T_K", "ref", "dev_pct")}
    out["halves_pct"] = max((p["halves_pct"] for p in pts), key=abs)
    out["seeds_sd_pct"] = 100 * st.stdev(p["rho"] for p in pts) / out["rho"]
    return out


def judge(p: dict) -> str:
    if abs(p["halves_pct"]) > SETTLE_PCT:
        return "not settled"
    return "pass" if abs(p["dev_pct"]) <= LIMIT_PCT else "FAIL"


def slope(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """Least-squares slope and its SE (from the residuals)."""
    mx, my = st.fmean(xs), st.fmean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True)) / sxx
    res = [y - my - b * (x - mx) for x, y in zip(xs, ys, strict=True)]
    se = math.sqrt(sum(r * r for r in res) / (len(xs) - 2) / sxx) if len(xs) > 2 else math.nan
    return b, se


def main(out_path: str) -> None:
    pts = {label: point(*args) for label, *args in POINTS}
    pts["1 M, 20 C"] = anchor()
    for p in pts.values():
        p["verdict"] = judge(p)
    at20 = sorted((p for k, p in pts.items() if k.endswith("20 C")), key=lambda p: p["c_mol_l"])
    at1m = sorted((p for k, p in pts.items() if k.startswith("1 M")), key=lambda p: p["T_K"])
    b_c, se_c = slope([p["c_mol_l"] for p in at20], [p["rho"] for p in at20])
    b_t, se_t = slope([p["T_K"] for p in at1m], [p["rho"] for p in at1m])
    verdicts = [p["verdict"] for p in pts.values()]
    overall = "FAIL" if "FAIL" in verdicts else "unresolved" if "not settled" in verdicts else "pass"
    result = {"points": pts, "drho_dc": {"value": b_c, "se": se_c, "reference": P2},
              "drho_dT": {"value": b_t, "se": se_t, "reference": P3}, "overall": overall}  # fmt: skip
    Path(out_path).write_text(json.dumps(result, indent=1) + "\n")
    for k, p in pts.items():
        print(f"{k:11s} rho {p['rho']:.4f}  c {p['c_mol_l']:.3f} M  fit {p['ref']:.4f}  {p['dev_pct']:+.2f} %"
              f"  halves {p['halves_pct']:+.2f} %  {p['verdict']}")  # fmt: skip
    print(f"d(rho)/dc = {b_c:.4f} +- {se_c:.4f} g/cm3 per M (reference {P2})")
    print(f"d(rho)/dT = {b_t:.6f} +- {se_t:.6f} g/cm3 per K (reference {P3})")
    print("SC-4:", overall)


if __name__ == "__main__":
    main(sys.argv[1])
