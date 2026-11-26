"""Tests of the SC-4 verdicts on made-up numbers (written before the runs)."""

import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("sc4", Path(__file__).with_name("analyze.py"))
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


def test_reference_at_1M_20C():
    assert a.reference(1.0, 293.15) == pytest.approx(1.1816665)  # the 1.1817 of SC-8


@pytest.mark.parametrize(
    ("dev", "halves", "expected"),
    [(1.4, 0.1, "pass"), (-1.5, 0.0, "pass"), (1.6, 0.1, "FAIL"), (-2.2, 0.1, "FAIL"),
     (0.5, 0.31, "not settled"), (3.0, -0.4, "not settled")],
)  # fmt: skip
def test_judge(dev, halves, expected):
    assert a.judge({"dev_pct": dev, "halves_pct": halves}) == expected


def test_slope_exact_line_and_noise():
    b, se = a.slope([0.0, 1.0, 2.0, 3.0], [1.0, 1.1, 1.2, 1.3])
    assert b == pytest.approx(0.1) and se == pytest.approx(0.0, abs=1e-12)
    b, se = a.slope([0.0, 1.0, 2.0], [0.0, 1.0, 0.0])
    assert b == pytest.approx(0.0) and se > 0


def test_point_density_and_concentration(tmp_path):
    pkg = tmp_path / "systems/x/minimized.ucsys"
    pkg.mkdir(parents=True)
    doc = {"components": [{"molecule_type": "Li", "count": 6},
                          {"molecule_type": "S", "count": 10}],
           "molecule_types": {"Li": {"atoms": [{"mass_amu": 7.0}]}, "S": {"atoms": [{"mass_amu": 10.0}]}}}  # fmt: skip
    (pkg / "system.json").write_text(json.dumps(doc))
    out = tmp_path / "runs/x/T20C/out"
    out.mkdir(parents=True)
    rows = ["# step\ttime_ps\tvolume_nm3"] + [f"{i}\t{i * 1.0}\t10.0" for i in range(5)]
    (out / "thermo.tsv").write_text("\n".join(rows) + "\n")
    a.STUDIES = tmp_path.parent
    p = a.point(tmp_path.name, "x", "T20C", 0.5, 4.0)
    assert p["rho"] == pytest.approx(142 * 1.66053906660e-3 / 10)
    assert p["c_mol_l"] == pytest.approx(6 / 6.02214076e23 / 1e-23)
    assert p["T_K"] == pytest.approx(293.15) and p["halves_pct"] == pytest.approx(0.0)


def test_unfinished_run_stops(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    (out / "thermo.tsv").write_text("# step\ttime_ps\tvolume_nm3\n0\t0.0\t1.0\n")
    with pytest.raises(SystemExit, match="not finished"):
        a.volumes(tmp_path, 0.0, 3000.0)
