"""Cost and consistency of OpenMM's pressure tensor for Green-Kubo viscosity (T4, step 0).

OpenMM 8.5 has no virial. MonteCarloFlexibleBarostat.computeCurrentPressure gives the six
components of the pressure tensor as finite-difference derivatives of the energy with respect to
the box matrix (atomic virial if scaleMoleculesAsRigid is false). This script measures, on one
package and one platform/precision:

- wall time per MD step (1 fs Langevin, only to warm up and to have a moving configuration);
- wall time per call of the flexible barostat's tensor (atomic and molecular) and of the scalar
  MonteCarloBarostat pressure the bridge uses now;
- whether the tensor is reproducible on the same state, and its trace / 3 against the scalar.

Measurement only: it changes no bridge code and writes no run output. Units: bar, ms, nm.

    python bench_tensor.py RUN_TOML PACKAGE --platform HIP --precision mixed --out OUT.json
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("run_toml", type=Path, help="run.toml whose [[providers]] block is used")
    ap.add_argument("package", type=Path, help="system package (.ucsys)")
    ap.add_argument("--platform", default="HIP")
    ap.add_argument("--precision", default="mixed")
    ap.add_argument("--temperature-K", type=float, default=298.15)
    ap.add_argument("--warmup-steps", type=int, default=2000)
    ap.add_argument("--timed-steps", type=int, default=2000)
    ap.add_argument("--calls", type=int, default=20)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()

    import openmm as mm
    from openmm import unit
    from ucmd_bridge.model import NonbondedSettings, build_system
    from ucmd_bridge.openmm_backend import read_plan
    from ucmd_bridge.package import load

    plan = read_plan(a.run_toml)
    top = load(a.package)
    system, _ = build_system(top, NonbondedSettings.from_provider(plan.provider))
    t = a.temperature_K
    flex_atomic = mm.MonteCarloFlexibleBarostat(1.0, t, 0, False)
    flex_rigid = mm.MonteCarloFlexibleBarostat(1.0, t, 0, True)
    scalar = mm.MonteCarloBarostat(1.0, t, 0)
    for f in (flex_atomic, flex_rigid, scalar):
        system.addForce(f)
    integ = mm.LangevinMiddleIntegrator(t, 1.0, 0.001)
    integ.setRandomNumberSeed(20261127)
    platform = mm.Platform.getPlatformByName(a.platform)
    props = {"Precision": a.precision} if a.platform in ("OpenCL", "CUDA", "HIP") else {}
    ctx = mm.Context(system, integ, platform, props)
    ctx.setPeriodicBoxVectors(*[mm.Vec3(*row) for row in top.cell_nm])
    ctx.setPositions([mm.Vec3(*p) for p in top.positions_nm])
    ctx.setVelocitiesToTemperature(t, 20261127)

    integ.step(a.warmup_steps)
    ctx.getState(getEnergy=True)  # sync
    t0 = time.perf_counter()
    integ.step(a.timed_steps)
    ctx.getState(getEnergy=True)
    ms_step = (time.perf_counter() - t0) * 1e3 / a.timed_steps

    def per_call(fn):
        times, values = [], []
        for _ in range(a.calls):
            t0 = time.perf_counter()
            v = fn(ctx)
            times.append((time.perf_counter() - t0) * 1e3)
            values.append(v)
        return times, values

    bar = unit.bar
    to_bar = lambda q: [float(x.value_in_unit(bar)) for x in q]
    ta, va = per_call(lambda c: to_bar(flex_atomic.computeCurrentPressure(c)))
    tr, vr = per_call(lambda c: to_bar(flex_rigid.computeCurrentPressure(c)))
    ts, vs = per_call(lambda c: float(scalar.computeCurrentPressure(c).value_in_unit(bar)))
    spread = max(max(abs(x - y) for x, y in zip(v, va[0])) for v in va)
    result = {
        "openmm": mm.__version__,
        "platform": a.platform,
        "precision": a.precision,
        "package": str(a.package),
        "n_atoms": top.n_atoms,
        "ms_per_step_1fs": ms_step,
        "ms_per_tensor_atomic": {"median": statistics.median(ta), "max": max(ta)},
        "ms_per_tensor_rigid": {"median": statistics.median(tr), "max": max(tr)},
        "ms_per_scalar_molecular": {"median": statistics.median(ts), "max": max(ts)},
        "tensor_atomic_bar": va[0],
        "tensor_rigid_bar": vr[0],
        "scalar_molecular_bar": vs[0],
        "trace_over_3_atomic_bar": sum(va[0][:3]) / 3,
        "trace_over_3_rigid_bar": sum(vr[0][:3]) / 3,
        "repeat_spread_atomic_bar": spread,
        "order": "XX YY ZZ XY XZ YZ",
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps(result, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
