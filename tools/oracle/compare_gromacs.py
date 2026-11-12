"""Compare a one-molecule system package with a GROMACS topology, term by term, in OpenMM.

    python compare_gromacs.py PACKAGE TOPOLOGY.top [--tolerance 1e-8]

The package goes through the oracle (`load_topology` → `molecular_system`); the topology goes
through OpenMM's own GROMACS reader (`app.GromacsTopFile`). Both are evaluated in vacuum (no
cutoff, no periodicity) at the package's positions. The two paths share no code: this checks
a builder-made package, including the builder's transcription and unit conversions, against
the original generator output.

The atom order must be the same in both, as for `library` templates transcribed from that
topology. Masses are compared to catch a different order. OpenMM's reader puts proper
periodic dihedrals and periodic impropers into one PeriodicTorsionForce. The mapping below
assumes the LigParGen layout (Ryckaert–Bellemans propers, periodic impropers) and says so in
its output.
"""

from __future__ import annotations

import argparse
import dataclasses
import sys
from pathlib import Path

import numpy as np
import openmm as mm
from openmm import app, unit

import oracle

OPENMM_TERMS = {
    "HarmonicBondForce": "bond",
    "HarmonicAngleForce": "angle",
    "RBTorsionForce": "dihedral",
    "PeriodicTorsionForce": "improper",
    "NonbondedForce": "coulomb",
    "CustomNonbondedForce": "lj",
    "CustomBondForce": "lj14",
}


def gromacs_terms(top_path: Path, positions_nm: np.ndarray) -> tuple[dict[str, float], np.ndarray]:
    top = app.GromacsTopFile(str(top_path), includeDir=str(top_path.parent))
    system = top.createSystem(nonbondedMethod=app.NoCutoff)
    masses = np.array([system.getParticleMass(i).value_in_unit(unit.dalton) for i in range(system.getNumParticles())])
    groups: dict[str, int] = {}
    for k, force in enumerate(system.getForces()):
        name = type(force).__name__
        if name == "CMMotionRemover":
            continue
        if name not in OPENMM_TERMS:
            raise SystemExit(f"unexpected OpenMM force {name}")
        force.setForceGroup(k)
        groups[OPENMM_TERMS[name]] = k
    context = mm.Context(system, mm.VerletIntegrator(0.001), mm.Platform.getPlatformByName("Reference"))
    context.setPositions(positions_nm)
    out = {name: 0.0 for name in oracle.TERMS.values()}
    for name, group in groups.items():
        e = context.getState(getEnergy=True, groups={group}).getPotentialEnergy()
        out[name] = float(e.value_in_unit(unit.kilojoule_per_mole))
    total = context.getState(getEnergy=True).getPotentialEnergy()
    out["total"] = float(total.value_in_unit(unit.kilojoule_per_mole))
    return out, masses


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("package", type=Path)
    ap.add_argument("topology", type=Path)
    ap.add_argument("--tolerance", type=float, default=1e-8, help="relative, per term")
    args = ap.parse_args()
    top = dataclasses.replace(oracle.load_topology(args.package), cell_nm=None)
    ours = oracle.energy_terms(oracle.molecular_system(top), top.positions_nm)
    theirs, masses = gromacs_terms(args.topology, top.positions_nm)
    if masses.shape != top.masses_amu.shape or not np.allclose(masses, top.masses_amu, rtol=1e-6):
        raise SystemExit("atom order or masses differ between package and topology")
    print(f"{args.package.name} vs {args.topology.name} (OpenMM {mm.__version__}, Reference, vacuum)")
    print(f"{'term':<10}{'oracle(package)':>20}{'OpenMM(GROMACS)':>20}{'rel. diff':>12}")
    worst = 0.0
    for name in [*oracle.TERMS.values(), "total"]:
        a, b = ours[name], theirs[name]
        rel = abs(a - b) / max(abs(b), 1e-3)  # terms below 1e-3 kJ/mol are compared absolutely
        worst = max(worst, rel)
        print(f"{name:<10}{a:>20.10f}{b:>20.10f}{rel:>12.2e}")
    print("note: OpenMM's PeriodicTorsionForce is mapped to 'improper' (LigParGen layout)")
    ok = worst <= args.tolerance
    print(f"{'PASS' if ok else 'FAIL'}: worst relative difference {worst:.2e} (tolerance {args.tolerance:g})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
