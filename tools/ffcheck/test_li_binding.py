"""Tests of li_binding.py against cases with known answers (run with the oracle's venv)."""

from __future__ import annotations

import dataclasses
import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import li_binding as lb

K_E = lb.COULOMB_KJMOL_NM  # e²N_A/(4πε₀) in kJ mol⁻¹ nm e⁻²


def two_atom_topology(
    q_li: float, q_x: float, sigma: tuple[float, float], eps: tuple[float, float]
):
    """Li at the origin and one 'solvent' atom X on the x axis; geometric mixing."""
    return lb.Topology(
        name="test",
        positions_nm=np.array([[0.0, 0, 0], [0.3, 0, 0]]),
        cell_nm=None,
        masses_amu=np.array([6.94, 16.0]),
        charges_e=np.array([q_li, q_x]),
        sigma_nm=np.array(sigma),
        epsilon_kjmol=np.array(eps),
        combination_rule="geometric",
        scale_14_lj=0.5,
        scale_14_coulomb=0.5,
        bonds=[],
        angles=[],
        periodic=[],
        rb=[],
        improper_periodic=[],
        improper_harmonic=[],
        excluded=[],
        pairs14=[],
        constraints=[],
    )


def test_coulomb_constant_matches_spec():
    # spec/units.md §2: 138.935 457 644 382 kJ mol⁻¹ nm e⁻² (CODATA 2018)
    assert K_E == pytest.approx(138.935457644382, rel=1e-12)


def test_unit_charges_at_1nm():
    top = two_atom_topology(1.0, -1.0, (0.1, 0.1), (0.0, 0.0))
    pos = np.array([[0.0, 0, 0], [1.0, 0, 0]])
    assert lb.total_energy(lb.build_system(top), pos) == pytest.approx(-K_E, rel=1e-10)


def test_binding_energy_of_ion_pair_with_lj_matches_1d_minimum():
    q_li, q_x, s, e = 1.0, -0.5, (0.15, 0.30), (0.1, 0.8)
    top = two_atom_topology(q_li, q_x, s, e)
    sig, eps = math.sqrt(s[0] * s[1]), math.sqrt(e[0] * e[1])
    r = np.linspace(0.12, 0.6, 400001)
    u = K_E * q_li * q_x / r + 4 * eps * ((sig / r) ** 12 - (sig / r) ** 6)
    exact = u.min()
    res = lb.binding_energy(top, li=0, solvent=[1], starts_nm=[np.array([0.0, 0.0, 0.0])])
    assert res.energy_kjmol == pytest.approx(exact, abs=1e-4)
    assert res.distance_nm == pytest.approx(r[u.argmin()], abs=1e-4)


def test_decoupled_atoms_do_not_contribute():
    # A third atom (stand-in for PF6-) is decoupled: same result as without it.
    base = two_atom_topology(1.0, -0.5, (0.15, 0.30), (0.1, 0.8))
    three = dataclasses.replace(
        base,
        positions_nm=np.array([[0.0, 0, 0], [0.3, 0, 0], [5.0, 0, 0]]),
        masses_amu=np.array([6.94, 16.0, 30.97]),
        charges_e=np.array([1.0, -0.5, -1.0]),
        sigma_nm=np.array([0.15, 0.30, 0.37]),
        epsilon_kjmol=np.array([0.1, 0.8, 0.8]),
    )
    a = lb.binding_energy(base, li=0, solvent=[1], starts_nm=[np.array([0.0, 0, 0])])
    b = lb.binding_energy(three, li=0, solvent=[1], starts_nm=[np.array([0.0, 0, 0])], decouple=[2])
    assert b.energy_kjmol == pytest.approx(a.energy_kjmol, abs=1e-6)


def test_li_charge_override():
    top = two_atom_topology(1.0, -0.5, (0.15, 0.30), (0.1, 0.8))
    full = lb.binding_energy(top, li=0, solvent=[1], starts_nm=[np.array([0.0, 0, 0])])
    scaled = lb.binding_energy(top, li=0, solvent=[1], starts_nm=[np.array([0.0, 0, 0])], q_li=0.75)
    assert scaled.energy_kjmol > full.energy_kjmol  # weaker attraction
