"""Tests of the V-4 analysis on made-up numbers (written before the runs)."""

import importlib.util
import json
import math
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("v4", Path(__file__).with_name("analyze.py"))
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


def test_ideal_mixing_of_exact_solvents_is_zero_and_scales_with_the_errors():
    assert a.ideal_mixing(0.3, 1.32, 1.32, 1.0, 1.0) == pytest.approx(0.0, abs=1e-12)
    # both solvents 2 % too dense: the mixture is 2 % too dense
    assert a.ideal_mixing(0.3, 1.32 * 1.02, 1.32, 1.02, 1.0) == pytest.approx(2.0, rel=1e-9)
    # only EMC wrong: weighted by its volume fraction (about 0.755 at w_EC = 0.3)
    phi_emc = (0.7 / 1.0) / (0.3 / 1.3214 + 0.7 / 1.0)
    assert a.ideal_mixing(0.3, 1.3214, 1.3214, 1.028, 1.0) == pytest.approx(2.8 * phi_emc, rel=0.02)


def test_v_phi_se_matches_the_finite_difference():
    rho, c, rho0, m = 1.197, 1.0, 1.115, 151.9
    _, se = a.v_phi_se(rho, 0.0, c, rho0, 0.001, m)
    h = 1e-6
    dv = (a.av.v_phi(rho, c, rho0 + h, m) - a.av.v_phi(rho, c, rho0 - h, m)) / (2 * h)
    assert se == pytest.approx(abs(dv) * 0.001, rel=1e-6)
    # Jo's number (feedback 3a): 0.5 % in rho0 moves V_phi at 1 M by about 4.6 cm3/mol
    _, se = a.v_phi_se(rho, 0.0, c, 1.125, 0.005 * 1.125, m)
    assert se == pytest.approx(4.6, abs=0.3)


def test_line_with_se_exact_and_noisy():
    f = a.line_with_se([0.1, 1.0, 2.0, 3.0], [1.1, 1.19, 1.29, 1.39])
    assert f["intercept"] == pytest.approx(1.09) and f["slope"] == pytest.approx(0.1)
    assert f["se_intercept"] == pytest.approx(0.0, abs=1e-9)
    f = a.line_with_se([0.0, 1.0, 2.0, 3.0], [1.0, 1.2, 1.1, 1.3])
    assert f["se_intercept"] > 0 and f["se_slope"] > 0


@pytest.mark.parametrize(("halves", "ok"), [(0.0, True), (0.3, True), (-0.29, True), (0.31, False), (-0.5, False)])
def test_settled(halves, ok):
    assert a.settled({"halves_pct": halves}) is ok


def test_density_from_thermo(tmp_path):
    pkg = tmp_path / "st/systems/x/minimized.ucsys"
    pkg.mkdir(parents=True)
    doc = {"components": [{"molecule_type": "S", "count": 10}],
           "molecule_types": {"S": {"atoms": [{"mass_amu": 10.0}]}}}  # fmt: skip
    (pkg / "system.json").write_text(json.dumps(doc))
    out = tmp_path / "st/runs/x/T20C/out"
    out.mkdir(parents=True)
    rows = ["# step\ttime_ps\tvolume_nm3"] + [f"{i}\t{i * 1.0}\t{10.0 if i < 3 else 12.5}" for i in range(7)]
    (out / "thermo.tsv").write_text("\n".join(rows) + "\n")
    a.STUDIES = tmp_path
    a.sc4.STUDIES = tmp_path
    p = a.density("st", "x", "T20C", 0.5, 6.0)
    rho = [100 * 1.66053906660e-3 / v for v in (10.0, 10.0, 12.5, 12.5, 12.5, 12.5)]
    assert p["rho"] == pytest.approx(sum(rho) / 6)
    assert p["halves_pct"] == pytest.approx(100 * (sum(rho[3:]) / sum(rho[:3]) - 1))
    assert math.isfinite(p["halves_pct"])
