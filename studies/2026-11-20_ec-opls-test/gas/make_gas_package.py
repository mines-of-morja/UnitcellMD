"""One molecule of the liquid package, alone and non-periodic: the gas phase for ΔH_vap.

    python3 gas/make_gas_package.py external/build/<pkg> external/build/<pkg>-gas.ucsys

Same molecule type and force field as the liquid (copied, not retyped). The first molecule's
minimized coordinates are the start. Spec 0.1 allows non-periodic packages (periodicity all
false, cell_nm null), like the fixture water-2.
"""

import datetime
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
doc = json.loads((src / "system.json").read_text())
if len(doc["components"]) != 1:
    sys.exit("expected a one-component liquid")
name = doc["components"][0]["molecule_type"]
n = len(doc["molecule_types"][name]["atoms"])
x = np.load(src / "positions.npy")[:n]
x = x - x.mean(axis=0)
doc.update(
    name=f"{doc['name']}-gas",
    periodicity=[False, False, False],
    cell_nm=None,
    components=[{"molecule_type": name, "count": 1}],
    atom_count=n,
)
doc["provenance"] = {
    "created_by": "studies/2026-11-20_ec-opls-test/gas/make_gas_package.py",
    "created_utc": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "derived_from": {
        "package": str(src),
        "system_json_sha256": hashlib.sha256((src / "system.json").read_bytes()).hexdigest(),
    },
    "notes": "first molecule of the liquid package, centred; gas phase for the enthalpy of vaporization",
}
dst.mkdir(parents=True)
(dst / "system.json").write_text(json.dumps(doc, indent=1, sort_keys=True))
np.save(dst / "positions.npy", x)
print(f"wrote {dst}: 1 {name}, {n} atoms, not periodic")
