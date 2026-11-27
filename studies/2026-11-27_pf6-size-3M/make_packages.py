"""Packages of the PF6 size map: the sigma of PF6 (P and F) scaled in the 3 M M1 box of SC-4.

    ucmd-builder/.venv/bin/python studies/2026-11-27_pf6-size-3M/make_packages.py

Reads the minimized 3 M package of studies/2026-11-27_density-concentration-M1, writes packages/<name>.ucsys
with the change under provenance, and checks each with the spec validator. The values are probes (README), not
model parameters. The change follows change_sigma_li of the 1 M scan (atom-type sigma times a factor; with the
geometric rule, PF6-PF6 pairs scale by the factor and PF6-other pairs by its square root).
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
SIGMA_PF6 = (0.95, 1.05)
PF6_TYPES = ("PF6.P", "PF6.FP")


def change_sigma_pf6(doc: dict, f: float) -> dict:
    for t in PF6_TYPES:
        doc["forcefield"]["atom_types"][t]["sigma_nm"] *= f
    return {"kind": "lj_sigma_scale", "types": list(PF6_TYPES), "factor": f}


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
        "created_by": "studies/2026-11-27_pf6-size-3M/make_packages.py",
        "created_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "transform": {**transform, "note": "density-map probe, not a model parameter"},
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
    for f in SIGMA_PF6:
        write(f"m1_3.0M_sigmaPF6_x{f:.2f}", lambda d, f=f: change_sigma_pf6(d, f))


if __name__ == "__main__":
    main()
