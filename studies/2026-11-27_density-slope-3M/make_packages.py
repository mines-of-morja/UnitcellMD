"""Packages of the 3 M density map: one knob of the 1 M scan changed in the 3 M M1 box of SC-4.

    ucmd-builder/.venv/bin/python studies/2026-11-27_density-slope-3M/make_packages.py

Reads the minimized 3 M package of studies/2026-11-27_density-concentration-M1, writes packages/<name>.ucsys
with the change under provenance, and checks each with the spec validator. The values are the scan's probes
(README), not model parameters. The change functions are those of the 1 M scan, unchanged.
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

SRC = ROOT / "studies/2026-11-27_density-concentration-M1/systems/m1_3.0M/minimized.ucsys"
ZETA0 = 0.75
ZETA = (0.65, 0.85)
EPS_EMC = (0.85,)


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


def write(name: str, change=None) -> None:
    src = SRC
    out = HERE / "packages" / f"{name}.ucsys"
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(src, out)
    doc = json.loads((out / "system.json").read_text(encoding="utf-8"))
    doc["name"] = name
    transform = change(doc) if change else {"kind": "none"}
    doc["provenance"] = {
        "created_by": "studies/2026-11-27_density-slope-3M/make_packages.py",
        "created_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "transform": {**transform, "note": "density-map probe (values of the 1 M scan), not a model parameter"},
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
    for z in ZETA:
        write(f"m1_3.0M_zeta_{z:.2f}", lambda d, z=z: change_zeta(d, z))
    for f in EPS_EMC:
        write(f"m1_3.0M_epsEMC_x{f:.2f}", lambda d, f=f: change_eps_emc(d, f))


if __name__ == "__main__":
    main()
