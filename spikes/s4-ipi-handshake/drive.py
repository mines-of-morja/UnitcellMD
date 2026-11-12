"""Spike S4 driver: Rust i-PI server <-> ASE SocketClient (spec/force-provider.md §5, ADR 0007).

usage: python drive.py <check|latency> [--codata 2014|2018]

check:   argon-864 (cubic) and a sheared triclinic copy, ASE LennardJones as the calculator;
         compares what the Rust server received with a direct ASE evaluation and with the
         OpenMM reference of tools/oracle.
latency: a calculator that returns zeros, 2000 round trips, 864 atoms.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SERVER = HERE / "server" / "target" / "release" / "s4-ipi-server"
FIXTURE = ROOT / "spec" / "fixtures" / "valid" / "argon-864"
REFERENCE = ROOT / "tools" / "oracle" / "reference" / "argon-864"
OUT = HERE / "out"


def set_codata(version: str) -> None:
    """Make every ASE module (including socketio) use the given CODATA constants."""
    import ase.units

    if version != "2014":
        for key, value in ase.units.create_units("2018").items():
            setattr(ase.units, key, value)
    if version == "spec":
        # pin the two wire constants to the tabulated values of spec/units.md §2
        # (create_units derives them from other constants; they differ by ~1e-11)
        ase.units.Bohr = 0.529177210903
        ase.units.Hartree = ase.units.Ha = 4.3597447222071e-18 / 1.602176634e-19


def run_server(name: str, cell_nm: np.ndarray, positions_nm: np.ndarray, repeats: int, calc) -> dict:
    from ase import Atoms
    from ase.calculators.socketio import SocketClient

    OUT.mkdir(exist_ok=True)
    payload = (
        np.ascontiguousarray(cell_nm, "<f8").tobytes()
        + np.uint64(len(positions_nm)).tobytes()
        + np.ascontiguousarray(positions_nm, "<f8").tobytes()
    )
    (OUT / f"{name}.bin").write_bytes(payload)
    result_file = OUT / f"{name}.json"
    server = subprocess.Popen([str(SERVER), name, str(OUT / f"{name}.bin"), str(repeats), str(result_file)])
    socket = Path(f"/tmp/ipi_{name}")
    for _ in range(200):
        if socket.exists():
            break
        time.sleep(0.01)
    atoms = Atoms(f"Ar{len(positions_nm)}", positions=positions_nm * 10, cell=cell_nm * 10, pbc=True)
    atoms.calc = calc
    SocketClient(unixsocket=name).run(atoms, use_stress=True)
    server.wait(timeout=60)
    return json.loads(result_file.read_text())


def direct(cell_nm: np.ndarray, positions_nm: np.ndarray, calc) -> tuple[float, np.ndarray, np.ndarray]:
    """Direct ASE evaluation, converted with ASE's own constants to kJ/mol and nm."""
    from ase import Atoms, units

    ev = 1.0 / (units.kJ / units.mol)
    atoms = Atoms(f"Ar{len(positions_nm)}", positions=positions_nm * 10, cell=cell_nm * 10, pbc=True)
    atoms.calc = calc
    energy = atoms.get_potential_energy() * ev
    forces = atoms.get_forces() * ev * 10
    virial = -atoms.get_volume() * atoms.get_stress(voigt=False) * ev
    return energy, forces, virial


def lj_calculator():
    from ase import units
    from ase.calculators.lj import LennardJones

    return LennardJones(sigma=3.4, epsilon=120.0 * units.kB, rc=8.5, smooth=False)


def check() -> dict:
    doc = json.loads((FIXTURE / "system.json").read_text())
    cell = np.array(doc["cell_nm"])
    positions = np.load(FIXTURE / "positions.npy")
    report: dict[str, object] = {}

    got = run_server("ucmd_s4_cubic", cell, positions, 1, lj_calculator())
    e_ase, f_ase, w_ase = direct(cell, positions, lj_calculator())
    f_got = np.array(got["forces"]).reshape(-1, 3)
    rms = np.sqrt(np.mean(f_ase**2))
    report["cubic_energy_server_kjmol"] = got["energy_kjmol"]
    report["cubic_energy_rel_dev_vs_direct_ase"] = got["energy_kjmol"] / e_ase - 1
    report["cubic_forces_max_dev_over_rms"] = float(np.max(np.abs(f_got - f_ase)) / rms)
    report["cubic_virial_rel_dev_vs_direct_ase"] = float(
        np.max(np.abs(np.array(got["virial_kjmol"]) - w_ase)) / np.max(np.abs(w_ase))
    )
    report["extra_bytes_from_ase"] = got["extra_bytes"]
    for mode in ("potential-shift", "truncate"):
        ref = json.loads((REFERENCE / f"lj-{mode}-rc0.85.json").read_text())
        report[f"energy_rel_dev_vs_openmm_{mode}"] = got["energy_kjmol"] / ref["energy_kjmol"] - 1
    ref = json.loads((REFERENCE / "lj-potential-shift-rc0.85.json").read_text())
    report["virial_rel_dev_vs_numpy_reference"] = float(
        np.max(np.abs(np.array(got["virial_kjmol"]) - np.array(ref["virial_kjmol"])))
        / np.max(np.abs(ref["virial_kjmol"]))
    )
    report["forces_rel_dev_vs_openmm_potential_shift"] = float(
        np.max(np.abs(f_got - np.load(REFERENCE / "lj-potential-shift-rc0.85-forces.npy"))) / rms
    )

    # Triclinic: shear the cell (b_x = 0.25 a_x) and the positions affinely (same fractional coords).
    sheared = cell.copy()
    sheared[1, 0] = 0.25 * cell[0, 0]
    positions_tri = positions @ np.linalg.inv(cell) @ sheared
    got_t = run_server("ucmd_s4_tri", sheared, positions_tri, 1, lj_calculator())
    e_t, f_t, w_t = direct(sheared, positions_tri, lj_calculator())
    report["triclinic_energy_rel_dev_vs_direct_ase"] = got_t["energy_kjmol"] / e_t - 1
    report["triclinic_forces_max_dev_over_rms"] = float(
        np.max(np.abs(np.array(got_t["forces"]).reshape(-1, 3) - f_t)) / np.sqrt(np.mean(f_t**2))
    )
    # Same check with the cell sent untransposed would give a different structure:
    wrong = run_server("ucmd_s4_wrong", sheared.T.copy(), positions_tri, 1, lj_calculator())
    report["triclinic_with_transposed_cell_energy_rel_dev"] = wrong["energy_kjmol"] / e_t - 1
    return report


def latency() -> dict:
    from ase.calculators.calculator import Calculator, all_changes

    class Zero(Calculator):
        implemented_properties = ["energy", "forces", "stress"]

        def calculate(self, atoms=None, properties=("energy",), system_changes=all_changes):
            super().calculate(atoms, properties, system_changes)
            self.results = {"energy": 0.0, "forces": np.zeros((len(atoms), 3)), "stress": np.zeros(6)}

    doc = json.loads((FIXTURE / "system.json").read_text())
    got = run_server("ucmd_s4_latency", np.array(doc["cell_nm"]), np.load(FIXTURE / "positions.npy"), 2000, Zero())
    return {"atoms": 864, "repeats": got["repeats"], "per_step_ms": got["per_step_ms"]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("what", choices=["check", "latency"])
    parser.add_argument("--codata", default="2014", choices=["2014", "2018", "spec"])
    args = parser.parse_args()
    set_codata(args.codata)
    result = check() if args.what == "check" else latency()
    result["ase_codata"] = args.codata
    json.dump(result, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main()
