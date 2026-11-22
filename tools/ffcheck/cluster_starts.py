"""Force-field minima of Li⁺(S)₄ clusters, the starts for the DFT clusters (trial T6, stage 1).

    ../oracle/.venv/bin/python cluster_starts.py PACKAGE.ucsys [...] --out DIR [--starts 10]

Each package holds one Li⁺, one PF₆⁻ (decoupled: charges and LJ ε zero, moved far away) and four
solvent molecules. Per start, the solvents are placed with their carbonyl O 0.21 nm from Li⁺ along
the directions of a randomly rotated tetrahedron, C=O pointing at Li⁺, each randomly rotated about
that axis. The cluster is minimized in vacuum (q_Li = 1, no cutoff, Reference platform). The lowest
minimum in which all four carbonyl O stay within 0.25 nm of Li⁺ is written as DIR/<package>.xyz
(Li⁺ first, then the solvents; Å), and a summary goes to stdout.

Validation only, like tools/oracle: nothing in the components imports it.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from li_binding import FAR_NM, _minimize, _package_info, build_system, write_xyz
from oracle import load_topology

TETRA = np.array([[1, 1, 1], [1, -1, -1], [-1, 1, -1], [-1, -1, 1]]) / np.sqrt(3.0)
LI_O_START_NM = 0.21
BOUND_NM = 0.25


def random_rotation(rng: np.random.Generator) -> np.ndarray:
    q = rng.normal(size=4)
    a, b, c, d = q / np.linalg.norm(q)
    return np.array([
        [a*a + b*b - c*c - d*d, 2*(b*c - a*d), 2*(b*d + a*c)],
        [2*(b*c + a*d), a*a - b*b + c*c - d*d, 2*(c*d - a*b)],
        [2*(b*d - a*c), 2*(c*d + a*b), a*a - b*b - c*c + d*d],
    ])  # fmt: skip


def align(u: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Rotation matrix that turns unit vector u into unit vector v."""
    w = np.cross(u, v)
    s, c = np.linalg.norm(w), float(u @ v)
    if s < 1e-12:
        if c > 0:
            return np.eye(3)
        p = np.cross(u, np.eye(3)[int(np.argmin(abs(u)))])  # any axis normal to u
        p /= np.linalg.norm(p)
        return 2 * np.outer(p, p) - np.eye(3)  # rotation by pi about p
    k = np.array([[0, -w[2], w[1]], [w[2], 0, -w[0]], [-w[1], w[0], 0]]) / s
    return np.eye(3) + s * k + (1 - c) * k @ k


def about(axis: np.ndarray, angle: float) -> np.ndarray:
    k = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(angle) * k + (1 - np.cos(angle)) * k @ k


def carbonyl(mt: dict) -> tuple[int, int]:
    """(carbonyl O, its C) as template indices."""
    nb: dict[int, list[int]] = {i: [] for i in range(len(mt["atoms"]))}
    for b in mt["bonds"]:
        i, j = b["atoms"]
        nb[i].append(j)
        nb[j].append(i)
    ((o, c),) = [
        (i, nb[i][0]) for i, a in enumerate(mt["atoms"]) if a["element"] == "O" and len(nb[i]) == 1
    ]
    return o, c


def run(path: Path, out: Path, n_starts: int, seed: int) -> dict:
    top = load_topology(path)
    info = _package_info(path)
    li = info["Li"][0][0]
    pf6 = info["PF6"][0]
    q, eps = top.charges_e.copy(), top.epsilon_kjmol.copy()
    q[pf6], eps[pf6] = 0.0, 0.0
    system = build_system(dataclasses.replace(top, cell_nm=None, charges_e=q, epsilon_kjmol=eps))
    molecules = []  # (global indices, carbonyl O global, its C global, name)
    for name, (idx, mt) in info.items():
        if name in ("Li", "PF6"):
            continue
        n = len(mt["atoms"])
        o, c = carbonyl(mt)
        for k in range(len(idx) // n):
            g = idx[k * n : (k + 1) * n]
            molecules.append((g, g[o], g[c], name))
    assert len(molecules) == 4, f"{path}: {len(molecules)} solvents, expected 4"
    rng = np.random.default_rng(seed)
    best = None
    tried = []
    for s in range(n_starts):
        pos = top.positions_nm.copy()
        pos[li] = 0.0
        pos[pf6] = pos[pf6] - pos[pf6].mean(axis=0) + np.array([0.0, 0.0, FAR_NM])
        dirs = TETRA @ random_rotation(rng).T
        for (g, o, c, _), d in zip(molecules, dirs, strict=True):
            r = pos[g] - pos[o]
            u = pos[o] - pos[c]
            u /= np.linalg.norm(u)
            rot = about(d, rng.uniform(0, 2 * np.pi)) @ align(u, -d)
            pos[g] = r @ rot.T + LI_O_START_NM * d
        e, p = _minimize(system, pos)
        d_o = [float(np.linalg.norm(p[o] - p[li])) for _, o, _, _ in molecules]
        ok = max(d_o) < BOUND_NM
        tried.append(
            {
                "start": s,
                "energy_kjmol": round(e, 3),
                "li_o_nm": [round(x, 4) for x in d_o],
                "four_bound": ok,
            }
        )
        if ok and (best is None or e < best[0]):
            best = (e, p, d_o)
    if best is None:
        raise SystemExit(f"{path}: no start kept all four carbonyl O bound")
    e, p, d_o = best
    order = [li] + [i for g, _, _, _ in molecules for i in g]
    els = _elements(path)
    write_xyz(
        out / f"{path.stem}.xyz",
        [els[i] for i in order],
        p[order] - p[li],
        f"Li+ {' '.join(m[3] for m in molecules)}, force-field minimum (M1, q_Li 1) of {path.name}",
    )
    return {
        "package": path.name,
        "solvents": [m[3] for m in molecules],
        "energy_kjmol": round(e, 3),
        "li_o_carbonyl_nm": [round(x, 4) for x in d_o],
        "starts": tried,
    }


def _elements(path: Path) -> list[str]:
    doc = json.loads((path / "system.json").read_text(encoding="utf-8"))
    out = []
    for comp in doc["components"]:
        mt = doc["molecule_types"][comp["molecule_type"]]
        out += [a["element"] for a in mt["atoms"]] * comp["count"]
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("packages", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--starts", type=int, default=10)
    ap.add_argument("--seed", type=int, default=20261122)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    rows = [run(p, args.out, args.starts, args.seed) for p in args.packages]
    json.dump(rows, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main()
