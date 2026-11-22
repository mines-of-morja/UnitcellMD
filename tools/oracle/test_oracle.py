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


# ---------------------------------------------------------------------------------------------
# Spec 0.1.2: pair overrides (Kob-Andersen fixture; ADR 0015)


@pytest.fixture(scope="module")
def kob_andersen() -> oracle.Package:
    return oracle.load_package(FIXTURES / "kob-andersen-500")


def numpy_lj_pairs(pkg: oracle.Package, cutoff_nm: float, shift: bool) -> tuple[float, np.ndarray]:
    """Brute-force minimum-image LJ with per-pair σ, ε from the package's pair table."""
    box = pkg.cell_nm[0, 0]
    t = pkg.pairs.type_index
    sigma = pkg.pairs.sigma_nm[t[:, None], t[None, :]]
    eps = pkg.pairs.epsilon_kjmol[t[:, None], t[None, :]]
    d = pkg.positions_nm[:, None, :] - pkg.positions_nm[None, :, :]
    d -= box * np.round(d / box)
    r2 = (d**2).sum(-1)
    np.fill_diagonal(r2, np.inf)
    inside = r2 < cutoff_nm**2
    sr6 = np.where(inside, (sigma**2 / r2) ** 3, 0.0)
    e_shift = 4 * eps * ((sigma / cutoff_nm) ** 12 - (sigma / cutoff_nm) ** 6) if shift else 0.0
    pair_e = np.where(inside, 4 * eps * (sr6**2 - sr6) - e_shift, 0.0)
    f_over_r = np.where(inside, 24 * eps * (2 * sr6**2 - sr6) / r2, 0.0)
    return 0.5 * pair_e.sum(), (f_over_r[:, :, None] * d).sum(axis=1)


def test_kob_andersen_table_has_the_override(kob_andersen) -> None:
    p = kob_andersen.pairs
    assert p is not None
    a, b = p.type_index[0], p.type_index[-1]  # all A first, then all B
    assert p.sigma_nm[a, b] == p.sigma_nm[b, a] == pytest.approx(0.8 * 0.34, rel=1e-9)
    assert p.epsilon_kjmol[a, b] / p.epsilon_kjmol[a, a] == pytest.approx(1.5, rel=1e-12)
    assert p.sigma_nm[b, b] == pytest.approx(0.88 * 0.34, rel=1e-9)  # the rule, no override


@pytest.mark.parametrize("mode", ["truncate", "potential-shift"])
def test_pair_overrides_match_numpy_bruteforce(kob_andersen, mode) -> None:
    system = oracle.lj_system(kob_andersen, 0.85, mode)
    energy, forces = oracle.evaluate(system, kob_andersen.positions_nm, kob_andersen.cell_nm)
    e_ref, f_ref = numpy_lj_pairs(kob_andersen, 0.85, shift=(mode == "potential-shift"))
    assert energy == pytest.approx(e_ref, rel=1e-10)
    assert np.max(np.abs(forces - f_ref)) <= 1e-9 * np.sqrt(np.mean(f_ref**2))


def test_overrides_equal_to_the_rule_change_nothing(kob_andersen) -> None:
    """A1: a table filled by the combination rule gives the per-particle result."""
    import dataclasses

    rule_pkg = dataclasses.replace(kob_andersen, pairs=None)
    rule_table = oracle.pair_table(
        {
            "combination_rule": kob_andersen.combination_rule,
            "atom_types": {
                "A": {"sigma_nm": kob_andersen.sigma_nm[0], "epsilon_kjmol": kob_andersen.epsilon_kjmol[0]},
                "B": {"sigma_nm": kob_andersen.sigma_nm[-1], "epsilon_kjmol": kob_andersen.epsilon_kjmol[-1]},
            },
            "pair_overrides": [
                {
                    "types": ["A", "B"],
                    "sigma_nm": 0.5 * (kob_andersen.sigma_nm[0] + kob_andersen.sigma_nm[-1]),
                    "epsilon_kjmol": float(np.sqrt(kob_andersen.epsilon_kjmol[0] * kob_andersen.epsilon_kjmol[-1])),
                }
            ],
        },
        ["A"] * 400 + ["B"] * 100,
    )
    table_pkg = dataclasses.replace(kob_andersen, pairs=rule_table)
    e_rule, f_rule = oracle.evaluate(oracle.lj_system(rule_pkg, 0.85, "truncate"), rule_pkg.positions_nm, rule_pkg.cell_nm)
    e_tab, f_tab = oracle.evaluate(oracle.lj_system(table_pkg, 0.85, "truncate"), table_pkg.positions_nm, table_pkg.cell_nm)
    assert e_tab == pytest.approx(e_rule, rel=1e-12)
    assert np.max(np.abs(f_tab - f_rule)) <= 1e-12 * np.sqrt(np.mean(f_rule**2))


def test_type_pair_dispersion_correction(kob_andersen, argon) -> None:
    """A4: the analytic sum over type pairs (N_a N_b, as the engine's lj.rs) reduces to the
    single-type formula and agrees with OpenMM's long-range correction up to OpenMM's pair count.

    OpenMM's CustomNonbondedForce counts n_a(n_a + 1)/2 pairs within a class and n_a n_b across
    classes, then rescales the total to N²/2. For one type that is N²/2 as well; for several types
    it differs from N_a N_b by O(1/N). Here the convention is reproduced exactly.
    """
    assert oracle.lj_dispersion_correction_types(argon, 0.85) == pytest.approx(
        oracle.lj_dispersion_correction(argon, 0.85), rel=1e-12
    )
    pkg = kob_andersen

    def energy(with_correction: bool) -> float:
        system = oracle.lj_system(pkg, 0.85, "truncate")
        system.getForce(0).setUseLongRangeCorrection(with_correction)
        return oracle.evaluate(system, pkg.positions_nm, pkg.cell_nm)[0]

    correction = energy(True) - energy(False)
    analytic = oracle.lj_dispersion_correction_types(pkg, 0.85)
    p = pkg.pairs
    n = np.bincount(p.type_index).astype(float)
    x = p.sigma_nm / 0.85
    per_pair = p.epsilon_kjmol * p.sigma_nm**3 * (x**9 / 3.0 - x**3)
    total = n.sum()
    openmm_count = (np.outer(n, n) + np.diag(n)) * total / (total + 1.0)
    volume = abs(float(np.linalg.det(pkg.cell_nm)))
    openmm_convention = 8.0 / 3.0 * np.pi / volume * float((openmm_count * per_pair).sum())
    assert correction == pytest.approx(openmm_convention, rel=1e-6)
    assert analytic == pytest.approx(openmm_convention, rel=1e-3)  # the O(1/N) difference
    assert abs(analytic / correction - 1.0) > 1e-5  # ...which is real for two types
