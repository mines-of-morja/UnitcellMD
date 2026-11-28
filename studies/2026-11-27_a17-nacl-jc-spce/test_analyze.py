"""Known answers for reference.py and the criterion of analyze.py (pytest test_analyze.py)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import analyze
import reference


def test_the_printed_fit_reproduces_table_iv_where_the_paper_says_it_does():
    ref = reference.reference()
    table = [-0.138, -0.29, -0.34, -0.31, -0.24, 0.03, 0.28, 0.60, 0.82]
    fit = ref["printed_fit_vs_table_IV"]
    # from 0.56 mol/kg on, the fit lies within 1.5 printed errors (0.05) of every row
    assert all(abs(f - t) <= 0.075 for f, t in zip(fit[2:], table[2:], strict=True))
    assert ref["chi2_per_dof"] > 1  # the reason for the Birge ratio


def test_reference_values():
    g = reference.reference()["gamma"]
    assert g["1"]["value"] == pytest.approx(1.078, abs=1e-3)
    assert g["3"]["value"] == pytest.approx(1.760, abs=1e-3)
    assert 0.1 < g["3"]["uncertainty"] < 0.2


def test_criterion():
    assert analyze.verdict(1.70, 0.05, 1.76, 0.146, True)["verdict"] == "pass"
    assert analyze.verdict(1.40, 0.05, 1.76, 0.146, True)["verdict"] == "FAIL"
    assert analyze.verdict(1.76, 0.05, 1.76, 0.146, False)["verdict"].startswith("not judged")
