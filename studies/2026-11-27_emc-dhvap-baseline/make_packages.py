"""Gas-phase packages for the EMC enthalpy of vaporization: one molecule of SC-1's EMC liquid, non-periodic.

    ucmd-builder/.venv/bin/python studies/2026-11-27_emc-dhvap-baseline/make_packages.py

Follows studies/2026-11-20_ec-opls-test/gas/make_gas_package.py: same molecule type and force field (copied, not
retyped), the first molecule's minimized coordinates, centred. Three copies (gas_s1..s3) only so that the study
driver gives each run its own seed. Checked with the spec validator.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import shutil
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
os.environ.setdefault("UCMD_SPEC_DIR", str(ROOT / "spec"))
from ucmd_spec.system import validate_system_package

SRC = ROOT / "studies/2026-11-25_timestep-emc-1fs/systems/emc_500_s1/minimized.ucsys"


def main() -> None:
    doc = json.loads((SRC / "system.json").read_text())
    if len(doc["components"]) != 1:
        raise SystemExit("expected a one-component liquid")
    name = doc["components"][0]["molecule_type"]
    n = len(doc["molecule_types"][name]["atoms"])
    x = np.load(SRC / "positions.npy")[:n]
    x = x - x.mean(axis=0)
    src_sha = hashlib.sha256((SRC / "system.json").read_bytes()).hexdigest()
    for s in (1, 2, 3):
        out = HERE / "packages" / f"emc_gas_s{s}.ucsys"
        if out.exists():
            shutil.rmtree(out)
        g = json.loads(json.dumps(doc))
        g.update(name=f"emc_gas_s{s}", periodicity=[False, False, False], cell_nm=None,
                 components=[{"molecule_type": name, "count": 1}], atom_count=n)  # fmt: skip
        g["provenance"] = {
            "created_by": "studies/2026-11-27_emc-dhvap-baseline/make_packages.py",
            "created_utc": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "derived_from": {"package": str(SRC.relative_to(ROOT)), "system_json_sha256": src_sha},
            "notes": "first molecule of the liquid package, centred; gas phase for the enthalpy of vaporization",
        }
        out.mkdir(parents=True)
        (out / "system.json").write_text(json.dumps(g, indent=1, sort_keys=True))
        np.save(out / "positions.npy", x)
        report = validate_system_package(out)
        if not report.ok:
            raise SystemExit(f"{out.name}: {report.error}")
        print(f"{out.name}: ok, 1 {name}, {n} atoms, not periodic")


if __name__ == "__main__":
    main()
