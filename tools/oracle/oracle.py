"""OpenMM oracle: reference energies and forces for UnitcellMD system packages.

Validation only; never a runtime dependency (PLAN.md §2.1). Converts a spec v0.1 system package
into an OpenMM System and evaluates it with the double-precision Reference platform. Version 0
covers what Phase 0 / E1 need: Lennard-Jones (and point charges without cutoff) with the cutoff
modes of the engine's LJ provider. Bonded terms and PME follow in E2.

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

    @property
    def n_atoms(self) -> int:
        return len(self.masses_amu)


def load_package(path: Path | str) -> Package:
    """Read a parameterized package without bonds (enough for LJ / point-charge references)."""
    path = Path(path)
    doc = json.loads((path / "system.json").read_text(encoding="utf-8"))
    if doc.get("spec_version", "").split(".")[:2] != ["0", "1"]:
        raise ValueError(f"oracle v0 reads spec 0.1 packages, got {doc.get('spec_version')}")
    ff = doc.get("forcefield")
    if ff is None:
        raise ValueError("the oracle needs a parameterized package")
    masses, charges, sigma, epsilon = [], [], [], []
    for component in doc["components"]:
        mtype = doc["molecule_types"][component["molecule_type"]]
        if mtype["bonds"]:
            raise NotImplementedError("bonded systems arrive in E2")
        for _ in range(component["count"]):
            for atom in mtype["atoms"]:
                lj = ff["atom_types"][atom["type"]]
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
    )


def lj_system(pkg: Package, cutoff_nm: float, mode: CutoffMode) -> mm.System:
    """OpenMM System with Lennard-Jones only, via CustomNonbondedForce (exact mixing rule and mode)."""
    if np.any(pkg.charges_e != 0):
        raise NotImplementedError("charged periodic systems need PME (E2)")
    system = mm.System()
    for mass in pkg.masses_amu:
        system.addParticle(float(mass))
    mix = (
        "sig=sqrt(sig1*sig2); eps=sqrt(eps1*eps2)"
        if pkg.combination_rule == "geometric"
        else "sig=0.5*(sig1+sig2); eps=sqrt(eps1*eps2)"
    )
    shift = " - 4*eps*((sig/rc)^12-(sig/rc)^6)" if mode == "potential-shift" else ""
    force = mm.CustomNonbondedForce(f"4*eps*((sig/r)^12-(sig/r)^6){shift}; {mix}")
    force.addGlobalParameter("rc", cutoff_nm)
    force.addPerParticleParameter("sig")
    force.addPerParticleParameter("eps")
    for s, e in zip(pkg.sigma_nm, pkg.epsilon_kjmol, strict=True):
        force.addParticle([float(s), float(e)])
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
