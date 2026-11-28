# V-3: thermodynamic consistency — integrator, or thermostat/barostat coupling?

- **Label:** confirmatory. Predictions (this file, `predict.py`, `prediction.json`) are committed before any V-3 run and
  before the result of SC-3's water arms (`studies/2026-11-25_water-npt-cpu-molecular`, job baf5) was read.
- **Owner:** agent "consistency" (task V-3, `docs/tasks.toml`), under the author's delegation of 2026-11-28.
- The full protocol, analysis and criteria follow in this README before the first V-3 run.

## Prediction for SC-3's three water arms (written 2026-11-28, before their result was read)

All three arms run SPC/Fw at 1 fs with the same Nosé–Hoover chain (τ 0.1 ps) and target. From `prediction.json`
(`predict.py`; inputs: the half-step temperature of SC-1's water frames, 9.09 K at 1 fs, and κ_T = 4.48·10⁻⁵ bar⁻¹ from
the volume fluctuations of the GPU water runs), counting **only the pressure each barostat holds**:

| Arm | barostat holds | true pressure − P₀ | ρ against CPU molecular |
|---|---|---|---|
| CPU, C-rescale, molecular (engine main) | molecular pressure, centre-of-mass kinetic energy (at T*) | ≈ 0 | — |
| CPU, C-rescale, atomic | on-step atomic pressure | +126.6 bar | **+0.57 %** |
| GPU, MonteCarloBarostat | accepts with the target T₀ while the slow modes are at T* = T₀ + 6.06 K | +28.1 bar | **+0.13 %** |

First order in κ_T. Other differences between the backends (precision, PME, tail) are not in these numbers. If the
GPU − CPU-molecular difference is near zero instead of +0.13 %, the MC-barostat term is wrong; if CPU-atomic − CPU-molecular
is far from +0.57 %, the estimator argument of SC-3 is incomplete.

## The parameter-free check on SC-1 (existing data, no fit)

With T* − T_on = (2/3)·ΔT_half (README "Why", to follow) and the model's own thermal expansion and compressibility,
`predict.py` gives ρ(0.5 fs) − ρ(1 fs) = **+0.233 %** for the 1 M box (SC-1 measured +0.227 ± 0.039 %) and **+0.314 %** for
pure EMC (measured +0.308 ± 0.030 %). Water needs SPC/Fw's thermal expansion, which no run of ours has measured.
