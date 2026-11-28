"""Tests of the V-2 analysis on made-up data (written before the runs). Needs numpy and h5py (ucmd-analysis venv)."""

import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import pytest

spec = importlib.util.spec_from_file_location("v2", Path(__file__).with_name("analyze.py"))
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)

KT = a.c.BOLTZMANN_J_PER_K * a.T_K


def yh_slope(eta_pa_s: float) -> float:
    """S = xi k_B T / (6 pi eta) in m2/s nm."""
    return a.c.YEH_HUMMER_XI_CUBIC * KT / (6 * math.pi * eta_pa_s) / a.c.NM_IN_M


def test_jo_numbers_for_the_1x_box():
    # feedback section 1: Delta D = 1.42e-13 m2/s / eta[Pa s] at L = 4.28 nm
    assert yh_slope(1.0) / 4.28 == pytest.approx(1.42e-13, rel=0.005)
    # T2 M1 kappa_NE 0.50 -> 0.65 S/m at eta = 7 mPa s (c = 0.994 mol/L)
    n = 0.994 * 1e3 * a.c.AVOGADRO_PER_MOL
    dd = yh_slope(7e-3) / 4.28
    assert 0.50 + a.kappa_ne(n, dd, dd) == pytest.approx(0.65, abs=0.006)


def test_eta_from_slope_inverts_and_brackets():
    e = a.eta_from_slope(yh_slope(5e-3), 0.1 * yh_slope(5e-3))
    assert e["eta_mPa_s"] == pytest.approx(5.0)
    assert e["eta_low_mPa_s"] == pytest.approx(5.0 / 1.2) and e["eta_high_mPa_s"] == pytest.approx(5.0 / 0.8)
    assert e["resolved"] and e["rel_se"] == pytest.approx(0.1)
    e = a.eta_from_slope(yh_slope(5e-3), 0.6 * yh_slope(5e-3))
    assert not e["resolved"] and e["eta_high_mPa_s"] == math.inf


def test_slope_and_beta_on_exact_curves():
    lags = np.arange(0, 5000, 4.0)
    assert a.slope(lags, 3.0 * lags + 2.0, (500, 2500)) == pytest.approx(3.0)
    assert a.beta(lags[1:], 0.7 * lags[1:] ** 0.8, (500, 2500)) == pytest.approx(0.8, rel=1e-3)
    with pytest.raises(ValueError):
        a.slope(lags, lags, (1.0, 2.0))


def brownian(rng, frames, n, d_nm2_ps, dt):
    steps = rng.normal(0.0, math.sqrt(2 * d_nm2_ps * dt), size=(frames, n, 3))
    return np.cumsum(steps, axis=0)


def test_diffusion_and_collective_kappa_of_independent_walkers():
    rng = np.random.default_rng(7)
    dt, frames = 4.0, 1500
    d_cat, d_an = 5e-5, 8e-5  # nm2/ps = 5e-11, 8e-11 m2/s
    cat, an = brownian(rng, frames, 400, d_cat, dt), brownian(rng, frames, 400, d_an, dt)
    assert a.diffusion(cat, dt, (100, 1000)) == pytest.approx(5e-11, rel=0.05)
    assert a.diffusion(an, dt, (100, 1000)) == pytest.approx(8e-11, rel=0.05)
    vol = 400 / 6.0  # nm3
    kb = a.kappa_blocks(cat, an, dt, vol)
    kne = a.kappa_ne(400 / (vol * 1e-27), 5e-11, 8e-11)
    assert kb["kappa_NE"] == pytest.approx(kne, rel=0.05)
    assert kb["D_cat"] == pytest.approx(5e-11, rel=0.05) and kb["D_an"] == pytest.approx(8e-11, rel=0.05)
    # uncorrelated ions: kappa = kappa_NE (one collective coordinate, so a loose tolerance)
    assert kb["kappa"] == pytest.approx(kne, rel=0.35)


def synthetic_runs(s_true, a_true, sizes=((7036, 3), (14072, 2), (56288, 2)), noise=0.0, seed=1):
    rng = np.random.default_rng(seed)
    runs = []
    for n_atoms, seeds in sizes:
        L = 4.2825 * (n_atoms / 7036) ** (1 / 3)
        for _ in range(seeds):
            r = {"n_atoms": n_atoms, "L_nm": L, "pairs_per_m3": 6e26, "kappa": 0.4 + 0.1 / L,
                 "kappa_NE_blocks": 0.8 - a.kappa_ne(6e26, s_true / L, s_true / L)}
            for n, A in a_true.items():
                r[f"D_{n}"] = (A - s_true / L) * (1 + noise * rng.normal() * math.sqrt(7036 / n_atoms))
            runs.append(r)
    return runs


A_TRUE = {"Li": 7.4e-11, "PF6": 10.4e-11, "EC": 16.1e-11, "EMC": 12.1e-11}


def test_joint_fit_recovers_exact_data_and_jackknife_is_zero():
    s = yh_slope(5e-3)
    runs = synthetic_runs(s, A_TRUE)
    f = a.joint_fit(runs)
    assert f["S"] == pytest.approx(s, rel=1e-9)
    for n, A in A_TRUE.items():
        assert f["A"][n] == pytest.approx(A, rel=1e-9) and f["S_own"][n] == pytest.approx(s, rel=1e-9)
    est, se = a.jackknife(runs, a.flat_estimates)
    assert est["S"] == pytest.approx(s, rel=1e-9) and se["S"] == pytest.approx(0.0, abs=1e-9 * s)
    assert est["kappa_intercept"] == pytest.approx(0.4) and est["kappa_slope"] == pytest.approx(0.1)
    assert est["kappa_NE_inf"] == pytest.approx(a.kappa_ne(6e26, A_TRUE["Li"], A_TRUE["PF6"]))
    # kappa_NE of the blocks, corrected by 2 S / L, is the same at every size here
    assert est["kappa_NE_blocks_inf"] == pytest.approx(0.8)
    assert est["ratio_corrected"] == pytest.approx(est["kappa_mean"] / 0.8)


def test_joint_fit_with_noise_is_unbiased_and_its_jackknife_error_is_honest():
    s = yh_slope(5e-3)
    pulls = []
    for seed in range(200):
        est, se = a.jackknife(synthetic_runs(s, A_TRUE, noise=0.05, seed=seed), a.flat_estimates)
        pulls.append((est["S"] - s) / se["S"])
    pulls = np.array(pulls)
    assert abs(pulls.mean()) < 0.25  # no bias beyond a quarter SE
    assert 0.6 < pulls.std() < 1.6  # the jackknife SE is the right size (small-sample jackknife: loose)


def test_fit_refuses_a_single_size():
    runs = synthetic_runs(yh_slope(5e-3), A_TRUE, sizes=((7036, 3),))
    with pytest.raises(ValueError):
        a.joint_fit(runs)


def test_barycentric_coms_from_a_small_h5md_file(tmp_path):
    h5py = pytest.importorskip("h5py")
    doc = {"components": [{"molecule_type": "A", "count": 2}, {"molecule_type": "B", "count": 1}],
           "molecule_types": {"A": {"atoms": [{"mass_amu": 1.0}, {"mass_amu": 3.0}], "bonds": [{"atoms": [0, 1]}]},
                              "B": {"atoms": [{"mass_amu": 4.0}], "bonds": [], "formal_charge_e": 1}}}  # fmt: skip
    frames = 7
    rng = np.random.default_rng(3)
    x = rng.normal(size=(frames, 5, 3)).astype(np.float32)
    path = tmp_path / "t.h5"
    with h5py.File(path, "w") as fh:
        fh["parameters/ucmd/system_json"] = json.dumps(doc)
        fh["particles/all/position/value"] = x
        fh["particles/all/position/time"] = np.arange(frames) * 4.0
        fh["particles/all/position/step"] = np.arange(frames) * 4000
        fh["particles/all/box/edges/value"] = np.repeat((np.eye(3) * 2.0)[None], frames, axis=0)
    out = a.barycentric_coms(path, skip_ps=8.0, chunk=2)
    xd = x[2:].astype(np.float64)
    m = np.array([1.0, 3.0, 1.0, 3.0, 4.0])
    centre = (xd * m[None, :, None]).sum(axis=1) / m.sum()
    com_a0 = (xd[:, 0] * 1 + xd[:, 1] * 3) / 4 - centre
    assert out["coms"]["A"].shape == (5, 2, 3) and out["coms"]["B"].shape == (5, 1, 3)
    assert np.allclose(out["coms"]["A"][:, 0], com_a0) and np.allclose(out["coms"]["B"][:, 0], xd[:, 4] - centre)
    assert out["volume_nm3"] == pytest.approx(8.0) and out["counts"] == {"A": 2, "B": 1}
    # the barycentric frame: the mass-weighted sum of all centres is zero
    total = 4 * out["coms"]["A"].sum(axis=1) + 4 * out["coms"]["B"].sum(axis=1)
    assert np.allclose(total, 0.0, atol=1e-9)


def test_size_labels_and_per_size_table():
    runs = synthetic_runs(yh_slope(5e-3), A_TRUE)
    for r in runs:
        for n in a.SPECIES:
            r[f"D_{n}_check"] = r[f"D_{n}"]
        r["kappa_NE"] = 0.5
    t = a.per_size(runs)
    assert list(t) == ["1x", "2x", "8x"] and [t[k]["runs"] for k in t] == [3, 2, 2]
    assert t["8x"]["L_nm"] == pytest.approx(2 * 4.2825)
