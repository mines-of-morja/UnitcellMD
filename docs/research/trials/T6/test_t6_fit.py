"""Amendment 5 of trial T6: energy weights and the counterpoise check of stage 2.

tools/oracle/.venv/bin/python -m pytest docs/research/trials/T6/test_t6_fit.py
"""

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t6_fit

RESULTS = t6_fit.ROOT / "tools/qm/results"
K = t6_fit.KJMOL_PER_HARTREE / t6_fit.KCAL_IN_KJ  # kcal/mol per hartree


def rows(bsse: dict[int, float | None], exchange: float = -2.0) -> list[dict]:
    """Synthetic clusters (no real cluster result) with ΔE_n = n · exchange without counterpoise."""
    alone = {"EC": -342.0, "EMC": -381.0}
    out = []
    for n, b in bsse.items():
        names = ["EC"] * n + ["EMC"] * (4 - n)
        e = sum(alone[s] for s in names) - 7.4 + n * exchange / K
        out.append(
            {
                "solvents": names,
                "e_complex_hartree": e,
                "e_bind_kcalmol": -100.0,
                "e_bind_cp_kcalmol": None if b is None else -100.0 + b,
                "solvent_alone": [
                    {"name": s, "e_alone_hartree": alone[s], "xyz_alone": []} for s in names
                ],
            }
        )
    return out


def test_s_x_is_the_rms_of_the_ec_minus_emc_errors():
    dimers = json.loads((RESULTS / "t6_dimers_wb97m-v_sp.json").read_text())
    s_d, s_x, err = t6_fit.uncertainties(dimers)
    ec, emc = err["m0_EC.xyz"], err["m0_EMC.xyz"]
    d = [ec["e_bind"] - emc["e_bind"], ec["e_int_cp"] - emc["e_int_cp"]]
    assert s_x == pytest.approx(((d[0] ** 2 + d[1] ** 2) / 2) ** 0.5)
    assert s_x == pytest.approx(0.962, abs=0.002)
    assert s_d == pytest.approx(0.0156, abs=1e-4)


def test_energy_residual_is_divided_by_n_s_x():
    ff = {"li_o_angstrom": {}, "delta_e_kcalmol": {1: -1.0, 4: -4.0}}
    r = t6_fit.residuals(ff, {}, {1: -2.0, 4: -8.0}, 0.01, 0.5, energies=True)
    assert r == pytest.approx([2.0, 2.0])


def test_small_cp_shift_gives_delta_e_without_counterpoise():
    _, de, _, check = t6_fit.dft_targets(rows({0: 0.4, 1: None, 2: None, 3: None, 4: 0.6}), 0.96)
    assert not check["cp_used"]
    assert check["shift_kcalmol_per_exchange"] == pytest.approx(0.05)
    assert de == pytest.approx({n: -2.0 * n for n in (1, 2, 3, 4)}, abs=1e-6)


def test_large_cp_shift_needs_counterpoise_everywhere():
    with pytest.raises(SystemExit, match=r"n = \[1, 2, 3\]"):
        t6_fit.dft_targets(rows({0: 0.0, 1: None, 2: None, 3: None, 4: 4.0}), 0.96)


def test_large_cp_shift_uses_counterpoise_when_all_have_it():
    _, de, _, check = t6_fit.dft_targets(rows({n: 1.0 * n for n in range(5)}), 0.96)
    assert check["cp_used"]
    assert de == pytest.approx({n: -1.0 * n for n in (1, 2, 3, 4)}, abs=1e-6)


@pytest.mark.parametrize("bsse", [{0: None, 4: 0.1}, {0: 0.1, 4: None}])
def test_end_members_without_counterpoise_are_refused(bsse):
    with pytest.raises(SystemExit, match="n = 0 and n = 4"):
        t6_fit.dft_targets(rows({1: None, **bsse}), 0.96)
