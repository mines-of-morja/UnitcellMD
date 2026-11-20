"""Gas-phase Li⁺–solvent binding energies of a force field (layer-0 test, forcefield-strategy.md).

    ../oracle/.venv/bin/python li_binding.py PACKAGE.ucsys [PACKAGE.ucsys ...] [--q-li 1.0 0.75]

Each package holds one Li⁺, one PF₆⁻ (only for neutrality; it is decoupled: charges and LJ ε set
to zero) and one solvent molecule. For every package and Li charge:
- the solvent alone is minimized (Li⁺ decoupled as well);
- the complex is minimized from starts near every oxygen (0.2 nm out along the bond direction,
  and between the two ether oxygens);
- E_bind = E(complex) − E(solvent), both flexible, no cutoff, Reference platform.
The lowest minimum overall and the lowest with Li⁺ nearest to the carbonyl O are reported, with
the Li–O distance. Reference values (QM) are compared in the README, not here.

Validation only, like tools/oracle: nothing in the components imports it.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import math
import sys
from pathlib import Path

import numpy as np
import openmm as mm
from openmm import unit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "oracle"))
from oracle import Topology, load_topology, molecular_system

# CODATA 2018 (spec/units.md §2): e²N_A/(4πε₀) in kJ mol⁻¹ nm e⁻²
_E_C = 1.602176634e-19
_N_A = 6.02214076e23
_EPS0 = 8.8541878128e-12
COULOMB_KJMOL_NM = _E_C**2 * _N_A / (4 * math.pi * _EPS0) / 1e3 * 1e9
KCAL_IN_KJ = 4.184  # thermochemical calorie (exact)

FAR_NM = 100.0
TOLERANCE = 1e-6  # kJ/mol/nm, minimizer force tolerance


@dataclasses.dataclass
class Result:
    energy_kjmol: float
    distance_nm: float  # Li to the nearest solvent atom
    nearest: int  # index of that atom
    positions_nm: np.ndarray


def build_system(top: Topology) -> mm.System:
    return molecular_system(dataclasses.replace(top, cell_nm=None))


def total_energy(system: mm.System, pos: np.ndarray) -> float:
    ctx = mm.Context(system, mm.VerletIntegrator(0.001), mm.Platform.getPlatformByName("Reference"))
    ctx.setPositions(pos)
    return ctx.getState(getEnergy=True).getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)


def _minimize(system: mm.System, pos: np.ndarray) -> tuple[float, np.ndarray]:
    ctx = mm.Context(system, mm.VerletIntegrator(0.001), mm.Platform.getPlatformByName("Reference"))
    ctx.setPositions(pos)
    mm.LocalEnergyMinimizer.minimize(ctx, TOLERANCE, 0)
    st = ctx.getState(getEnergy=True, getPositions=True)
    return (
        st.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole),
        np.array(st.getPositions(asNumpy=True).value_in_unit(unit.nanometer)),
    )


def binding_energy(
    top: Topology,
    *,
    li: int,
    solvent: list[int],
    starts_nm: list[np.ndarray],
    decouple: list[int] = (),
    q_li: float | None = None,
) -> Result:
    """Lowest E(complex) − E(solvent) over the given Li start positions (kJ/mol)."""
    q = top.charges_e.copy()
    eps = top.epsilon_kjmol.copy()
    for i in decouple:
        q[i] = 0.0
        eps[i] = 0.0
    if q_li is not None:
        q[li] = q_li
    t = dataclasses.replace(top, cell_nm=None, charges_e=q, epsilon_kjmol=eps)
    system = build_system(t)
    centre = top.positions_nm[solvent].mean(axis=0)
    base = top.positions_nm - centre
    for i in decouple:  # out of the way; it interacts with nothing
        base[i] = base[i] + np.array([0.0, 0.0, -FAR_NM])
    # The solvent alone: Li decoupled as well (charge and ε zero), so nothing can pull on it.
    q_alone = q.copy()
    eps_alone = eps.copy()
    q_alone[li] = 0.0
    eps_alone[li] = 0.0
    system_alone = build_system(dataclasses.replace(t, charges_e=q_alone, epsilon_kjmol=eps_alone))
    alone = base.copy()
    alone[li] = np.array([FAR_NM, 0.0, 0.0])
    e_alone, _ = _minimize(system_alone, alone)
    best: Result | None = None
    for s in starts_nm:
        pos = base.copy()
        pos[li] = np.asarray(s) - centre
        e, p = _minimize(system, pos)
        d = np.linalg.norm(p[solvent] - p[li], axis=1)
        r = Result(e - e_alone, float(d.min()), solvent[int(d.argmin())], p)
        if best is None or r.energy_kjmol < best.energy_kjmol:
            best = r
    assert best is not None
    return best


def _package_info(path: Path) -> dict:
    doc = json.loads((path / "system.json").read_text(encoding="utf-8"))
    out, offset = {}, 0
    for comp in doc["components"]:
        mt = doc["molecule_types"][comp["molecule_type"]]
        n = len(mt["atoms"]) * comp["count"]
        out[comp["molecule_type"]] = (list(range(offset, offset + n)), mt)
        offset += n
    return out


def _starts(top: Topology, solvent: list[int], mt: dict) -> tuple[list[np.ndarray], set[int]]:
    """Starts 0.2 nm out from every O along its bond(s), and between ether O pairs."""
    pos = top.positions_nm
    o = solvent[0]
    neighbours: dict[int, list[int]] = {i: [] for i in range(len(mt["atoms"]))}
    for b in mt["bonds"]:
        i, j = b["atoms"]
        neighbours[i].append(j)
        neighbours[j].append(i)
    oxygens = [i for i, a in enumerate(mt["atoms"]) if a["element"] == "O"]
    carbonyl = {o + i for i in oxygens if len(neighbours[i]) == 1}
    starts = []
    for i in oxygens:
        out = np.zeros(3)
        for j in neighbours[i]:
            v = pos[o + i] - pos[o + j]
            out += v / np.linalg.norm(v)
        out /= np.linalg.norm(out)
        starts.append(pos[o + i] + 0.2 * out)
    ether = [i for i in oxygens if len(neighbours[i]) == 2]
    for a in range(len(ether)):
        for b in range(a + 1, len(ether)):
            mid = 0.5 * (pos[o + ether[a]] + pos[o + ether[b]])
            c = pos[solvent].mean(axis=0)
            v = mid - c
            starts.append(mid + 0.2 * v / np.linalg.norm(v))
    return starts, carbonyl


def run(path: Path, q_values: list[float]) -> list[dict]:
    top = load_topology(path)
    info = _package_info(path)
    li = info["Li"][0][0]
    pf6 = info["PF6"][0]
    ((name, (solvent, mt)),) = [(k, v) for k, v in info.items() if k not in ("Li", "PF6")]
    starts, carbonyl = _starts(top, solvent, mt)
    rows = []
    for q in q_values:
        best = None
        best_carbonyl = None
        for s in starts:
            r = binding_energy(top, li=li, solvent=solvent, starts_nm=[s], decouple=pf6, q_li=q)
            if best is None or r.energy_kjmol < best.energy_kjmol:
                best = r
            if r.nearest in carbonyl and (
                best_carbonyl is None or r.energy_kjmol < best_carbonyl.energy_kjmol
            ):
                best_carbonyl = r
        assert best is not None
        row = {
            "package": str(path),
            "solvent": name,
            "q_li_e": q,
            "e_bind_kjmol": round(best.energy_kjmol, 3),
            "e_bind_kcalmol": round(best.energy_kjmol / KCAL_IN_KJ, 3),
            "li_o_nm": round(best.distance_nm, 4),
            "nearest_is_carbonyl_o": best.nearest in carbonyl,
            "solvent_charges_e": [a["charge_e"] for a in mt["atoms"]],
        }
        if best_carbonyl is not None:
            row["e_bind_carbonyl_kjmol"] = round(best_carbonyl.energy_kjmol, 3)
            row["e_bind_carbonyl_kcalmol"] = round(best_carbonyl.energy_kjmol / KCAL_IN_KJ, 3)
            row["li_o_carbonyl_nm"] = round(best_carbonyl.distance_nm, 4)
        rows.append(row)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("packages", nargs="+", type=Path)
    ap.add_argument("--q-li", type=float, nargs="+", default=[1.0, 0.75])
    args = ap.parse_args()
    out = [row for p in args.packages for row in run(p, args.q_li)]
    json.dump(out, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main()
