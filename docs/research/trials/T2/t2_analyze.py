"""Trial T2 (docs/research/trials/T2-ec-model-1M.md): analysis and the pre-registered decision.

Run from the workspace root with the ucmd-analysis venv:

    HDF5_USE_FILE_LOCKING=FALSE ucmd-analysis/.venv/bin/python \
        docs/research/trials/T2/t2_analyze.py OUT.json

Per run (last 4 ns): carbonyl O of EC and EMC and PF6- (P) within 0.28 nm and 0.516 nm of Li+,
mean contacts per Li+ (`ucmd-analyze shell`, cutoffs given explicitly for every partner); density;
D and kappa_NE (`ucmd-analyze transport`, reported only). Mean +- SE over the three seeds.

Run-length diagnostic (author, 2026-11-21: a long run must show it was worth it): the EC
first-shell count per Li+ in 250 ps windows over the whole run, from the first frame. The
equilibration time is the start of the first window after which every window lies within
+-10 % of the run's final-4-ns mean. It is reported, not used for the decision, and sets the
justified length of later 1 M shell runs.
"""

from __future__ import annotations

import json
import math
import statistics as st
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
STUDY = ROOT / "studies/2026-11-21_trial-t2-ec-model-1M"
ANALYZE = ROOT / "ucmd-analysis/.venv/bin/ucmd-analyze"
SKIP_PS = 1000.0
DRS_BOUND, DRS_ERR = 2.2, 0.1  # bound EC per Li+, Self, Hahn, Persson 2024 (our reading)
PARTNERS = ["EC:O:1", "EMC:O:1", "PF6:P"]


def analyze(*args: str) -> dict:
    out = subprocess.run([str(ANALYZE), *args], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def shell(traj: Path, r_nm: float) -> dict:
    cmd = ["shell", str(traj), "--skip-ps", str(SKIP_PS), "--a", "Li:Li"]
    for b in PARTNERS:
        cmd += ["--b", b]
    for _ in PARTNERS:
        cmd += ["--r-cut-nm", str(r_nm)]
    return analyze(*cmd)["mean_contacts"]


def convergence(traj: Path, window_ps: float = 250.0, tol: float = 0.10) -> dict:
    """EC carbonyl O within 0.28 nm per Li+, in windows over the whole run."""
    from ucmd_analysis.association import contacts
    from ucmd_analysis.io import read_h5md

    t = read_h5md(traj)
    a = t.system.atoms_where("Li", "Li")
    b = t.system.atoms_where("EC", "O", bonded=1)
    per_frame = contacts(t.positions_nm, t.boxes_nm, a, b, 0.28).sum(axis=2).mean(axis=1)
    dt = float(t.times_ps[1] - t.times_ps[0])
    n = max(1, round(window_ps / dt))
    starts = list(range(0, len(per_frame) - n + 1, n))
    means = [float(per_frame[i : i + n].mean()) for i in starts]
    final = float(per_frame[t.times_ps >= t.times_ps[0] + SKIP_PS].mean())
    ok = [abs(m - final) <= tol * final for m in means]
    t_eq = next((starts[i] * dt for i in range(len(ok)) if all(ok[i:])), None)  # None: not reached
    return {
        "window_ps": n * dt,
        "window_start_ps": [i * dt for i in starts],
        "EC_first_shell_per_window": means,
        "final_4ns_mean": final,
        "tolerance": tol,
        "equilibration_ps": t_eq,
    }


def mean_se(x: list[float]) -> tuple[float, float]:
    return st.fmean(x), (st.stdev(x) / math.sqrt(len(x)) if len(x) > 1 else float("nan"))


def main(out_path: str) -> None:
    runs: dict[str, dict] = {}
    for model in ("m0", "m1"):
        for seed in (1, 2, 3):
            name = f"t2_{model}_s{seed}"
            run = STUDY / "runs" / name / "T20C"
            status = json.loads((run / "status.json").read_text())
            if status.get("state") != "done":
                raise SystemExit(f"{name} is {status.get('state')}, not done")
            traj = run / "out/trajectory.h5"
            first, wide = shell(traj, 0.28), shell(traj, 0.516)
            dens = analyze("density", str(traj), "--skip-ps", str(SKIP_PS))
            tr = analyze("transport", str(traj), "--temperature-K", "293.15", "--cation", "Li",
                         "--anion", "PF6", "--skip-ps", str(SKIP_PS))  # fmt: skip
            runs[name] = {
                "model": model.upper(),
                "first_shell_0.28nm": first,
                "within_0.516nm": wide,
                "density": dens,
                "reported_only": {k: tr[k] for k in tr if k.startswith(("D_", "kappa_NE"))},
                "engine": status.get("engine"),
                "convergence": convergence(traj),
            }
    summary = {}
    for model in ("M0", "M1"):
        sel = [r for r in runs.values() if r["model"] == model]
        summary[model] = {
            f"{key}_{p}": mean_se([r[key][p] for r in sel])
            for key in ("first_shell_0.28nm", "within_0.516nm")
            for p in PARTNERS
        }
    ec0, se0 = summary["M0"]["first_shell_0.28nm_EC:O:1"]
    ec1, se1 = summary["M1"]["first_shell_0.28nm_EC:O:1"]
    se1_comb = math.hypot(se1, DRS_ERR)
    over = ec1 - DRS_BOUND > 2 * se1_comb
    closer = abs(ec1 - DRS_BOUND) < abs(ec0 - DRS_BOUND)
    same = abs(ec1 - ec0) <= 2 * math.hypot(se0, se1)
    if over:
        verdict = "rule 2: M1 exceeds the DRS bound; neither passes; next: pair-specific Li-O term"
    elif closer and not same:
        verdict = "rule 1: M1 replaces M0 as the EC model"
    elif same and ec0 < DRS_BOUND and ec1 < DRS_BOUND:
        verdict = "rule 3: no difference at 1 M; M0 stays; shell deficit passed to M2/M3"
    else:
        verdict = "no rule applies cleanly; report to the author"
    result = {
        "plan": "docs/research/trials/T2-ec-model-1M.md",
        "skip_ps": SKIP_PS,
        "drs_bound": [DRS_BOUND, DRS_ERR],
        "runs": runs,
        "summary_mean_se": summary,
        "decision": {
            "EC_first_shell_M0": [ec0, se0],
            "EC_first_shell_M1": [ec1, se1],
            "M1_exceeds_bound_by_2se": over,
            "M1_closer_to_bound": closer,
            "difference_within_2se": same,
            "verdict": verdict,
        },
        "run_length": {
            "equilibration_ps_per_run": {
                k: r["convergence"]["equilibration_ps"] for k, r in runs.items()
            },
            "longest_ps": (
                None
                if any(r["convergence"]["equilibration_ps"] is None for r in runs.values())
                else max(r["convergence"]["equilibration_ps"] for r in runs.values())
            ),
        },
    }
    Path(out_path).write_text(json.dumps(result, indent=1))
    print(
        json.dumps({"decision": result["decision"], "run_length": result["run_length"]}, indent=1)
    )


if __name__ == "__main__":
    main(sys.argv[1])
