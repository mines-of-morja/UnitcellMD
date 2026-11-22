"""Li⁺–solvent complexes and Li⁺(S)ₙ clusters at DFT (trial T6, stage 1).

Runs inside the Psi4 image (tools/qm/Dockerfile):

    docker run --rm -u "$(id -u):$(id -g)" -e HOME=/tmp -e USER=psi4 -v "$PWD:/work" -w /work \
        ucmd-psi4:1.9.1 python cluster_dft.py START.xyz [...] --functional wb97x-d --out r.json

Each START.xyz holds Li⁺ as the first atom and one or more solvent molecules. The molecules are
found by covalent connectivity. Per file:
- the complex (charge +1) is optimized at FUNCTIONAL/def2-SVP;
- each solvent is optimized alone at def2-SVP, starting from its geometry in the complex;
- energies at FUNCTIONAL/def2-TZVPD on those geometries:
  - E_bind = E(complex) − Σ E(solvent, own minimum) − E(Li⁺);
  - E_int_CP = E(complex) − Σ over fragments of E(fragment in the full complex basis, at the
    complex geometry), Boys–Bernardi;
  - E_bind_CP = E_bind + Σ over fragments of [E(fragment, own basis) − E(fragment, complex
    basis)], both at the complex geometry.
- Li–O distances to every carbonyl O (O with one bonded neighbour) and the solvent formulas.

Validation only, like tools/oracle: nothing in the components imports it. Energies in kJ/mol
(spec units) and kcal/mol, converted from hartree with CODATA 2018.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from collections import Counter
from pathlib import Path

import psi4

# CODATA 2018 (spec/units.md): hartree energy 4.3597447222071e-18 J, N_A 6.02214076e23 /mol
KJMOL_PER_HARTREE = 4.3597447222071e-18 * 6.02214076e23 / 1e3
KCAL_IN_KJ = 4.184  # thermochemical calorie (exact)
# covalent radii, Å (Cordero et al., Dalton Trans. 2008, 2832), for connectivity only
R_COV = {"H": 0.31, "C": 0.76, "O": 0.66, "F": 0.57, "P": 1.07, "Li": 1.28}
NAMES = {"C3H4O3": "EC", "C4H8O3": "EMC", "C4H6O3": "PC", "C3H6O3": "DMC"}
OPT_BASIS, SP_BASIS = "def2-svp", "def2-tzvpd"

Atom = tuple[str, float, float, float]


def read_xyz(path: Path) -> list[Atom]:
    lines = path.read_text(encoding="utf-8").splitlines()
    n = int(lines[0])
    rows = map(str.split, lines[2 : 2 + n])
    return [(r[0].capitalize(), float(r[1]), float(r[2]), float(r[3])) for r in rows]


def dist(a: Atom, b: Atom) -> float:
    return math.dist(a[1:], b[1:])


def fragments(atoms: list[Atom]) -> list[list[int]]:
    """Molecules among atoms[1:] (atom 0 is Li⁺) by covalent connectivity (1.2 × radii)."""
    rest = list(range(1, len(atoms)))
    seen: set[int] = set()
    out = []
    for i in rest:
        if i in seen:
            continue
        stack, frag = [i], []
        seen.add(i)
        while stack:
            k = stack.pop()
            frag.append(k)
            for j in rest:
                if j not in seen:
                    cut = 1.2 * (R_COV[atoms[k][0]] + R_COV[atoms[j][0]])
                    if dist(atoms[k], atoms[j]) < cut:
                        seen.add(j)
                        stack.append(j)
        out.append(sorted(frag))
    return out


def formula(atoms: list[Atom], idx: list[int]) -> str:
    c = Counter(atoms[i][0] for i in idx)
    return "".join(f"{el}{c[el]}" for el in ("C", "H", "O", "F", "P") if c[el])


def carbonyl_o(atoms: list[Atom], idx: list[int]) -> list[int]:
    out = []
    for i in idx:
        if atoms[i][0] == "O":
            nb = [
                j
                for j in idx
                if j != i and dist(atoms[i], atoms[j]) < 1.2 * (0.66 + R_COV[atoms[j][0]])
            ]
            if len(nb) == 1:
                out.append(i)
    return out


def mol(atoms: list[Atom], charge: int, ghost: set[int] = frozenset()) -> psi4.core.Molecule:
    body = "\n".join(
        f"{'Gh(' + el + ')' if i in ghost else el} {x:.8f} {y:.8f} {z:.8f}"
        for i, (el, x, y, z) in enumerate(atoms)
    )
    return psi4.geometry(f"{charge} 1\n{body}\nunits angstrom\nno_reorient\nno_com\nsymmetry c1\n")


def geometry(m: psi4.core.Molecule) -> list[Atom]:
    rows = [r.split() for r in m.save_string_xyz().splitlines()[1:]]
    return [(r[0].capitalize(), float(r[1]), float(r[2]), float(r[3])) for r in rows]


def energy(f: str, atoms: list[Atom], charge: int, ghost: set[int] = frozenset()) -> float:
    psi4.set_options({"basis": SP_BASIS})
    return float(psi4.energy(f, molecule=mol(atoms, charge, ghost)))


def optimize(f: str, atoms: list[Atom], charge: int) -> list[Atom]:
    psi4.set_options({"basis": OPT_BASIS, "geom_maxiter": 300})
    m = mol(atoms, charge)
    psi4.optimize(f, molecule=m)
    return geometry(m)


def run_one(path: Path, f: str) -> dict:
    t0 = time.time()
    start = read_xyz(path)
    if start[0][0] != "Li":
        raise ValueError(f"{path}: the first atom must be Li")
    cplx = optimize(f, start, +1)
    frags = fragments(cplx)
    names = [NAMES.get(formula(cplx, fr), formula(cplx, fr)) for fr in frags]
    e_c = energy(f, cplx, +1)
    e_li = energy(f, [cplx[0]], +1)
    pieces = [([0], +1)] + [(fr, 0) for fr in frags]
    e_bind_h = e_c - e_li
    bsse_h = 0.0
    e_int_h = e_c
    solvents = []
    for (idx, q), name in zip(pieces, ["Li", *names], strict=True):
        own = energy(f, [cplx[i] for i in idx], q)
        full = energy(f, cplx, q, ghost=set(range(len(cplx))) - set(idx))
        bsse_h += own - full
        e_int_h -= full
        if name != "Li":
            alone = optimize(f, [cplx[i] for i in idx], 0)
            e_alone = energy(f, alone, 0)
            e_bind_h -= e_alone
            solvents.append({"name": name, "e_alone_hartree": e_alone, "e_at_complex_hartree": own,
                             "xyz_alone": alone})  # fmt: skip
    d = [
        {"solvent": n, "li_o_angstrom": round(dist(cplx[0], cplx[o]), 4)}
        for fr, n in zip(frags, names, strict=True)
        for o in carbonyl_o(cplx, fr)
    ]
    k = KJMOL_PER_HARTREE
    return {
        "start": path.name,
        "functional": f,
        "opt_basis": OPT_BASIS,
        "sp_basis": SP_BASIS,
        "solvents": names,
        "e_complex_hartree": e_c,
        "e_li_hartree": e_li,
        "e_bind_kjmol": round(e_bind_h * k, 3),
        "e_bind_kcalmol": round(e_bind_h * k / KCAL_IN_KJ, 3),
        "e_bind_cp_kcalmol": round((e_bind_h + bsse_h) * k / KCAL_IN_KJ, 3),
        "e_int_cp_at_complex_kcalmol": round(e_int_h * k / KCAL_IN_KJ, 3),
        "li_o_carbonyl": d,
        "solvent_alone": solvents,
        "complex_xyz": cplx,
        "wall_s": round(time.time() - t0, 1),
        "psi4": psi4.__version__,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("starts", nargs="+", type=Path)
    ap.add_argument("--functional", required=True)
    ap.add_argument("--threads", type=int, default=16)
    ap.add_argument("--memory", default="20 GB")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    psi4.set_num_threads(args.threads)
    psi4.set_memory(args.memory)
    psi4.set_options({"scf_type": "df", "dft_radial_points": 99, "dft_spherical_points": 590})
    rows = json.loads(args.out.read_text()) if args.out.exists() else []
    done = {(r["start"], r["functional"]) for r in rows}
    for p in args.starts:
        if (p.name, args.functional) in done:
            continue
        psi4.core.set_output_file(str(args.out.with_suffix("")) + f"_{p.stem}.out", False)
        rows.append(run_one(p, args.functional))
        args.out.write_text(json.dumps(rows, indent=1) + "\n")  # after each, so a crash keeps work
        psi4.core.clean()


if __name__ == "__main__":
    main()
