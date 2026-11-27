"""Tests of the dH_vap baseline analysis."""

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("dh", Path(__file__).with_name("analyze.py"))
dh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dh)


def test_dh_vap_definition():
    # U_gas 10, liquid -30 per molecule (total -15000 for 500), so 40 + RT
    rt = dh.GAS_CONSTANT_KJ_PER_MOL_K * 298.15
    assert dh.dh_vap(10.0, -15000.0, 500, 298.15) == pytest.approx(40.0 + rt)
    assert rt == pytest.approx(2.4790, abs=1e-4)


def test_mean_potential_last_row_wins_and_window(tmp_path):
    p = tmp_path / "thermo.tsv"
    p.write_text(
        "# step\ttime_ps\tpotential_kjmol\n0\t0.0\t100\n1\t1.0\t1\n2\t2.0\t3\n1\t1.0\t5\n3\t3.0\t7\n"
    )
    # after 0.5 ps, up to 2 ps: rows 1 (restarted, value 5) and 2 (3)
    assert dh.mean_potential(p, 0.5, 2.0) == pytest.approx(4.0)


def test_unfinished_run_is_refused(tmp_path):
    p = tmp_path / "thermo.tsv"
    p.write_text("# step\ttime_ps\tpotential_kjmol\n0\t0.0\t1\n")
    with pytest.raises(SystemExit):
        dh.mean_potential(p, 0.0, 2.0)
