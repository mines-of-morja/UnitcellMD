"""Trial T6, option B: the fit's own pair terms equal spec 0.1.2 pair overrides (ADR 0015, A9).

    tools/oracle/.venv/bin/python docs/research/trials/T6/t6_spec_path.py PKG.ucsys START.xyz \
        [--ec SIGMA_NM EPS_KJMOL] [--emc SIGMA_NM EPS_KJMOL]

t6_fit.py adds option B as a CustomBondForce between Li⁺ and each carbonyl O, with those pairs
excluded from the LJ force. A liquid run instead reads `forcefield.pair_overrides` from the
package. This script writes a copy of PKG with the overrides, loads it through the oracle's spec
path (per-type tables), and compares the energy at START.xyz with t6_fit's at the same q_Li. They
must agree to 1e-9 kJ/mol. The default values are test numbers; after stage 2 the fitted ones are
passed.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t6_fit  # sets up the oracle and ffcheck paths
from li_binding import build_system, total_energy
from oracle import load_topology

TOLERANCE_KJMOL = 1e-9


def read_xyz(path: Path) -> list[list]:
    lines = path.read_text(encoding="utf-8").splitlines()
    n = int(lines[0])
    return [[r[0], *map(float, r[1:4])] for r in map(str.split, lines[2 : 2 + n])]


def with_overrides(pkg: Path, out: Path, pairs: dict[str, tuple[float, float]]) -> None:
    """Copy PKG to OUT with Li⁺–O(carbonyl) overrides for the solvents in `pairs`."""
    shutil.copytree(pkg, out)
    doc = json.loads((out / "system.json").read_text(encoding="utf-8"))
    (li_type,) = {a["type"] for a in doc["molecule_types"]["Li"]["atoms"]}
    overrides = []
    for name, (sigma, epsilon) in pairs.items():
        mt = doc["molecule_types"].get(name)
        if mt is None:
            continue
        o_type = mt["atoms"][t6_fit.carbonyl(mt)]["type"]
        types = [a["type"] for a in mt["atoms"]]
        if types.count(o_type) != 1:  # the override acts on the type, the fit on the atom
            raise SystemExit(f"{name}: carbonyl type {o_type} is shared with other atoms")
        overrides.append({"types": [li_type, o_type], "sigma_nm": sigma, "epsilon_kjmol": epsilon})
    doc["forcefield"]["pair_overrides"] = overrides
    doc["spec_version"] = "0.1.2"
    (out / "system.json").write_text(json.dumps(doc, indent=1), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("package", type=Path)
    ap.add_argument("xyz", type=Path)
    ap.add_argument("--ec", type=float, nargs=2, default=(0.21, 0.9))
    ap.add_argument("--emc", type=float, nargs=2, default=(0.22, 0.7))
    args = ap.parse_args()
    pairs = {"EC": tuple(args.ec), "EMC": tuple(args.emc)}
    c = t6_fit.load_cluster(args.package, 0)  # n_ec only labels the cluster in t6_fit
    x = t6_fit.positions(c, read_xyz(args.xyz))
    fit_energy = total_energy(t6_fit.system_for(c, {"pairs": pairs}), x)
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / args.package.name
        with_overrides(args.package, copy, pairs)
        top = load_topology(copy)
        assert top.pairs is not None
    q = top.charges_e.copy()
    q[c.pf6] = 0.0
    q[c.li] = t6_fit.Q_LI
    spec = dataclasses.replace(top, cell_nm=None, charges_e=q)
    spec_energy = total_energy(build_system(spec), x)
    diff = abs(spec_energy - fit_energy)
    print(
        json.dumps(
            {
                "package": args.package.name,
                "pairs": pairs,
                "fit_route_kjmol": fit_energy,
                "spec_route_kjmol": spec_energy,
                "difference_kjmol": diff,
                "tolerance_kjmol": TOLERANCE_KJMOL,
            },
            indent=1,
        )
    )
    if diff > TOLERANCE_KJMOL:
        raise SystemExit("FAIL: the spec path differs from the fit's pair terms")


if __name__ == "__main__":
    main()
