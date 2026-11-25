"""Tests of analyze.py with made-up numbers (no simulation)."""

import json
import math

import analyze as a


def arm(rho, p=None):
    return [
        {"rho": r, "block_se": 0.0005, "halves": 0.0, "pressure": 0.0, "p_mol": 1.0 + 5 * k}
        for k, r in enumerate(rho)
    ]


B = (1.0068, 1.0072, 1.0076)


def texts(shift_a, shift_g=0.0, **change):
    arms = {
        "A": arm([r + shift_a for r in B]),
        "B": arm(B),
        "G": arm([r + shift_g for r in B]),
    }
    for key, value in change.items():
        arms["B"][0][key] = value
    return " | ".join(a.verdict(arms))


def test_verdicts():
    assert "effect confirmed" in texts(0.0058) and "consistent" in texts(0.0058)
    assert "effect of another size" in texts(0.0100)
    assert "effect not seen" in texts(0.0002)
    assert "DIFFERENT" in texts(0.0058, shift_g=0.0020)


def test_refusals():
    assert "not judged" in texts(0.0058, halves=0.0040)
    assert "nothing else is read" in texts(0.0058, p_mol=200.0)
    wide = {k: arm([1.000, 1.0072, 1.014]) for k in "ABG"}
    assert " | ".join(a.verdict(wide)).count("unresolved") == 2


def test_run_summary(tmp_path):
    package = tmp_path / "p.ucsys"
    package.mkdir()
    atoms = [{"mass_amu": 15.9994}, {"mass_amu": 1.008}, {"mass_amu": 1.008}]
    doc = {
        "components": [{"molecule_type": "w", "count": 512}],
        "molecule_types": {"w": {"atoms": atoms}},
    }
    (package / "system.json").write_text(json.dumps(doc))
    out = tmp_path / "run/out"
    out.mkdir(parents=True)
    rows = ["# step\ttime_ps\tpressure_bar\tvolume_nm3"]
    rows += [f"{i}\t{i}\t{'nan' if i % 2 else 3.0}\t{20.0 if i <= 200 else 15.2}" for i in range(1001)]
    (out / "thermo.tsv").write_text("\n".join(rows) + "\n")
    r = a.run_summary(tmp_path / "run", package)
    assert math.isclose(r["rho"], 512 * 18.0154 * 1.66053906660e-3 / 15.2, rel_tol=1e-9)
    assert r["pressure"] == 3.0 and "p_mol" not in r
