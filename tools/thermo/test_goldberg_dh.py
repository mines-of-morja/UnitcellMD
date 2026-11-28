"""Tests of goldberg_dh.py against cases with known answers."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import goldberg_dh as g


@pytest.mark.parametrize("solvent", ["EMC", "DMC"])
def test_boiling_point_inverts_pressure(solvent):
    tb = g.boiling_point_k(solvent)
    assert g.pressure_pa(solvent, tb) == pytest.approx(101325.0, rel=1e-12)


@pytest.mark.parametrize("solvent", ["EMC", "DMC"])
def test_dh_is_slope_of_ln_p(solvent):
    # Clausius-Clapeyron: d ln p / d(1/T) = -dH/R, central difference in 1/T.
    t, h = 298.15, 1e-7
    x1, x2 = 1 / t - h, 1 / t + h
    slope = (math.log(g.pressure_pa(solvent, 1 / x2)) - math.log(g.pressure_pa(solvent, 1 / x1))) / (x2 - x1)
    assert -slope * g.R / 1000 == pytest.approx(g.dh_vap_kj_mol(solvent, t), rel=1e-6)


def test_emc_values_used_in_ledger_note():
    assert g.pressure_pa("EMC", 298.15) / 1000 == pytest.approx(3.4366, abs=5e-4)
    assert g.dh_vap_kj_mol("EMC", 298.15) == pytest.approx(40.35, abs=0.01)
    assert g.boiling_point_k("EMC") == pytest.approx(381.03, abs=0.01)


def test_range_flags():
    assert g.in_range("EMC", 298.15)
    assert g.in_range("DMC", 298.15)
    assert not g.in_range("EMC", 290.0)


def test_line_fit_recovers_exact_antoine():
    t = [290.0, 300.0, 310.0, 320.0]
    p = [g.pressure_pa('EMC', x) / 1000 for x in t]
    dh, _, _ = g.line_fit_dh(t, p)
    assert dh == pytest.approx(g.dh_vap_kj_mol('EMC', 305.0), rel=2e-3)


def test_dougassa_line_fit():
    dh, se, p298 = g.line_fit_dh(g.DOUGASSA_EMC_T, [v / 10 for v in g.DOUGASSA_EMC_TEN_P])
    assert dh == pytest.approx(40.69, abs=0.01)
    assert se == pytest.approx(0.57, abs=0.01)
    assert p298 == pytest.approx(3.399, abs=0.002)
