"""Tests of the SC-1 verdicts on made-up numbers (written before the runs)."""

import importlib.util
import json
import math
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("sc1", Path(__file__).with_name("analyze.py"))
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


def test_compare_by_hand():
    c = a.compare([1.0, 2.0, 3.0], [2.0, 3.0, 4.0])  # s2 = 1 in both arms
    assert c["diff"] == pytest.approx(1.0)
    assert c["se"] == pytest.approx(math.sqrt(2 / 3))
    assert c["diff_pct"] == pytest.approx(50.0)


@pytest.mark.parametrize(
    ("diff", "se", "expected"),
    [
        (0.30, 0.04, "matters"),
        (-0.30, 0.04, "matters"),  # the sign is not part of the criterion
        (0.30, 0.20, "unresolved"),  # large, but not 2 SE
        (0.09, 0.03, "unresolved"),  # 3 SE, but not above 0.1 %; up to 0.15 % is possible
        (0.02, 0.03, "below 0.1 %"),
        (0.02, 0.05, "unresolved"),
    ],
)
def test_verdict(diff, se, expected):
    assert a.verdict({"diff_pct": diff, "se_pct": se}) == expected


def test_timestep_reads_the_electrolyte_only():
    low = "below 0.1 %"
    assert a.timestep({"1M": low, "EMC": low, "water": "matters"}) == "1 fs"
    assert a.timestep({"1M": "matters", "EMC": low, "water": low}).startswith("0.5 fs")
    assert a.timestep({"1M": low, "EMC": "unresolved", "water": low}).startswith("unresolved")


def write_run(tmp_path, rows):
    out = tmp_path / "run/out"
    out.mkdir(parents=True)
    lines = ["# step\ttime_ps\tvolume_nm3"] + ["\t".join(map(str, r)) for r in rows]
    (out / "thermo.tsv").write_text("\n".join(lines) + "\n")
    pkg = tmp_path / "p.ucsys"
    pkg.mkdir()
    doc = {"components": [{"molecule_type": "w", "count": 2}],
           "molecule_types": {"w": {"atoms": [{"mass_amu": 10.0}, {"mass_amu": 2.0}]}}}  # fmt: skip
    (pkg / "system.json").write_text(json.dumps(doc))
    return tmp_path / "run", pkg


def test_density_units_skip_and_repeated_rows(tmp_path):
    rows = [(0, 0.0, 9.0), (1, 1.0, 9.0), (2, 2.0, 9.0), (2, 2.0, 1.0), (3, 3.0, 1.0)]
    run, pkg = write_run(tmp_path, rows)
    rho = a.densities(run, pkg, 1.0, 3.0)  # the restarted row 2 replaces the first one
    assert rho == pytest.approx([24 * 1.66053906660e-3] * 2)


def test_unfinished_run_stops(tmp_path):
    run, pkg = write_run(tmp_path, [(0, 0.0, 1.0), (1, 1.0, 1.0)])
    with pytest.raises(SystemExit, match="not finished"):
        a.densities(run, pkg, 0.0, 5.0)
