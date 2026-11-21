"""Gas-phase Li⁺–solvent binding energies from QM (layer 0, docs/research/forcefield-strategy.md).

Runs inside the Psi4 image (tools/qm/Dockerfile):

    docker run --rm -u "$(id -u):$(id -g)" -e HOME=/tmp -e USER=psi4 -v "$PWD:/work" -w /work ucmd-psi4:1.9.1 \
        python li_binding_qm.py START.xyz [START.xyz ...] --out results.json

Each START.xyz holds Li⁺ (first atom) and one solvent molecule, e.g. the force-field minimum
written by tools/ffcheck/li_binding.py --xyz. For each file:
- the complex (charge +1) and the solvent alone (from the complex geometry without Li) are
  optimized at METHOD/BASIS;
- E_bind = E(Li⁺·S) − E(S) − E(Li⁺), all at their own optimized geometries; the counterpoise
  correction is reported separately (Boys–Bernardi, at the complex geometry, fragment
  relaxation not included).
The default level, MP2/aug-cc-pVTZ on MP2/aug-cc-pVTZ geometries, is one of the levels in
Olguin et al., PCCP 18, 164 (2016), Table 1, so EC and DMC check the setup against their numbers
before EMC (not in their table) is trusted.

Validation only, like tools/oracle: nothing in the components imports it. Energies are reported
in kJ/mol (spec units) and kcal/mol (the literature's), converted from hartree with CODATA 2018.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import psi4

# CODATA 2018 (spec/units.md): hartree energy 4.3597447222071e-18 J, N_A 6.02214076e23 /mol
KJMOL_PER_HARTREE = 4.3597447222071e-18 * 6.02214076e23 / 1e3
KCAL_IN_KJ = 4.184  # thermochemical calorie (exact)


def read_xyz(path: Path) -> list[tuple[str, float, float, float]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    n = int(lines[0])
    out = []
    for line in lines[2 : 2 + n]:
        el, x, y, z = line.split()[:4]
        out.append((el, float(x), float(y), float(z)))
    return out


def molecule(atoms, charge: int, name: str) -> psi4.core.Molecule:
    body = "\n".join(f"{el} {x:.8f} {y:.8f} {z:.8f}" for el, x, y, z in atoms)
    m = psi4.geometry(f"{charge} 1\n{body}\nunits angstrom\nno_reorient\nno_com\n", name=name)
    return m


def optimized_energy(m: psi4.core.Molecule, method: str) -> float:
    psi4.set_options({"geom_maxiter": 200})
    return float(psi4.optimize(method, molecule=m))


def run_one(path: Path, method: str, basis: str) -> dict:
    atoms = read_xyz(path)
    if atoms[0][0] != "Li":
        raise ValueError(f"{path}: the first atom must be Li")
    psi4.set_options({"basis": basis, "scf_type": "df", "mp2_type": "df", "freeze_core": True})
    t0 = time.time()
    cplx = molecule(atoms, +1, "complex")
    e_c = optimized_energy(cplx, method)
    geom = cplx.save_string_xyz()
    solv = molecule(atoms[1:], 0, "solvent")
    e_s = optimized_energy(solv, method)
    li = molecule([atoms[0]], +1, "li")
    e_li = float(psi4.energy(method, molecule=li))
    # counterpoise at the optimized complex geometry: fragment 1 = Li+, fragment 2 = solvent
    xyz = [line.split() for line in cplx.save_string_xyz().splitlines()[1:]]
    frag = "\n".join(" ".join(r[:4]) for r in xyz[:1])
    rest = "\n".join(" ".join(r[:4]) for r in xyz[1:])
    dimer = psi4.geometry(
        f"1 1\n{frag}\n--\n0 1\n{rest}\nunits angstrom\nno_reorient\nno_com\n", name="cp"
    )
    e_cp = float(psi4.energy(method, molecule=dimer, bsse_type="cp"))  # interaction, CP
    e_bind = (e_c - e_s - e_li) * KJMOL_PER_HARTREE
    d_li_o = min(
        ((float(r[1]) - float(xyz[0][1])) ** 2 + (float(r[2]) - float(xyz[0][2])) ** 2
         + (float(r[3]) - float(xyz[0][3])) ** 2) ** 0.5
        for r in xyz[1:] if r[0].upper() == "O"
    )  # fmt: skip
    return {
        "start": path.name,
        "method": method,
        "basis": basis,
        "freeze_core": True,
        "e_complex_hartree": e_c,
        "e_solvent_hartree": e_s,
        "e_li_hartree": e_li,
        "e_bind_kjmol": round(e_bind, 3),
        "e_bind_kcalmol": round(e_bind / KCAL_IN_KJ, 3),
        "e_int_cp_at_complex_kjmol": round(e_cp * KJMOL_PER_HARTREE, 3),
        "e_int_cp_at_complex_kcalmol": round(e_cp * KJMOL_PER_HARTREE / KCAL_IN_KJ, 3),
        "li_o_angstrom": round(d_li_o, 4),
        "complex_xyz": geom,
        "wall_s": round(time.time() - t0, 1),
        "psi4": psi4.__version__,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("starts", nargs="+", type=Path)
    ap.add_argument("--method", default="mp2")
    ap.add_argument("--basis", default="aug-cc-pvtz")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--memory", default="6 GB")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    psi4.set_num_threads(args.threads)
    psi4.set_memory(args.memory)
    rows = json.loads(args.out.read_text()) if args.out.exists() else []
    done = {(r["start"], r["method"], r["basis"]) for r in rows}
    for p in args.starts:
        if (p.name, args.method, args.basis) in done:
            continue
        psi4.core.set_output_file(str(args.out.with_suffix("")) + f"_{p.stem}.out", False)
        rows.append(run_one(p, args.method, args.basis))
        args.out.write_text(json.dumps(rows, indent=1) + "\n")  # after each, so a crash keeps work
        psi4.core.clean()


if __name__ == "__main__":
    main()
