"""OpenMM oracle: reference energies and forces for UnitcellMD system packages.

Validation only; never a runtime dependency (PLAN.md §2.1). Converts a spec 0.1 system package (0.1.2 with pair overrides)
into an OpenMM System and evaluates it with the double-precision Reference platform.

- Version 0 (`load_package`, `lj_system`) covers Phase 0 and E1: Lennard-Jones with the cutoff
  modes of the engine's LJ provider.
- Version 1 (`load_topology`, `molecular_system`, `energy_terms`) covers molecular packages:
  every bonded form of the spec, exclusions and 1-4 pairs by shortest bond path, both
  combination rules, and Coulomb without cutoff or with PME. Energies come per term, in the
  same split that OpenMM's own GROMACS reader produces, for term-by-term comparisons
  (PLAN.md E2.1, E2.2, B1 gate).

Units are the same as the spec's (nm, kJ/mol, amu), so no conversion happens here.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import openmm as mm
from openmm import unit

CutoffMode = Literal["truncate", "potential-shift"]


@dataclass(frozen=True)
class Package:
    """The parts of a system package the oracle needs, expanded to per-atom arrays."""

    name: str
    positions_nm: np.ndarray  # (N, 3)
    cell_nm: np.ndarray | None  # (3, 3) rows = a, b, c
    masses_amu: np.ndarray
    charges_e: np.ndarray
    sigma_nm: np.ndarray
    epsilon_kjmol: np.ndarray
    combination_rule: str
    pairs: PairTable | None = None  # only when the package has pair overrides (spec 0.1.2)

    @property
    def n_atoms(self) -> int:
        return len(self.masses_amu)


@dataclass(frozen=True)
class PairTable:
    """LJ parameters per type pair, for packages with `pair_overrides` (spec 0.1.2, §5.2).

    `sigma_nm[a, b]` and `epsilon_kjmol[a, b]` are the override where one is given, else the
    combination rule; `type_index[i]` is atom i's row.
    """

    type_index: np.ndarray  # (N,) int
    sigma_nm: np.ndarray  # (T, T), symmetric
    epsilon_kjmol: np.ndarray  # (T, T), symmetric


def combine(rule: str, s1: float, e1: float, s2: float, e2: float) -> tuple[float, float]:
    """σ_ij, ε_ij from the combination rule (spec §5.2)."""
    sigma = math.sqrt(s1 * s2) if rule == "geometric" else 0.5 * (s1 + s2)
    return sigma, math.sqrt(e1 * e2)


def pair_table(ff: dict, atom_types: list[str]) -> PairTable | None:
    """The type-pair table of a force-field block, or None without overrides."""
    overrides = ff.get("pair_overrides", [])
    if not overrides:
        return None
    names = sorted(ff["atom_types"])
    row = {t: k for k, t in enumerate(names)}
    lj = [ff["atom_types"][t] for t in names]
    n = len(names)
    sigma, epsilon = np.zeros((n, n)), np.zeros((n, n))
    for a in range(n):
        for b in range(n):
            sigma[a, b], epsilon[a, b] = combine(
                ff["combination_rule"],
                lj[a]["sigma_nm"], lj[a]["epsilon_kjmol"], lj[b]["sigma_nm"], lj[b]["epsilon_kjmol"],
            )
    for o in overrides:
        a, b = (row[t] for t in o["types"])
        sigma[a, b] = sigma[b, a] = o["sigma_nm"]
        epsilon[a, b] = epsilon[b, a] = o["epsilon_kjmol"]
    return PairTable(np.array([row[t] for t in atom_types]), sigma, epsilon)


def _lj_nonbonded(rule: str, sigma, epsilon, pairs: PairTable | None, shift: bool) -> mm.CustomNonbondedForce:
    """The LJ CustomNonbondedForce: per-particle mixing, or per-type tables with overrides."""
    tail = " - 4*eps*((sig/rc)^12-(sig/rc)^6)" if shift else ""
    if pairs is None:
        mix = (
            "sig=sqrt(sig1*sig2); eps=sqrt(eps1*eps2)"
            if rule == "geometric"
            else "sig=0.5*(sig1+sig2); eps=sqrt(eps1*eps2)"
        )
        force = mm.CustomNonbondedForce(f"4*eps*((sig/r)^12-(sig/r)^6){tail}; {mix}")
        force.addPerParticleParameter("sig")
        force.addPerParticleParameter("eps")
        for s, e in zip(sigma, epsilon, strict=True):
            force.addParticle([float(s), float(e)])
        return force
    n = len(pairs.sigma_nm)
    force = mm.CustomNonbondedForce(
        f"4*eps*((sig/r)^12-(sig/r)^6){tail}; sig=sigt(t1, t2); eps=epst(t1, t2)"
    )
    # Discrete2DFunction values run with the first index fastest; the tables are symmetric.
    force.addTabulatedFunction("sigt", mm.Discrete2DFunction(n, n, pairs.sigma_nm.T.ravel().tolist()))
    force.addTabulatedFunction("epst", mm.Discrete2DFunction(n, n, pairs.epsilon_kjmol.T.ravel().tolist()))
    force.addPerParticleParameter("t")
    for t in pairs.type_index:
        force.addParticle([float(t)])
    return force


def load_package(path: Path | str) -> Package:
    """Read a parameterized package without bonds (enough for LJ / point-charge references)."""
    path = Path(path)
    doc = json.loads((path / "system.json").read_text(encoding="utf-8"))
    if doc.get("spec_version", "").split(".")[:2] != ["0", "1"]:
        raise ValueError(f"oracle v0 reads spec 0.1 packages, got {doc.get('spec_version')}")
    ff = doc.get("forcefield")
    if ff is None:
        raise ValueError("the oracle needs a parameterized package")
    masses, charges, sigma, epsilon, types = [], [], [], [], []
    for component in doc["components"]:
        mtype = doc["molecule_types"][component["molecule_type"]]
        if mtype["bonds"]:
            raise NotImplementedError("bonded systems arrive in E2")
        for _ in range(component["count"]):
            for atom in mtype["atoms"]:
                lj = ff["atom_types"][atom["type"]]
                types.append(atom["type"])
                masses.append(atom["mass_amu"])
                charges.append(atom["charge_e"])
                sigma.append(lj["sigma_nm"])
                epsilon.append(lj["epsilon_kjmol"])
    cell = None if doc["cell_nm"] is None else np.array(doc["cell_nm"], dtype=float)
    return Package(
        doc["name"],
        np.load(path / "positions.npy"),
        cell,
        np.array(masses),
        np.array(charges),
        np.array(sigma),
        np.array(epsilon),
        ff["combination_rule"],
        pair_table(ff, types),
    )


def lj_system(pkg: Package, cutoff_nm: float, mode: CutoffMode) -> mm.System:
    """OpenMM System with Lennard-Jones only, via CustomNonbondedForce (exact mixing rule and mode)."""
    if np.any(pkg.charges_e != 0):
        raise NotImplementedError("charged periodic systems need PME (E2)")
    system = mm.System()
    for mass in pkg.masses_amu:
        system.addParticle(float(mass))
    force = _lj_nonbonded(
        pkg.combination_rule, pkg.sigma_nm, pkg.epsilon_kjmol, pkg.pairs, mode == "potential-shift"
    )
    force.addGlobalParameter("rc", cutoff_nm)
    force.setCutoffDistance(cutoff_nm)
    if pkg.cell_nm is None:
        force.setNonbondedMethod(mm.CustomNonbondedForce.CutoffNonPeriodic)
    else:
        force.setNonbondedMethod(mm.CustomNonbondedForce.CutoffPeriodic)
        system.setDefaultPeriodicBoxVectors(*(mm.Vec3(*row) for row in pkg.cell_nm))
    force.setUseLongRangeCorrection(False)
    system.addForce(force)
    return system


def evaluate(system: mm.System, positions_nm: np.ndarray, cell_nm: np.ndarray | None = None) -> tuple[float, np.ndarray]:
    """Potential energy (kJ/mol) and forces (kJ mol-1 nm-1) on the Reference platform."""
    context = mm.Context(system, mm.VerletIntegrator(0.001), mm.Platform.getPlatformByName("Reference"))
    if cell_nm is not None:
        context.setPeriodicBoxVectors(*(mm.Vec3(*row) for row in cell_nm))
    context.setPositions(positions_nm)
    state = context.getState(getEnergy=True, getForces=True)
    energy = state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)
    forces = state.getForces(asNumpy=True).value_in_unit(unit.kilojoule_per_mole / unit.nanometer)
    return float(energy), np.asarray(forces)


def virial_trace_fd(system: mm.System, pkg: Package, strain: float = 1e-6) -> float:
    """tr W = -dE/d(eps) under isotropic strain r -> (1+eps) r, h -> (1+eps) h (units.md §4)."""
    energies = []
    for sign in (+1, -1):
        scale = 1.0 + sign * strain
        cell = None if pkg.cell_nm is None else pkg.cell_nm * scale
        energies.append(evaluate(system, pkg.positions_nm * scale, cell)[0])
    return -(energies[0] - energies[1]) / (2 * strain)


def lj_dispersion_correction(pkg: Package, cutoff_nm: float) -> float:
    """Analytic long-range LJ energy beyond rc for a single atom type (kJ/mol)."""
    if len(set(zip(pkg.sigma_nm, pkg.epsilon_kjmol, strict=True))) != 1 or pkg.cell_nm is None:
        raise NotImplementedError("single atom type in a periodic box only")
    sigma, epsilon = pkg.sigma_nm[0], pkg.epsilon_kjmol[0]
    volume = abs(float(np.linalg.det(pkg.cell_nm)))
    x = sigma / cutoff_nm
    n = pkg.n_atoms
    return 8.0 / 3.0 * math.pi * n * n / volume * epsilon * sigma**3 * (x**9 / 3.0 - x**3)


def lj_dispersion_correction_types(pkg: Package, cutoff_nm: float) -> float:
    """Analytic long-range LJ energy beyond rc, summed over type pairs (kJ/mol).

    E = (8π/3V) Σ_a Σ_b N_a N_b ε_ab σ_ab³ [(σ_ab/rc)⁹/3 − (σ_ab/rc)³], with the pair overrides
    (spec 0.1.2) where the package has them. One type gives `lj_dispersion_correction`.
    """
    if pkg.cell_nm is None:
        raise NotImplementedError("periodic box only")
    keys = list(zip(pkg.sigma_nm, pkg.epsilon_kjmol, strict=True))
    if pkg.pairs is None:
        index = {k: n for n, k in enumerate(dict.fromkeys(keys))}
        types = np.array([index[k] for k in keys])
        per_type = list(index)
        sig = np.array([[combine(pkg.combination_rule, a[0], a[1], b[0], b[1])[0] for b in per_type] for a in per_type])
        eps = np.array([[combine(pkg.combination_rule, a[0], a[1], b[0], b[1])[1] for b in per_type] for a in per_type])
    else:
        types, sig, eps = pkg.pairs.type_index, pkg.pairs.sigma_nm, pkg.pairs.epsilon_kjmol
    counts = np.bincount(types, minlength=len(sig)).astype(float)
    volume = abs(float(np.linalg.det(pkg.cell_nm)))
    x = sig / cutoff_nm
    per_pair = eps * sig**3 * (x**9 / 3.0 - x**3)
    return 8.0 / 3.0 * math.pi / volume * float(counts @ per_pair @ counts)


# ---------------------------------------------------------------------------------------------
# Version 1: molecular packages

TERMS = {1: "bond", 2: "angle", 3: "dihedral", 4: "improper", 5: "coulomb", 6: "lj", 7: "lj14"}
"""Force groups. `coulomb` includes the scaled 1-4 Coulomb pairs; `lj14` holds the 1-4 LJ pairs."""


@dataclass(frozen=True)
class Topology:
    """A spec v0.1 package expanded to global atom indices."""

    name: str
    positions_nm: np.ndarray
    cell_nm: np.ndarray | None
    masses_amu: np.ndarray
    charges_e: np.ndarray
    sigma_nm: np.ndarray
    epsilon_kjmol: np.ndarray
    combination_rule: str
    scale_14_lj: float
    scale_14_coulomb: float
    bonds: list[tuple[int, int, float, float]]
    angles: list[tuple[int, int, int, float, float]]
    periodic: list[tuple[int, int, int, int, int, float, float]]
    rb: list[tuple[int, int, int, int, tuple[float, ...]]]
    improper_periodic: list[tuple[int, int, int, int, int, float, float]]
    improper_harmonic: list[tuple[int, int, int, int, float, float]]
    excluded: list[tuple[int, int]]
    pairs14: list[tuple[int, int]]
    constraints: list[tuple[int, int, float]]
    pairs: PairTable | None = None  # only with pair overrides (spec 0.1.2)

    @property
    def n_atoms(self) -> int:
        return len(self.masses_amu)


def _graph_distances(n: int, bonds: list[list[int]], limit: int = 3) -> dict[tuple[int, int], int]:
    """Shortest bond-path distance ≤ limit for every connected pair (i < j) of one molecule."""
    neighbours: list[list[int]] = [[] for _ in range(n)]
    for i, j in bonds:
        neighbours[i].append(j)
        neighbours[j].append(i)
    out: dict[tuple[int, int], int] = {}
    for start in range(n):
        depth = {start: 0}
        frontier = [start]
        for d in range(1, limit + 1):
            nxt = []
            for a in frontier:
                for b in neighbours[a]:
                    if b not in depth:
                        depth[b] = d
                        nxt.append(b)
            frontier = nxt
        for b, d in depth.items():
            if b > start:
                out[(start, b)] = d
    return out


def load_topology(path: Path | str) -> Topology:
    """Read a parameterized spec v0.1 package with all its bonded terms."""
    path = Path(path)
    doc = json.loads((path / "system.json").read_text(encoding="utf-8"))
    if doc.get("spec_version", "").split(".")[:2] != ["0", "1"]:
        raise ValueError(f"the oracle reads spec 0.1 packages, got {doc.get('spec_version')}")
    ff = doc.get("forcefield")
    if ff is None:
        raise ValueError("the oracle needs a parameterized package")
    masses, charges, sigma, epsilon, types = [], [], [], [], []
    bonds, angles, periodic, rb, imp_p, imp_h, excluded, pairs14, constraints = ([] for _ in range(9))
    offset = 0
    for component in doc["components"]:
        mtype = doc["molecule_types"][component["molecule_type"]]
        n = len(mtype["atoms"])
        distances = _graph_distances(n, [b["atoms"] for b in mtype["bonds"]])
        for _ in range(component["count"]):
            for atom in mtype["atoms"]:
                lj = ff["atom_types"][atom["type"]]
                types.append(atom["type"])
                masses.append(atom["mass_amu"])
                charges.append(atom["charge_e"])
                sigma.append(lj["sigma_nm"])
                epsilon.append(lj["epsilon_kjmol"])
            o = offset
            for b in mtype["bonds"]:
                if b["form"] != "harmonic":
                    raise ValueError(f"bond form {b['form']}")
                i, j = b["atoms"]
                bonds.append((o + i, o + j, b["params"]["r0_nm"], b["params"]["k_kjmol_nm2"]))
            for a in mtype.get("angles", []):
                i, j, k = a["atoms"]
                p = a["params"]
                angles.append((o + i, o + j, o + k, math.radians(p["theta0_deg"]), p["k_kjmol_rad2"]))
            for d in mtype.get("dihedrals", []):
                i, j, k, m = (o + x for x in d["atoms"])
                p = d["params"]
                if d["form"] == "periodic":
                    periodic.append((i, j, k, m, int(p["n"]), math.radians(p["phi0_deg"]), p["k_kjmol"]))
                elif d["form"] == "ryckaert-bellemans":
                    rb.append((i, j, k, m, tuple(p[f"c{c}_kjmol"] for c in range(6))))
                elif d["form"] == "opls-fourier":
                    # ½[V1(1+cos φ) + V2(1−cos 2φ) + V3(1+cos 3φ) + V4(1−cos 4φ)] as periodic terms
                    for nn, key, phase in ((1, "v1_kjmol", 0.0), (2, "v2_kjmol", math.pi),
                                           (3, "v3_kjmol", 0.0), (4, "v4_kjmol", math.pi)):
                        periodic.append((i, j, k, m, nn, phase, 0.5 * p[key]))
                else:
                    raise ValueError(f"dihedral form {d['form']}")
            for d in mtype.get("impropers", []):
                i, j, k, m = (o + x for x in d["atoms"])
                p = d["params"]
                if d["form"] == "periodic":
                    imp_p.append((i, j, k, m, int(p["n"]), math.radians(p["phi0_deg"]), p["k_kjmol"]))
                elif d["form"] == "harmonic":
                    imp_h.append((i, j, k, m, math.radians(p["xi0_deg"]), p["k_kjmol_rad2"]))
                else:
                    raise ValueError(f"improper form {d['form']}")
            for (i, j), dist in distances.items():
                (excluded if dist <= 2 else pairs14).append((o + i, o + j))
            for c in mtype.get("constraints", []):
                i, j = c["atoms"]
                constraints.append((o + i, o + j, c["length_nm"]))
            offset += n
    cell = None if doc["cell_nm"] is None else np.array(doc["cell_nm"], dtype=float)
    return Topology(
        doc["name"], np.load(path / "positions.npy"), cell, np.array(masses), np.array(charges),
        np.array(sigma), np.array(epsilon), ff["combination_rule"], float(ff["scale_14_lj"]),
        float(ff["scale_14_coulomb"]), bonds, angles, periodic, rb, imp_p, imp_h, excluded,
        pairs14, constraints, pair_table(ff, types),
    )


def _mix(top: Topology, i: int, j: int) -> tuple[float, float]:
    """σ_ij, ε_ij of atoms i and j: the pair override if there is one, else the rule."""
    if top.pairs is not None:
        a, b = top.pairs.type_index[i], top.pairs.type_index[j]
        return float(top.pairs.sigma_nm[a, b]), float(top.pairs.epsilon_kjmol[a, b])
    return combine(
        top.combination_rule, top.sigma_nm[i], top.epsilon_kjmol[i], top.sigma_nm[j], top.epsilon_kjmol[j]
    )


def molecular_system(
    top: Topology,
    *,
    cutoff_nm: float | None = None,
    lj_mode: CutoffMode = "truncate",
    ewald_tolerance: float = 1e-6,
    pme_parameters: tuple[float, int, int, int] | None = None,
) -> mm.System:
    """OpenMM System for a molecular package; force groups as in `TERMS`.

    Non-periodic packages use no cutoff. Periodic packages need `cutoff_nm`: Coulomb then
    uses PME (`ewald_tolerance`, or explicit `pme_parameters` = (α nm⁻¹, nx, ny, nz)), LJ is
    truncated or shifted at the cutoff. 1-4 pairs are computed without cutoff or shift.
    """
    periodic = top.cell_nm is not None
    if periodic and cutoff_nm is None:
        raise ValueError("a periodic package needs a cutoff")
    system = mm.System()
    for mass in top.masses_amu:
        system.addParticle(float(mass))
    if periodic:
        system.setDefaultPeriodicBoxVectors(*(mm.Vec3(*row) for row in top.cell_nm))
    for i, j, length in top.constraints:
        system.addConstraint(i, j, length)

    bonds = mm.HarmonicBondForce()
    for i, j, r0, k in top.bonds:
        bonds.addBond(i, j, r0, k)
    angles = mm.HarmonicAngleForce()
    for i, j, k, theta0, kk in top.angles:
        angles.addAngle(i, j, k, theta0, kk)
    dihedrals = mm.PeriodicTorsionForce()
    for i, j, k, m, n, phase, kk in top.periodic:
        dihedrals.addTorsion(i, j, k, m, n, phase, kk)
    rb = mm.RBTorsionForce()
    for i, j, k, m, c in top.rb:
        rb.addTorsion(i, j, k, m, *c)
    impropers = mm.PeriodicTorsionForce()
    for i, j, k, m, n, phase, kk in top.improper_periodic:
        impropers.addTorsion(i, j, k, m, n, phase, kk)
    # ½k(ξ − ξ0)² with ξ − ξ0 wrapped into one period around zero (spec §5.3).
    harmonic = mm.CustomTorsionForce(
        "0.5*k*d^2; d = theta - xi0 - 2*pi*floor((theta - xi0 + pi)/(2*pi)); pi = 3.141592653589793"
    )
    harmonic.addPerTorsionParameter("xi0")
    harmonic.addPerTorsionParameter("k")
    for i, j, k, m, xi0, kk in top.improper_harmonic:
        harmonic.addTorsion(i, j, k, m, [xi0, kk])

    coulomb = mm.NonbondedForce()
    for q in top.charges_e:
        coulomb.addParticle(float(q), 1.0, 0.0)
    for i, j in top.excluded:
        coulomb.addException(i, j, 0.0, 1.0, 0.0)
    for i, j in top.pairs14:
        qq = top.scale_14_coulomb * top.charges_e[i] * top.charges_e[j]
        coulomb.addException(i, j, float(qq), 1.0, 0.0)
    lj = _lj_nonbonded(
        top.combination_rule, top.sigma_nm, top.epsilon_kjmol, top.pairs, lj_mode == "potential-shift"
    )
    for i, j in (*top.excluded, *top.pairs14):
        lj.addExclusion(i, j)
    lj.setUseLongRangeCorrection(False)
    if periodic:
        coulomb.setNonbondedMethod(mm.NonbondedForce.PME)
        coulomb.setCutoffDistance(cutoff_nm)
        coulomb.setEwaldErrorTolerance(ewald_tolerance)
        if pme_parameters is not None:
            coulomb.setPMEParameters(*pme_parameters)
        lj.setNonbondedMethod(mm.CustomNonbondedForce.CutoffPeriodic)
        lj.setCutoffDistance(cutoff_nm)
        lj.addGlobalParameter("rc", cutoff_nm)
    else:
        coulomb.setNonbondedMethod(mm.NonbondedForce.NoCutoff)
        lj.setNonbondedMethod(mm.CustomNonbondedForce.NoCutoff)
        if lj_mode != "truncate":
            raise ValueError("potential-shift needs a cutoff")
    lj14 = mm.CustomBondForce("4*eps*((sig/r)^12-(sig/r)^6)")
    lj14.addPerBondParameter("sig")
    lj14.addPerBondParameter("eps")
    for i, j in top.pairs14:
        sigma, epsilon = _mix(top, i, j)
        lj14.addBond(i, j, [sigma, top.scale_14_lj * epsilon])
    lj14.setUsesPeriodicBoundaryConditions(periodic)

    for group, force in (
        (1, bonds), (2, angles), (3, dihedrals), (3, rb), (4, impropers), (4, harmonic),
        (5, coulomb), (6, lj), (7, lj14),
    ):
        force.setForceGroup(group)
        system.addForce(force)
    return system


def energy_terms(system: mm.System, positions_nm: np.ndarray, cell_nm: np.ndarray | None = None) -> dict[str, float]:
    """Energy per term (kJ/mol, keys as in `TERMS`) and `total`, on the Reference platform."""
    context = mm.Context(system, mm.VerletIntegrator(0.001), mm.Platform.getPlatformByName("Reference"))
    if cell_nm is not None:
        context.setPeriodicBoxVectors(*(mm.Vec3(*row) for row in cell_nm))
    context.setPositions(positions_nm)
    out = {}
    for group, name in TERMS.items():
        state = context.getState(getEnergy=True, groups={group})
        out[name] = float(state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole))
    out["total"] = float(
        context.getState(getEnergy=True).getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)
    )
    return out


def term_forces(system: mm.System, positions_nm: np.ndarray, cell_nm: np.ndarray | None = None) -> dict[str, np.ndarray]:
    """Forces (kJ mol⁻¹ nm⁻¹) per term of `TERMS`, on the Reference platform."""
    context = mm.Context(system, mm.VerletIntegrator(0.001), mm.Platform.getPlatformByName("Reference"))
    if cell_nm is not None:
        context.setPeriodicBoxVectors(*(mm.Vec3(*row) for row in cell_nm))
    context.setPositions(positions_nm)
    out = {}
    for group, name in TERMS.items():
        state = context.getState(getForces=True, groups={group})
        out[name] = np.asarray(state.getForces(asNumpy=True).value_in_unit(unit.kilojoule_per_mole / unit.nanometer))
    return out
