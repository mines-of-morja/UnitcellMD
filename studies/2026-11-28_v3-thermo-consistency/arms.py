"""V-3 arms: every run of the study, as data (README "Runs"). Standard library only.

Each arm is one run.toml. `make_run_toml(arm)` writes it; `run.py` runs the arms through the queue.
All arms start from the end of SC-1's 1 fs NPT runs of the 1 M M1 box (packages/end1fs_sK.ucsys, made with
tools/study/package_from_run.py: last frame, scaled to the mean volume of the last 500 ps). Intervals are the
same in time at every step: thermo 0.1 ps, trajectory 1 ps (positions, velocities, forces), checkpoint 100 ps.
"""

from __future__ import annotations

from dataclasses import dataclass, field

T0_K = 293.15  # 20 C, the state point of SC-1 and T2
# T0 - (2/3) dT_half(1 fs) of the 1 M box, prediction.json "nhc_target_shift_T_set_K" (fixed before any run)
T_SET_SHIFTED_K = 289.554
P0_BAR = 1.01325


@dataclass(frozen=True)
class Arm:
    name: str
    job: str  # queue job that runs it (README "Jobs")
    package: str  # file name under packages/
    dt_fs: float
    length_ps: float
    thermostat: dict | None  # None: NVE
    integrator: str = "velocity-verlet"
    barostat: bool = False
    precision: str = "mixed"
    trajectory_vectors: bool = True  # velocities and forces in the trajectory
    seed: int = 0
    labels: dict = field(default_factory=dict)


def nhc(tau_ps: float, t_k: float = T0_K) -> dict:
    return {"kind": "nose-hoover-chain", "tau_ps": tau_ps, "chain_length": 3, "temperature_K": t_k}


def langevin(gamma_per_ps: float) -> dict:
    return {"kind": "langevin", "friction_per_ps": gamma_per_ps, "temperature_K": T0_K}


ARMS = [
    # job A: Nose-Hoover chain on the on-step kinetic energy, coupling strength and step
    Arm("nhc-tau0p1", "A", "end1fs_s1", 1.0, 1100.0, nhc(0.1), seed=1),  # production thermostat
    Arm("nhc-tau1", "A", "end1fs_s1", 1.0, 1100.0, nhc(1.0), seed=2),  # 10 x weaker
    Arm("nhc-tau0p025", "A", "end1fs_s1", 1.0, 1100.0, nhc(0.025), seed=3),  # 4 x stronger
    Arm("nhc-tau0p1-0p5fs", "A", "end1fs_s1", 0.5, 1100.0, nhc(0.1), seed=4),
    # job B: another definition of temperature (BAOAB), and the shifted target
    Arm("baoab-g1", "B", "end1fs_s1", 1.0, 1100.0, langevin(1.0), "langevin-baoab", seed=5),
    Arm("baoab-g0p1", "B", "end1fs_s1", 1.0, 1100.0, langevin(0.1), "langevin-baoab", seed=6),
    Arm("nhc-shift", "B", "end1fs_s1", 1.0, 1100.0, nhc(0.1, T_SET_SHIFTED_K), seed=7),
    # job C: no thermostat, no barostat (double precision: the bridge refuses mixed without a thermostat)
    Arm("nve-1fs", "C", "end1fs_s1", 1.0, 1100.0, None, precision="double", seed=8),
    Arm("nve-0p5fs", "C", "end1fs_s1", 0.5, 600.0, None, precision="double", seed=9),
    # job D: NPT density with BAOAB and the MC barostat, three starts (the SC-1 seeds' end states)
    *[
        Arm(
            f"baoab-g1-npt-s{k}",
            "D",
            f"end1fs_s{k}",
            1.0,
            2500.0,
            langevin(1.0),
            "langevin-baoab",
            barostat=True,
            trajectory_vectors=False,
            seed=9 + k,
        )
        for k in (1, 2, 3)
    ],
    # job X: exploratory model change, X-H bonds constrained (packages from ucmd-builder branch v3-xh-constraints)
    Arm("xh-nhc-1fs", "X", "end1fs_s1_xh", 1.0, 1100.0, nhc(0.1), seed=13, labels={"model": "X-H constrained"}),
    Arm("xh-nhc-2fs", "X", "end1fs_s1_xh", 2.0, 1100.0, nhc(0.1), seed=14, labels={"model": "X-H constrained"}),
]
STUDY_SEED = 20261128


def steps(arm: Arm, ps: float) -> int:
    n = ps * 1000.0 / arm.dt_fs
    if abs(n - round(n)) > 1e-9:
        raise ValueError(f"{arm.name}: {ps} ps is not a whole number of steps")
    return round(n)


def run_config(arm: Arm) -> dict:
    """The run.toml of one arm as a dict (README "Runs")."""
    doc: dict = {
        "spec_version": "0.1.0",
        "system": f"../../packages/{arm.package}.ucsys",
        "title": f"V-3 {arm.name}",
        "run": {
            "integrator": arm.integrator,
            "timestep_fs": arm.dt_fs,
            "steps": steps(arm, arm.length_ps),
            "seed": STUDY_SEED + 1000 * arm.seed,
        },
        "velocities": {"generate": "maxwell-boltzmann", "temperature_K": T0_K},
        "momentum": {"remove_com_every": steps(arm, 0.1)},
    }
    if arm.thermostat is not None:
        doc["thermostat"] = dict(arm.thermostat)
    if arm.barostat:
        doc["barostat"] = {"kind": "c-rescale", "pressure_bar": P0_BAR, "tau_ps": 1.0,
                           "compressibility_per_bar": 4.5e-5, "every": steps(arm, 0.025)}  # fmt: skip
    traj = {
        "file": "trajectory.h5",
        "every": steps(arm, 1.0 if arm.trajectory_vectors else 4.0),
        "precision": "float32",
    }
    if arm.trajectory_vectors:
        traj |= {"velocities": True, "forces": True}
    doc["output"] = {
        "directory": "out",
        "thermo": {"file": "thermo.tsv", "every": steps(arm, 0.1)},
        "trajectory": traj,
        "checkpoint": {"file": "checkpoint.ucchk", "every": steps(arm, 100.0)},
    }
    doc["providers"] = [{"kind": "force-field", "cutoff_nm": 1.4, "coulomb": "pme", "ewald_tolerance": 1e-5,
                         "dispersion_correction": True}]  # fmt: skip
    return doc


def _value(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return repr(v)
    if isinstance(v, str):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    raise TypeError(type(v))


def to_toml(doc: dict) -> str:
    """Scalars first, then [tables] (one level of nesting under [output]), then [[providers]]."""
    lines = [f"{k} = {_value(v)}" for k, v in doc.items() if not isinstance(v, (dict, list))]
    for k, v in doc.items():
        if isinstance(v, dict):
            lines += ["", f"[{k}]"] + [f"{a} = {_value(b)}" for a, b in v.items() if not isinstance(b, dict)]
            for a, b in v.items():
                if isinstance(b, dict):
                    lines += ["", f"[{k}.{a}]"] + [f"{c} = {_value(d)}" for c, d in b.items()]
    for k, v in doc.items():
        if isinstance(v, list):
            for item in v:
                lines += ["", f"[[{k}]]"] + [f"{a} = {_value(b)}" for a, b in item.items()]
    return "\n".join(lines) + "\n"


def make_run_toml(arm: Arm) -> str:
    return to_toml(run_config(arm))


def by_name(name: str) -> Arm:
    for arm in ARMS:
        if arm.name == name:
            return arm
    raise KeyError(name)
