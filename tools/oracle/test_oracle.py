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


# ---------------------------------------------------------------------------------------------
# Version 1: molecular packages

K_E = 138.93545764438196  # e²N_A/(4πε₀) in kJ mol⁻¹ nm e⁻², spec/units.md §2


def test_water_terms_equal_a_numpy_hand_calculation() -> None:
    top = oracle.load_topology(FIXTURES / "water-2")
    assert top.excluded == [(0, 1), (0, 2), (1, 2), (3, 4), (3, 5), (4, 5)] and top.pairs14 == []
    terms = oracle.energy_terms(oracle.molecular_system(top), top.positions_nm)
    x = top.positions_nm
    bond = sum(0.5 * k * (np.linalg.norm(x[i] - x[j]) - r0) ** 2 for i, j, r0, k in top.bonds)
    angle = 0.0
    for i, j, k, theta0, kk in top.angles:
        u, v = x[i] - x[j], x[k] - x[j]
        theta = np.arccos(u @ v / np.linalg.norm(u) / np.linalg.norm(v))
        angle += 0.5 * kk * (theta - theta0) ** 2
    coulomb = lj = 0.0
    for i in range(3):
        for j in range(3, 6):
            r = np.linalg.norm(x[i] - x[j])
            coulomb += K_E * top.charges_e[i] * top.charges_e[j] / r
            sigma = 0.5 * (top.sigma_nm[i] + top.sigma_nm[j])  # Lorentz–Berthelot
            eps = np.sqrt(top.epsilon_kjmol[i] * top.epsilon_kjmol[j])
            lj += 4 * eps * ((sigma / r) ** 12 - (sigma / r) ** 6)
    assert terms["bond"] == pytest.approx(bond, rel=1e-10)
    assert terms["angle"] == pytest.approx(angle, rel=1e-10)
    assert terms["coulomb"] == pytest.approx(coulomb, rel=1e-10)
    assert terms["lj"] == pytest.approx(lj, rel=1e-10)
    assert terms["total"] == pytest.approx(bond + angle + coulomb + lj, rel=1e-10)


def test_nacl_pme_energy_gives_the_madelung_constant() -> None:
    top = oracle.load_topology(FIXTURES / "nacl-crystal")
    a = top.cell_nm[0, 0] / 2  # two conventional cells per edge
    r0 = a / 2  # nearest-neighbour distance
    system = oracle.molecular_system(top, cutoff_nm=0.55, ewald_tolerance=1e-10)
    terms = oracle.energy_terms(system, top.positions_nm, top.cell_nm)
    pairs = top.n_atoms // 2
    madelung = -terms["coulomb"] * r0 / (pairs * K_E)
    assert madelung == pytest.approx(1.747565, abs=2e-6)  # NaCl, referred to r0 (PLAN.md E2.3)
