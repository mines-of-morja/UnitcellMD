"""Tests of analyze.py and arms.py (written before any V-3 run).

ucmd-analysis/.venv/bin/pytest studies/2026-11-28_v3-thermo-consistency
"""

from __future__ import annotations

import math
import sys
import tomllib
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import analyze as A
import arms


def test_block_se_matches_iid_error():
    rng = np.random.default_rng(1)
    x = rng.normal(3.0, 2.0, 100_000)
    mean, se = A.block_se(x)
    assert abs(mean - 3.0) < 4 * 2.0 / math.sqrt(len(x))
    assert se == pytest.approx(2.0 / math.sqrt(len(x)), rel=0.5)


def _dimers(n=50, seed=3):
    """n free dimers (masses 12 and 1) in a cubic box, some split by the boundary."""
    rng = np.random.default_rng(seed)
    L = 3.0
    m = np.tile([12.0, 1.0], n)
    mol = np.repeat(np.arange(n), 2)
    a = rng.uniform(0, L, (n, 3))
    bond = rng.normal(0, 1, (n, 3))
    bond *= 0.1 / np.linalg.norm(bond, axis=1)[:, None]
    x = np.empty((2 * n, 3))
    x[0::2], x[1::2] = a, (a + bond) % L  # the second atom wrapped into the box
    v = rng.normal(0, 1, (2 * n, 3)) / np.sqrt(m)[:, None]
    f = rng.normal(0, 50, (2 * n, 3))
    return x, v, f, np.full(3, L), m, mol, bond


def test_frame_stats_temperatures_and_pressure_by_hand():
    x, v, f, box, m, mol, bond = _dimers()
    n_mol, first = A.molecules(mol)
    s = A.frame_stats(x, v, f, box, m, mol, n_mol, first, dt_ps=1e-3)
    vs = v - (m[:, None] * v).sum(0) / m.sum()
    n_dof = 3 * len(m) - 3
    assert s["T_on"] == pytest.approx((m[:, None] * vs**2).sum() / (n_dof * A.K_B), rel=1e-12)
    M = m[0] + m[1]
    V = (m[0] * vs[0::2] + m[1] * vs[1::2]) / M
    assert s["T_com"] == pytest.approx((M * V**2).sum() / ((3 * n_mol - 3) * A.K_B), rel=1e-12)
    # internal virial with the true (unwrapped) bond vectors: r_i - R_I = -m_H/M b (atom 0), +m_C/M b (atom 1)
    w = ((-m[1] / M * bond) * f[0::2] + (m[0] / M * bond) * f[1::2]).sum()
    two_k_int = (m[:, None] * vs**2).sum() - (M * V**2).sum()
    vol = 27.0
    assert s["dP_atomic_minus_molecular_bar"] == pytest.approx((two_k_int + w) / (3 * vol) * A.BAR_PER_KJMOL_NM3,
                                                               rel=1e-10)  # fmt: skip
    F = f[0::2] + f[1::2]
    sa, sc = (f**2 / (4 * m[:, None])).sum(), (F**2 / (4 * M)).sum()
    assert s["dT_half"] == pytest.approx(1e-6 * sa / (n_dof * A.K_B), rel=1e-12)
    assert s["dP_predicted_bar"] == pytest.approx(-1e-6 * (sa - sc) / (3 * vol) * A.BAR_PER_KJMOL_NM3, rel=1e-12)


def test_constraint_forces_cancel_the_relative_acceleration_along_the_bond():
    x, _v, f, box, m, mol, bond = _dimers()
    xu = A.unwrap(x, box, mol, A.molecules(mol)[1])
    pairs = np.array([(2 * k, 2 * k + 1) for k in range(len(m) // 2)])
    g = A.constraint_forces(xu, f, m, pairs)
    a = (f + g) / m[:, None]
    u = bond / np.linalg.norm(bond, axis=1)[:, None]
    assert np.abs(((a[1::2] - a[0::2]) * u).sum(1)).max() < 1e-9
    assert np.abs(g[0::2] + g[1::2]).max() < 1e-12  # internal: no net force on the molecule


def test_baoab_harmonic_oscillators_on_step_temperature_low_by_dT_half():
    """The premise of criterion C3: BAOAB samples q at T0 (exact for harmonic modes) and its on-step kinetic
    temperature is T0 - dT_half, with dT_half computed exactly as analyze.py does (dt^2 sum F^2 / (4m) / (N k))."""
    rng = np.random.default_rng(7)
    n, kT, dt, gamma = 4000, 2.5, 0.01, 2.0
    omega = np.where(np.arange(n) % 2 == 0, 60.0, 2.0)  # fast (omega dt = 0.6) and slow modes, m = 1
    q = rng.normal(0, 1, n) * np.sqrt(kT) / omega
    p = rng.normal(0, np.sqrt(kT), n)
    c = math.exp(-gamma * dt)
    on, half, conf = [], [], []
    for step in range(6000):
        p -= 0.5 * dt * omega**2 * q
        q += 0.5 * dt * p
        p = c * p + math.sqrt((1 - c * c) * kT) * rng.normal(size=n)
        q += 0.5 * dt * p
        p -= 0.5 * dt * omega**2 * q
        if step >= 1000 and step % 5 == 0:
            f = -(omega**2) * q
            on.append((p * p).mean())
            half.append(dt**2 * (f * f / 4).mean())
            conf.append(((omega * q) ** 2)[1::2].mean())  # slow modes, configurational
    t_on, t_half = np.mean(on) / kT, np.mean(half) / kT
    assert t_half > 0.04  # a sizeable bias
    assert t_on == pytest.approx(1 - t_half, abs=0.004)
    assert np.mean(conf) / kT == pytest.approx(1.0, abs=0.01)


def test_drift_and_density():
    t = np.linspace(0, 1000, 101)
    n_dof = 21105
    e = 5.0 + 0.002 * t  # kJ/mol per ps
    assert A.drift_K_per_ns(t, e, n_dof) == pytest.approx(2 * 2.0 / (n_dof * A.K_B), rel=1e-9)
    # 7036 atoms of the 1 M box: 1.19426 g/cm3 at 78.5553 nm3 (prediction.json) -> total mass
    mass = 1.1942586498060181 * 78.55529497356294e-21 / A.G_PER_AMU
    assert A.density_g_cm3(mass, np.array([78.55529497356294]))[0] == pytest.approx(1.1942586498060181, rel=1e-12)


def test_constraint_pairs_in_canonical_order():
    system = {
        "components": [{"molecule_type": "A", "count": 2}, {"molecule_type": "B", "count": 1}],
        "molecule_types": {
            "A": {"atoms": [{}, {}, {}], "constraints": [{"atoms": [0, 2], "length_nm": 0.1}]},
            "B": {"atoms": [{}, {}]},
        },
    }
    assert A.constraint_pairs(system).tolist() == [[0, 2], [3, 5]]


def test_arms_write_valid_run_tomls():
    for arm in arms.ARMS:
        doc = tomllib.loads(arms.make_run_toml(arm))
        dt = doc["run"]["timestep_fs"]
        # intervals the same in time at every step
        assert doc["output"]["thermo"]["every"] * dt == pytest.approx(100.0)
        assert doc["output"]["checkpoint"]["every"] * dt == pytest.approx(100_000.0)
        assert doc["run"]["steps"] * dt == pytest.approx(1000 * arm.length_ps)
        assert ("thermostat" in doc) == (arm.thermostat is not None)
        assert ("barostat" in doc) == arm.barostat
        if arm.integrator == "langevin-baoab":
            assert doc["thermostat"]["kind"] == "langevin"
        if arm.trajectory_vectors:
            assert doc["output"]["trajectory"]["velocities"] and doc["output"]["trajectory"]["forces"]
            assert doc["output"]["trajectory"]["every"] * dt == pytest.approx(1000.0)
    assert len({a.name for a in arms.ARMS}) == len(arms.ARMS)
    assert len({a.seed for a in arms.ARMS}) == len(arms.ARMS)
    shifted = arms.by_name("nhc-shift").thermostat["temperature_K"]
    assert shifted == pytest.approx(289.554, abs=1e-3)  # prediction.json, fixed before the runs


PLUMB = Path(__import__("os").environ.get("V3_PLUMB_DIR", "/nonexistent"))


@pytest.mark.skipif(not (PLUMB / "nhc-tau0p1/out/trajectory.h5").exists(), reason="set V3_PLUMB_DIR to a plumbing run")
def test_reads_a_real_bridge_trajectory():
    r = A.analyze_arm(PLUMB / "nhc-tau0p1", skip_ps=0.0)
    assert r["frames"] >= 3 and r["n_dof"] == 21105
    assert 250 < r["T_on"][0] < 340 and 200 < r["T_com"][0] < 400
    assert 3.0 < r["dT_half"][0] < 8.0  # SC-1: 5.39 K at 1 fs
    assert -200 < r["dP_predicted_bar"][0] < -20
