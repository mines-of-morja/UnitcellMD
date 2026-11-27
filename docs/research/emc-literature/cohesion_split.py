"""Where the EMC model's cohesion sits: inter- against intramolecular, Coulomb against LJ (SC-7 step 0).

On frames of SC-1's EMC liquids (1 fs, 500 molecules, 25 C) the potential is recomputed with OpenMM
(CPU platform, the bridge's own System: PME 1.4 nm, tail correction) and compared with the
trajectory's stored energy. Each molecule, made whole by the minimum image, is then evaluated alone
with the gas package's System (no cutoff, direct Coulomb), so

    E_inter / N = (E_liquid - sum_m E_m) / N,   E_intra / N = sum_m E_m / N

and the same with only the Coulomb force (NonbondedForce, incl. 1-4 exceptions) or only the LJ
force (CustomNonbondedForce, incl. the tail correction). The 1-4 and bonded terms are purely
intramolecular. The gas-phase package's own start energy is printed against the engine's step-0
value as a cross-check of the two providers.

    cd ucmd-engine/bridge && .venv/bin/python ../../docs/research/emc-literature/cohesion_split.py OUT.json

Units: kJ/mol, nm, ps.
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

import h5py
import numpy as np
import openmm as mm
from ucmd_bridge.model import NonbondedSettings, build_system
from ucmd_bridge.package import load

ROOT = Path(__file__).resolve().parents[3]
LIQ = ROOT / "studies/2026-11-25_timestep-emc-1fs"
GAS = ROOT / "studies/2026-11-27_emc-dhvap-baseline/systems/emc_gas_s1/minimized.ucsys"
GAS_THERMO = ROOT / "studies/2026-11-27_emc-dhvap-baseline/runs/emc_gas_s1/T25C/out/thermo.tsv"
SEEDS = (1, 2, 3)
SKIP_PS, N_FRAMES = 500.0, 8
COULOMB, LJ = 1, 2  # force groups
KJ = mm.unit.kilojoule_per_mole


def grouped(system: mm.System) -> None:
    for force in system.getForces():
        if isinstance(force, mm.NonbondedForce):
            force.setForceGroup(COULOMB)
        elif isinstance(force, mm.CustomNonbondedForce):
            force.setForceGroup(LJ)
        else:
            force.setForceGroup(0)


def energies(ctx: mm.Context) -> tuple[float, float, float]:
    """Total, Coulomb and LJ potential energy, kJ/mol."""

    def e(groups=-1):
        return ctx.getState(getEnergy=True, groups=groups).getPotentialEnergy().value_in_unit(KJ)

    return e(), e({COULOMB}), e({LJ})


def provider(run_toml: Path) -> dict:
    import tomllib

    return tomllib.loads(run_toml.read_text())["providers"][0]


def main(out_path: Path) -> None:
    gas = load(GAS)
    sys_g, _ = build_system(gas, NonbondedSettings.from_provider({"kind": "force-field", "coulomb": "direct"}))
    grouped(sys_g)
    ctx_g = mm.Context(sys_g, mm.VerletIntegrator(0.001), mm.Platform.getPlatformByName("Reference"))
    ctx_g.setPositions([mm.Vec3(*p) for p in gas.positions_nm])
    with GAS_THERMO.open() as fh:
        names = fh.readline().lstrip("# ").strip().split("\t")
        engine_step0 = float(fh.readline().split("\t")[names.index("potential_kjmol")])
    n = len(gas.masses_amu)
    result: dict = {
        "cross_check_gas_start": {"openmm_kjmol": energies(ctx_g)[0], "engine_step0_kjmol": engine_step0},
        "seeds": {},
    }
    for s in SEEDS:
        run = LIQ / f"runs/emc_500_s{s}/T25C"
        liq = load(LIQ / f"systems/emc_500_s{s}/minimized.ucsys")
        sys_l, _ = build_system(liq, NonbondedSettings.from_provider(provider(run / "run.toml")))
        grouped(sys_l)
        ctx_l = mm.Context(sys_l, mm.VerletIntegrator(0.001), mm.Platform.getPlatformByName("CPU"))
        with h5py.File(run / "out/trajectory.h5", "r") as f:
            xs = f["particles/all/position/value"]
            boxes = f["particles/all/box/edges/value"]
            t = f["particles/all/position/time"][:]
            pe = f["observables/potential_energy/value"][:]
            pe_t = f["observables/potential_energy/time"][:]
            later = np.flatnonzero(t > SKIP_PS)
            frames = later[:: max(1, len(later) // N_FRAMES)][:N_FRAMES]
            rows = []
            for i in frames:
                x = xs[i].astype(np.float64)
                box = boxes[i].astype(np.float64)
                if np.count_nonzero(box - np.diag(np.diag(box))):
                    raise SystemExit("expected an orthorhombic box")
                edge = np.diag(box)
                ctx_l.setPeriodicBoxVectors(*[mm.Vec3(*r) for r in box])
                ctx_l.setPositions([mm.Vec3(*p) for p in x])
                tot, q, lj = energies(ctx_l)
                n_mol = len(x) // n
                intra = np.zeros(3)
                for m in range(n_mol):
                    y = x[m * n : (m + 1) * n]
                    y = y[0] + (y - y[0] + edge / 2) % edge - edge / 2
                    ctx_g.setPositions([mm.Vec3(*p) for p in y])
                    intra += energies(ctx_g)
                j = int(np.argmin(abs(pe_t - t[i])))
                rows.append(
                    {
                        "time_ps": float(t[i]),
                        "liquid_kjmol": tot,
                        "trajectory_kjmol": float(pe[j]),
                        "intra_per_molecule": intra[0] / n_mol,
                        "inter_per_molecule": (tot - intra[0]) / n_mol,
                        "inter_coulomb_per_molecule": (q - intra[1]) / n_mol,
                        "inter_lj_per_molecule": (lj - intra[2]) / n_mol,
                    }
                )
        keys = [k for k in rows[0] if k.endswith("per_molecule")]
        result["seeds"][s] = {
            "frames": rows,
            "mean": {k: statistics.fmean(r[k] for r in rows) for k in keys},
            "max_abs_recompute_minus_trajectory_kjmol": max(
                abs(r["liquid_kjmol"] - r["trajectory_kjmol"]) for r in rows
            ),
        }
    keys = list(result["seeds"][SEEDS[0]]["mean"])
    per_seed = {k: [result["seeds"][s]["mean"][k] for s in SEEDS] for k in keys}
    result["mean_over_seeds"] = {
        k: {"mean": statistics.fmean(v), "se": statistics.stdev(v) / len(v) ** 0.5} for k, v in per_seed.items()
    }
    out_path.write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps({"cross_check": result["cross_check_gas_start"], "mean": result["mean_over_seeds"]}, indent=1))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]))
