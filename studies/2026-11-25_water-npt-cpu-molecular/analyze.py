"""Verdicts of SC-3 test 2, exactly as README.md fixes them. Standard library only.

    python3 analyze.py            # reads the three arms next to this folder
"""

from __future__ import annotations

import json
import math
import statistics as st
from pathlib import Path

ARMS = {
    "A": "2026-11-25_water-npt-cpu-atomic",
    "B": "2026-11-25_water-npt-cpu-molecular",
    "G": "2026-11-25_water-npt-gpu",
}
SEEDS = ("spcfw_512_s1", "spcfw_512_s2", "spcfw_512_s3")
SKIP_PS, END_PS = 200.0, 1000.0
T95_6 = 2.447  # two-sided 95 %, 6 degrees of freedom
T95_2 = 4.303  # two-sided 95 %, 2 degrees of freedom (one arm)
TARGET_BAR = 1.01325
PREDICTED, RANGE = 0.0058, (0.0045, 0.0078)  # g/cm3
GRAM_PER_AMU, CM3_PER_NM3 = 1.66053906660e-24, 1e-21
BLOCKS = 5
DRIFT_SE = 7.0  # 3.5 sigma of the difference of two halves
P_LIMIT_BAR = 65.0  # half the bias that option B removes


def mass_amu(package: Path) -> float:
    doc = json.loads((package / "system.json").read_text())
    total = 0.0
    for comp in doc["components"]:
        mol = doc["molecule_types"][comp["molecule_type"]]
        total += comp["count"] * sum(a["mass_amu"] for a in mol["atoms"])
    return total


def table(path: Path) -> list[dict[str, float]]:
    with path.open() as fh:
        names = fh.readline().lstrip("# ").strip().split("\t")
        rows = [dict(zip(names, map(float, line.split("\t")), strict=True)) for line in fh]
    if not rows or rows[-1]["time_ps"] < END_PS - 1e-6:
        raise SystemExit(f"{path}: not finished")
    return [r for r in rows if r["time_ps"] > SKIP_PS]


def run_summary(folder: Path, system: Path) -> dict:
    rows = table(folder / "out/thermo.tsv")
    factor = mass_amu(system) * GRAM_PER_AMU / CM3_PER_NM3
    rho = [factor / r["volume_nm3"] for r in rows]
    half = len(rho) // 2
    size = len(rho) // BLOCKS
    blocks = [st.fmean(rho[k * size : (k + 1) * size]) for k in range(BLOCKS)]
    se = st.stdev(blocks) / math.sqrt(BLOCKS)
    halves = st.fmean(rho[half:]) - st.fmean(rho[:half])
    out = {
        "rho": st.fmean(rho),
        "block_se": se,
        "halves": halves,
        "pressure": st.fmean(p) if (p := finite(rows, "pressure_bar")) else math.nan,
    }
    if p := finite(rows, "pressure_molecular_bar"):
        out["p_mol"] = st.fmean(p)
    return out


def finite(rows: list[dict[str, float]], column: str) -> list[float]:
    """The evaluated values of a pressure column (spec 0.1.3: nan = not evaluated)."""
    return [r[column] for r in rows if column in r and math.isfinite(r[column])]


def verdict(arms: dict[str, list[dict]]) -> list[str]:
    out = []
    rho = {a: [r["rho"] for r in runs] for a, runs in arms.items()}
    p_mol = [r["p_mol"] for r in arms["B"]]
    se_p = st.stdev(p_mol) / math.sqrt(len(p_mol))
    ok = abs(st.fmean(p_mol) - TARGET_BAR) <= T95_2 * se_p
    sharp = T95_2 * se_p <= P_LIMIT_BAR
    out.append(
        f"1 barostat check: <P_mol> = {st.fmean(p_mol):.1f} +- {se_p:.1f} bar (SE, 3 seeds): "
        + ("pass" if ok and sharp else "unresolved" if ok else "FAIL")
    )
    if not (ok and sharp):
        return [*out, "nothing else is read"]
    runs = [r for rs in arms.values() for r in rs]
    pooled = math.sqrt(st.fmean(r["block_se"] ** 2 for r in runs))
    if drifting := [r for r in runs if abs(r["halves"]) > DRIFT_SE * pooled]:
        return [*out, f"5 {len(drifting)} run(s) drift: 2 and 3 are not judged"]
    s2 = st.fmean(st.variance(v) for v in rho.values())
    limit = T95_6 * math.sqrt(2 * s2 / 3)
    for number, (x, y) in ((2, ("A", "B")), (3, ("B", "G"))):
        d = st.fmean(rho[x]) - st.fmean(rho[y])
        head = f"{number} rho_{x} - rho_{y} = {d:+.5f} (95 % limit {limit:.5f}) g/cm3: "
        if limit > PREDICTED / 2:
            out.append(head + "unresolved")
        elif number == 3:
            out.append(head + ("consistent" if abs(d) <= limit else "DIFFERENT"))
        elif abs(d) <= limit:
            out.append(head + "effect not seen")
        else:
            inside = RANGE[0] <= d <= RANGE[1]
            out.append(head + ("effect confirmed" if inside else "effect of another size"))
    return out


def main() -> None:
    studies = Path(__file__).resolve().parents[1]
    arms: dict[str, list[dict]] = {}
    for arm, name in ARMS.items():
        arms[arm] = []
        for seed in SEEDS:
            study = studies / name
            r = run_summary(
                study / "runs" / seed / "T25.01C", study / "systems" / seed / "built.ucsys"
            )
            arms[arm].append(r)
            extra = f"  P_mol {r['p_mol']:7.1f}" if "p_mol" in r else ""
            print(
                f"{arm} {seed}: rho {r['rho']:.5f} +- {r['block_se']:.5f}  halves {r['halves']:+.5f}"
                f"  P {r['pressure']:7.1f}{extra}"
            )
    print("\n".join(verdict(arms)))


if __name__ == "__main__":
    main()
