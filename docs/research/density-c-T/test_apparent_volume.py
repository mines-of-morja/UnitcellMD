"""Tests of the apparent-molar-volume formula (apparent_volume.py)."""

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("av", Path(__file__).with_name("apparent_volume.py"))
av = importlib.util.module_from_spec(spec)
spec.loader.exec_module(av)


def test_linear_density_gives_a_constant_v_phi():
    rho0, s, m = 1.09, 0.09, 151.9
    expected = (m - 1000.0 * s) / rho0
    for c in (0.1, 1.0, 3.0):
        assert av.v_phi(rho0 + s * c, c, rho0, m) == pytest.approx(expected, rel=1e-12)


def test_salt_that_adds_its_own_volume_at_solvent_density_has_v_equal_m_over_rho0():
    # a "salt" as dense as the solvent: rho stays rho0, so V_phi = M / rho0
    assert av.v_phi(1.2, 2.0, 1.2, 150.0) == pytest.approx(150.0 / 1.2)


def test_line_recovers_intercept_and_slope():
    b, s = av.line([0.0, 1.0, 2.0], [1.0, 1.5, 2.0])
    assert (b, s) == (pytest.approx(1.0), pytest.approx(0.5))
