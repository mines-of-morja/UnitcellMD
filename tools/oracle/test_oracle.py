"""The oracle itself is validated against an independent NumPy implementation (spike S2)."""

from pathlib import Path

import numpy as np
import openmm as mm
import pytest

import oracle

FIXTURES = Path(__file__).resolve().parents[2] / "spec" / "fixtures" / "valid"


def numpy_lj(pkg: oracle.Package, cutoff_nm: float, shift: bool) -> tuple[float, np.ndarray, float]:
    """Brute-force minimum-image LJ for a cubic box: energy, forces, virial trace (sum r_ij . F_ij)."""
    box = pkg.cell_nm[0, 0]
    sigma, eps = pkg.sigma_nm[0], pkg.epsilon_kjmol[0]
    d = pkg.positions_nm[:, None, :] - pkg.positions_nm[None, :, :]
    d -= box * np.round(d / box)
    r2 = (d**2).sum(-1)
    np.fill_diagonal(r2, np.inf)
    inside = r2 < cutoff_nm**2
    sr6 = np.where(inside, (sigma**2 / r2) ** 3, 0.0)
    e_shift = 4 * eps * ((sigma / cutoff_nm) ** 12 - (sigma / cutoff_nm) ** 6) if shift else 0.0
    pair_e = np.where(inside, 4 * eps * (sr6**2 - sr6) - e_shift, 0.0)
    f_over_r = np.where(inside, 24 * eps * (2 * sr6**2 - sr6) / r2, 0.0)
    forces = (f_over_r[:, :, None] * d).sum(axis=1)
    virial = 0.5 * np.where(inside, f_over_r * r2, 0.0).sum()  # diagonal: r2 = inf, f = 0
    return 0.5 * pair_e.sum(), forces, virial


@pytest.fixture(scope="module")
def argon() -> oracle.Package:
    return oracle.load_package(FIXTURES / "argon-864")


@pytest.mark.parametrize("mode", ["truncate", "potential-shift"])
def test_openmm_matches_numpy_bruteforce(argon, mode) -> None:
    system = oracle.lj_system(argon, 0.85, mode)
    energy, forces = oracle.evaluate(system, argon.positions_nm, argon.cell_nm)
    e_ref, f_ref, w_ref = numpy_lj(argon, 0.85, shift=(mode == "potential-shift"))
    assert energy == pytest.approx(e_ref, rel=1e-10)
    assert np.max(np.abs(forces - f_ref)) <= 1e-9 * np.sqrt(np.mean(f_ref**2))
    # finite-difference virial only for truncation-free smooth part: compare to analytic r.F
    if mode == "potential-shift":
        assert oracle.virial_trace_fd(system, argon) == pytest.approx(w_ref, rel=1e-5)


def test_dispersion_correction_matches_openmm(argon) -> None:
    """OpenMM's own NonbondedForce long-range correction equals the analytic formula."""
    def nonbonded(with_correction: bool) -> float:
        system = mm.System()
        for m in argon.masses_amu:
            system.addParticle(float(m))
        nb = mm.NonbondedForce()
        nb.setNonbondedMethod(mm.NonbondedForce.CutoffPeriodic)
        nb.setCutoffDistance(0.85)
        nb.setUseDispersionCorrection(with_correction)
        for s, e in zip(argon.sigma_nm, argon.epsilon_kjmol, strict=True):
            nb.addParticle(0.0, float(s), float(e))
        system.addForce(nb)
        system.setDefaultPeriodicBoxVectors(*(mm.Vec3(*row) for row in argon.cell_nm))
        return oracle.evaluate(system, argon.positions_nm, argon.cell_nm)[0]

    correction = nonbonded(True) - nonbonded(False)
    assert correction == pytest.approx(oracle.lj_dispersion_correction(argon, 0.85), rel=1e-9)
