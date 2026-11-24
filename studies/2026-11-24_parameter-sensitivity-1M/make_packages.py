"""Packages of the sensitivity scan: one knob changed in the M1 package of trial T2.

    ucmd-builder/.venv/bin/python studies/2026-11-24_parameter-sensitivity-1M/make_packages.py

Reads the minimized M1 packages of studies/2026-11-21_trial-t2-ec-model-1M (seeds 1-3), writes
packages/<name>.ucsys, each with the change recorded under provenance, and checks every package
with the spec validator. The values are probes (README), not model parameters. Positions are
those of the M1 package; every variant uses seed 1.
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
os.environ.setdefault("UCMD_SPEC_DIR", str(ROOT / "spec"))
from ucmd_spec.system import validate_system_package

T2 = ROOT / "studies/2026-11-21_trial-t2-ec-model-1M/systems"
ZETA0 = 0.75
ZETA = (0.65, 0.70, 0.80, 0.85)
SIGMA_LI = (0.90, 0.95, 1.05, 1.10)
EPS_EMC = (0.85, 0.90, 0.95, 1.05)


def change_zeta(doc: dict, zeta: float) -> dict:
    for ion in ("Li", "PF6"):
        for a in doc["molecule_types"][ion]["atoms"]:
            a["charge_e"] *= zeta / ZETA0
    return {"kind": "ion_charge_scale", "from": ZETA0, "to": zeta, "molecules": ["Li", "PF6"]}


def change_sigma_li(doc: dict, f: float) -> dict:
    doc["forcefield"]["atom_types"]["Li.Li"]["sigma_nm"] *= f
    return {"kind": "lj_sigma_scale", "types": ["Li.Li"], "factor": f}


def change_eps_emc(doc: dict, f: float) -> dict:
    types = [t for t in doc["forcefield"]["atom_types"] if t.startswith("EMC.")]
    for t in types:
        doc["forcefield"]["atom_types"][t]["epsilon_kjmol"] *= f
    return {"kind": "lj_epsilon_scale", "types": types, "factor": f}


def write(name: str, seed: int, change=None) -> None:
    src = T2 / f"t2_m1_s{seed}/minimized.ucsys"
    out = HERE / "packages" / f"{name}.ucsys"
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(src, out)
    doc = json.loads((out / "system.json").read_text(encoding="utf-8"))
    doc["name"] = name
    transform = change(doc) if change else {"kind": "none"}
    doc["provenance"] = {
        "created_by": "studies/2026-11-24_parameter-sensitivity-1M/make_packages.py",
        "created_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "transform": {**transform, "note": "sensitivity probe, not a model parameter"},
        "derived_from": doc["provenance"],
    }
    (out / "system.json").write_text(
        json.dumps(doc, indent=1, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8"
    )
    report = validate_system_package(out)
    if not report.ok:
        raise SystemExit(f"{name}: {report.error}")
    total = sum(
        c["count"] * sum(a["charge_e"] for a in doc["molecule_types"][c["molecule_type"]]["atoms"])
        for c in doc["components"]
    )
    if abs(total) > 1e-9:
        raise SystemExit(f"{name}: net charge {total}")
    print(f"{name}: ok, {transform}")


def main() -> None:
    for seed in (1, 2, 3):
        write(f"base_s{seed}", seed)
    for z in ZETA:
        write(f"zeta_{z:.2f}", 1, lambda d, z=z: change_zeta(d, z))
    for f in SIGMA_LI:
        write(f"sigmaLi_x{f:.2f}", 1, lambda d, f=f: change_sigma_li(d, f))
    for f in EPS_EMC:
        write(f"epsEMC_x{f:.2f}", 1, lambda d, f=f: change_eps_emc(d, f))


if __name__ == "__main__":
    main()
