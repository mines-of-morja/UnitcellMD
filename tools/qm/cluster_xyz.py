"""Geometries of cluster_dft.py as extended XYZ, to look at them (no Psi4 needed, stdlib only).

    python3 tools/qm/cluster_xyz.py RESULT.json OUT_DIR

For every start file in RESULT.json, written by `cluster_dft.py`:

- OUT_DIR/<start>.final.xyz: the optimized complex, as in the JSON;
- OUT_DIR/<start>.path.xyz: every geometry the optimizer proposed, from the Psi4 output next to
  RESULT.json (`<result>_<start>.out`), then the optimized complex (the start is not included).

Both hold Å, with the solvent of each atom as the column `molecule` (0 = Li⁺) and the step in the
comment line. **Coordinates only:** no energy is read or written, so a blinded energy stays
blinded. A missing .out file, or one whose atoms differ from the JSON, is an error.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

Atom = tuple[str, float, float, float]
NEXT = "Next Geometry in Ang"
ROW = re.compile(r"^\s*([A-Z][a-z]?)((?:\s+-?\d+\.\d+){3})\s*$")
COVALENT = {"H": 0.31, "C": 0.76, "O": 0.66}  # Å; bonds below 1.25 × the sum of radii


def path_frames(text: str, elements: list[str]) -> list[list[Atom]]:
    """The optimizer's geometries of the complex: blocks with the complex's atom count."""
    frames = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip() != NEXT:
            continue
        atoms: list[Atom] = []
        for row in lines[i + 1 :]:
            m = ROW.match(row)
            if m:
                atoms.append((m[1], *map(float, m[2].split())))
            elif atoms and row.strip() and "Fragment" not in row:
                break  # the block ended
            elif atoms and not row.strip() and len(atoms) >= len(elements):
                break
        if len(atoms) == len(elements):
            if [a[0] for a in atoms] != elements:
                raise ValueError("the .out file has the same atom count but other elements")
            frames.append(atoms)
    return frames


def molecules(atoms: list[Atom]) -> list[int]:
    """Molecule index per atom; Li is 0, each solvent 1, 2, … in order of its first atom."""
    n = len(atoms)
    owner = [-1] * n
    owner[0] = 0
    current = 0
    for s in range(1, n):
        if owner[s] >= 0:
            continue
        current += 1
        owner[s] = current
        stack = [s]
        while stack:
            i = stack.pop()
            for j in range(1, n):
                if owner[j] < 0 and math.dist(atoms[i][1:], atoms[j][1:]) < 1.25 * (
                    COVALENT[atoms[i][0]] + COVALENT[atoms[j][0]]
                ):
                    owner[j] = current
                    stack.append(j)
    return owner


def frame(atoms: list[Atom], mol: list[int], comment: str) -> str:
    head = f"Properties=species:S:1:pos:R:3:molecule:I:1 {comment}"
    rows = [f"{e} {x:.6f} {y:.6f} {z:.6f} {m}" for (e, x, y, z), m in zip(atoms, mol, strict=True)]
    return "\n".join([str(len(atoms)), head, *rows]) + "\n"


def export(result: Path, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for row in json.loads(result.read_text(encoding="utf-8")):
        name = Path(row["start"]).stem
        cplx: list[Atom] = [(a[0], *map(float, a[1:])) for a in row["complex_xyz"]]
        elements = [a[0] for a in cplx]
        mol = molecules(cplx)
        if max(mol) != len(row["solvents"]):
            raise ValueError(f"{name}: {max(mol)} molecules found, {len(row['solvents'])} expected")
        final = out_dir / f"{name}.final.xyz"
        final.write_text(frame(cplx, mol, f'step=final name="{name}"'), encoding="utf-8")
        log = result.with_name(f"{result.stem}_{name}.out")
        frames = path_frames(log.read_text(encoding="utf-8", errors="replace"), elements)
        path = out_dir / f"{name}.path.xyz"
        path.write_text(
            "".join(frame(f, mol, f'step={i} name="{name}"') for i, f in enumerate(frames, 1))
            + frame(cplx, mol, f'step=final name="{name}"'),
            encoding="utf-8",
        )
        print(f"{name}: {len(frames)} optimizer steps + final")
        written += [final, path]
    return written


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("result", type=Path)
    ap.add_argument("out_dir", type=Path)
    a = ap.parse_args()
    export(a.result, a.out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
