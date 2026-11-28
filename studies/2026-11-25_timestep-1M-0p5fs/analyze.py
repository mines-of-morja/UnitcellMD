"""Verdicts of SC-1 (timestep convergence), exactly as README.md fixes them.

    HDF5_USE_FILE_LOCKING=FALSE python3 analyze.py OUT.json

Standard library only; D comes from `ucmd-analyze diffusion`. Density from the thermo tables
(volume) and the package masses. Arms that are not finished stop the script: no partial verdict.
"""

from __future__ import annotations

import json
import math
import statistics as st
import subprocess
import sys
from pathlib import Path

STUDIES = Path(__file__).resolve().parents[1]
ANALYZE = STUDIES.parent / "ucmd-analysis/.venv/bin/ucmd-analyze"
GRAM_PER_AMU, CM3_PER_NM3 = 1.66053906660e-24, 1e-21  # CODATA 2018; definition
MATTERS_PCT, MATTERS_SE = 0.1, 2.0  # README, criterion 1 (docs/tasks.toml, SC-1)
T95_4 = 2.776  # two-sided 95 %, 4 degrees of freedom (reported next to the verdict)
PAIRS = {
    # system: (arm at 1 fs, arm at 0.5 fs, runs, condition, skip ps, end ps, D species)
    "1M": ("2026-11-24_parameter-sensitivity-1M", "2026-11-25_timestep-1M-0p5fs",
           ("base_s1", "base_s2", "base_s3"), "T20C", 1500.0, 5000.0, ("Li", "PF6", "EC", "EMC")),
    "EMC": ("2026-11-25_timestep-emc-1fs", "2026-11-25_timestep-emc-0p5fs",
            ("emc_500_s1", "emc_500_s2", "emc_500_s3"), "T25C", 500.0, 2000.0, ("EMC",)),
    "water": ("2026-11-25_water-npt-gpu", "2026-11-25_timestep-water-0p5fs",
              ("spcfw_512_s1", "spcfw_512_s2", "spcfw_512_s3"), "T25.01C", 200.0, 1000.0, ()),
}  # fmt: skip
QUARTER = ("2026-11-25_timestep-water-0p25fs", "spcfw_512_s1", "T25.01C", 200.0, 1000.0)


def mass_amu(package: Path) -> float:
    doc = json.loads((package / "system.json").read_text())
    return sum(
        comp["count"] * atom["mass_amu"]
        for comp in doc["components"]
        for atom in doc["molecule_types"][comp["molecule_type"]]["atoms"]
    )


def densities(run: Path, package: Path, skip_ps: float, end_ps: float) -> list[float]:
    """g/cm3 of every thermo row after skip_ps; a restarted run may repeat rows (last one wins)."""
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
    factor = mass_amu(package) * GRAM_PER_AMU / CM3_PER_NM3
    rho = [factor / v for t, v in ordered if t > skip_ps]
    if not all(map(math.isfinite, rho)):
        raise SystemExit(f"{run}: density is not finite")
    return rho


def one(study: str, run: str, cond: str, skip: float, end: float) -> dict:
    base = STUDIES / study
    rho = densities(base / "runs" / run / cond, base / "systems" / run / "minimized.ucsys", skip, end)
    half = len(rho) // 2
    return {"rho": st.fmean(rho), "halves": st.fmean(rho[half:]) - st.fmean(rho[:half])}


def diffusion(study: str, run: str, cond: str, skip: float, temp: float, species) -> dict:
    traj = STUDIES / study / "runs" / run / cond / "out/trajectory.h5"
    out = {}
    for name in species:
        cmd = [str(ANALYZE), "diffusion", str(traj), "--temperature-K", str(temp),
               "--species", name, "--skip-ps", str(skip)]  # fmt: skip
        doc = json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)
        out[name] = doc[f"D_{name}_m2_per_s"]["mean"]
    return out


def compare(slow: list[float], fast: list[float]) -> dict:
    """0.5 fs minus 1 fs; s pooled over the two arms, SE = s sqrt(1/n1 + 1/n2)."""
    dof = len(slow) + len(fast) - 2
    s2 = ((len(slow) - 1) * st.variance(slow) + (len(fast) - 1) * st.variance(fast)) / dof
    se = math.sqrt(s2 * (1 / len(slow) + 1 / len(fast)))
    d, ref = st.fmean(fast) - st.fmean(slow), st.fmean(slow)
    return {"diff": d, "se": se, "diff_pct": 100 * d / ref, "se_pct": 100 * se / ref,
            "ci95_pct": [100 * (d - T95_4 * se) / ref, 100 * (d + T95_4 * se) / ref]}  # fmt: skip


def verdict(c: dict) -> str:
    d, se = abs(c["diff_pct"]), c["se_pct"]
    if d > MATTERS_SE * se and d > MATTERS_PCT:
        return "matters"
    if d + MATTERS_SE * se <= MATTERS_PCT:
        return "below 0.1 %"
    return "unresolved"


def timestep(verdicts: dict[str, str]) -> str:
    """README, criterion 2: only the two liquids of the electrolyte decide."""
    v = [verdicts["1M"], verdicts["EMC"]]
    if "matters" in v:
        return "0.5 fs (or a multiple time step): the author decides which"
    if v == ["below 0.1 %", "below 0.1 %"]:
        return "1 fs"
    return "unresolved: the author decides; no seed is added after looking"


def main(out_path: str) -> None:
    result: dict = {"density": {}, "D": {}, "verdict": {}}
    for name, (slow, fast, runs, cond, skip, end, species) in PAIRS.items():
        arms = {a: [one(s, r, cond, skip, end) for r in runs] for a, s in (("1", slow), ("0.5", fast))}
        c = compare([r["rho"] for r in arms["1"]], [r["rho"] for r in arms["0.5"]])
        result["density"][name] = {"runs": arms, **c}
        result["verdict"][name] = verdict(c)
        if species:
            temp = float(cond[1:-1]) + 273.15
            d = {a: [diffusion(s, r, cond, skip, temp, species) for r in runs]
                 for a, s in (("1", slow), ("0.5", fast))}  # fmt: skip
            result["D"][name] = {
                sp: compare([math.log(x[sp]) for x in d["1"]], [math.log(x[sp]) for x in d["0.5"]])
                | {"runs": {a: [x[sp] for x in d[a]] for a in d}}
                for sp in species
            }
    result["water_0.25fs"] = one(*QUARTER)
    result["timestep"] = timestep(result["verdict"])
    Path(out_path).write_text(json.dumps(result, indent=1) + "\n")
    for name, c in result["density"].items():
        print(f"{name:6s} rho(0.5) - rho(1) = {c['diff']:+.5f} +- {c['se']:.5f} g/cm3 = "
              f"{c['diff_pct']:+.3f} +- {c['se_pct']:.3f} % (1 SE): {result['verdict'][name]}")  # fmt: skip
        for a, runs in c["runs"].items():
            print(f"         {a:>3s} fs " + "  ".join(f"{r['rho']:.5f} (halves {r['halves']:+.5f})" for r in runs))
    for name, sp in result["D"].items():
        for k, c in sp.items():
            print(f"{name:6s} D({k}): ln D(0.5) - ln D(1) = {c['diff']:+.3f} +- {c['se']:.3f} (1 SE)")
    print(f"water 0.25 fs (one run): rho {result['water_0.25fs']['rho']:.5f}")
    print("timestep for SC-4 and T4:", result["timestep"])


if __name__ == "__main__":
    main(sys.argv[1])
