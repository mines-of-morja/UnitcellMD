# V-3: thermodynamic consistency — integrator, or thermostat/barostat coupling?

- **Label:** confirmatory. Predictions (this file, `predict.py`, `prediction.json`), protocol, `analyze.py` and its tests are
  committed before any V-3 run. The SC-3 water prediction below was committed (9b22a5d) before baf5's result was read.
- **Owner:** agent "consistency" (task V-3, `docs/tasks.toml`), under the author's delegation of 2026-11-28.
- **Question:** configurational minus kinetic temperature is +3.7 ± 0.5 K at 1 fs and +1.7 ± 0.9 K at 0.5 fs in the 1 M box
  (SC-1). Is that the integrator, or do the thermostat and the barostat interfere (the author, 2026-11-28)? Which part of the
  offset is which, with errors, and what is the one bias row for the summary (Jo, section 2)?

## Why (the derivation the criteria test)

1. Velocity Verlet samples, to O(Δt²), the Boltzmann distribution of its shadow Hamiltonian
   H̃ = H + Δt² [ p·M⁻¹U″M⁻¹p/12 − U′·M⁻¹U′/24 ] (backward error analysis of the Strang splitting). Integrating the
   Gaussian momenta of H̃ at temperature T* and using ⟨∇²U⟩ = β⟨|∇U|²⟩ gives, exactly at this order,
   **T_on = T* − (2/3)·ΔT_half**, with ΔT_half = Δt²⟨Σ F²/(4m)⟩/(N_dof k) the half-step minus on-step kinetic temperature.
   The slow degrees of freedom (molecule centres, rotations; ωΔt ≪ 1) are at T*. Fast modes show an on-step kinetic
   temperature below T* and a half-step one above (T* + ΔT_half/3).
2. **Nosé–Hoover chain** (engine and bridge, `integrators.py`): it pins the **on-step** kinetic energy, T_on = T₀. So the slow
   modes run at **T* = T₀ + (2/3)·ΔT_half**, whatever τ is. The coupling strength sets how fast, not where. **NVE** has the
   same offset between T* and T_on, with T* set by the energy.
3. **Langevin BAOAB** (bridge, `integrators.py`): the O step acts between the two half drifts; for harmonic modes the
   configurations are sampled exactly at T₀ and the on-step momenta at T₀(1 − ω²Δt²/4). So **T* = T₀ and T_on = T₀ − ΔT_half**.
   Already seen, not pre-registered: the gas-phase EMC of SC-7 step 0 (BAOAB, 1 fs) reads 292.4 K against 298.15 K, i.e.
   −5.75 K; the liquid's ΔT_half is 6.04 K.
4. **MonteCarloBarostat** (GPU; OpenMM 8.6.1 does not scale velocities, checked): it accepts with the target T₀. With the slow
   modes at T*, its balance ⟨P_conf⟩ + ρ_mol k T₀ = P₀ holds the true pressure at **P₀ + ρ_mol k (T* − T₀)**: +3.8 bar in the
   1 M box at 1 fs, +28 bar in water. **C-rescale with the molecular pressure** (engine main) uses the centre-of-mass kinetic
   energy, which is at T*: no such term. **C-rescale with the atomic on-step pressure** (engine before SC-3 B) holds a pressure
   that is low by N_dof k ΔT_half/(3V) (SC-3: −127 predicted, −129 ± 9 bar measured in water).
5. **Density** follows: ρ(1 fs) − ρ(Δt→0) = −α·(2/3)ΔT_half + κ_T·ρ_mol k (2/3)ΔT_half. With SC-1's own ΔT_half (5.39 K, from
   forces, ±0.01 K) and the model's α and κ_T this predicts the measured 1 → 0.5 fs shifts without a free parameter (below).

So the expectation is: **integrator only; the thermostat converts the integrator's on-step bias into a real temperature
error of the slow modes; the coupling strength plays no role.** The runs test each step of that chain.

## Runs (arms.py; 1 M M1 box, 7036 atoms, 20 °C)

- **Start:** the end of SC-1's three 1 fs NPT runs (`base_s1..3` of `2026-11-24_parameter-sensitivity-1M`, 5 ns), last frame
  scaled to the mean volume of its last 500 ps (`tools/study/package_from_run.py` → `packages/end1fs_sK.ucsys`, not in git).
  Fresh Maxwell–Boltzmann velocities at 293.15 K.
- **Same as production** (scan, SC-1): force field, cut-off 1.4 nm, PME 10⁻⁵, tail correction, COM removal every 0.1 ps.
  Every interval is the same in time: thermo 0.1 ps, trajectory 1 ps (positions, **velocities and forces**), checkpoint 100 ps.
- **Engine:** worktree `ucmd-engine-consist`, branch `v3-consistency` = ucmd-engine `main` 36b2837 (velocities in the
  trajectory, molecular C-rescale), release `ucmd` and the bridge in the HIP image `ucmd-openmm:gfx906-hip`. Mixed precision
  except NVE (double: the bridge refuses mixed precision without a thermostat, ADR 0012).

| Arm | job | thermostat | step | length | tests |
|---|---|---|---|---|---|
| `nhc-tau0p1` | A | NHC τ 0.1 ps (production) | 1 fs | 1.1 ns | reference |
| `nhc-tau1` | A | NHC τ 1 ps (10× weaker) | 1 fs | 1.1 ns | C2 |
| `nhc-tau0p025` | A | NHC τ 0.025 ps (4× stronger) | 1 fs | 1.1 ns | C2 |
| `nhc-tau0p1-0p5fs` | A | NHC τ 0.1 ps | 0.5 fs | 1.1 ns | C4 |
| `baoab-g1` | B | Langevin BAOAB γ 1 ps⁻¹ | 1 fs | 1.1 ns | C3 |
| `baoab-g0p1` | B | Langevin BAOAB γ 0.1 ps⁻¹ | 1 fs | 1.1 ns | C3 |
| `nhc-shift` | B | NHC τ 0.1 ps, target 289.554 K = T₀ − (2/3)ΔT_half | 1 fs | 1.1 ns | C5 |
| `nve-1fs` | C | none (NVE, double) | 1 fs | 1.1 ns | C1, drift |
| `nve-0p5fs` | C | none (NVE, double) | 0.5 fs | 0.6 ns | C1, drift |
| `baoab-g1-npt-s1..3` | D | BAOAB γ 1 ps⁻¹ + MonteCarloBarostat every 25 fs | 1 fs | 2.5 ns each | C6 |
| `xh-nhc-1fs`, `xh-nhc-2fs` | X | NHC τ 0.1 ps, **X–H bonds constrained (model change)** | 1, 2 fs | 1.1 ns | reported only |

- The target shift of `nhc-shift` is fixed from SC-1 data before any run (`prediction.json`, 289.554 K).
- Arm X needs packages with X–H constraints from the builder (ucmd-builder branch `v3-xh-constraints`); it is an
  exploratory **model change**: Lehnert 2025 used none, and the author decides any use.
- **Cost** (105 ns/day at 1 fs mixed, SC-1; double assumed 3× slower): A ≈ 1.5 h, B ≈ 1 h, C ≈ 1.5 h, D ≈ 1.9 h, X ≈ 0.5 h.
  Queue: one command job per letter, `--needs gpu-hip-mixed` (C: `gpu-hip-double`), priority 2, `run.py JOB`.

## Analysis (analyze.py, tested in test_analyze.py)

- Frames after 100 ps (500 ps for the NPT density). Per frame: T_on (all atoms, on-step, COM removed, N_dof = 3N − 3 − N_c),
  T_com (molecule centres, 3N_mol − 3), ΔT_half from the stored forces, P_atomic − P_molecular = [2K_int + Σ(r_i − R_I)·F_i]/(3V)
  and its prediction −Δt²[Σ F_i²/(4m_i) − Σ F_I²/(4M_I)]/(3V). Errors: SE of the mean from 10 contiguous blocks; per-frame
  differences are averaged as pairs. NVE drift: slope of the conserved energy as 2(dE/dt)/(N_dof k) in K/ns.
- T_com from velocities replaces the configurational temperature of SC-1 as the main observable (error ≈ 0.3 K per arm against
  ≈ 1.3 K). `docs/research/water-pressure/tconf.py` on 200 frames of `nhc-tau0p1` and `baoab-g1` is computed as a cross-check,
  not judged.
- Constrained arms: the stored forces are the providers'; ΔT_half adds an approximate constraint force (each constraint
  cancels its pair's relative acceleration along the bond). Their numbers are reported, not judged.

## Criteria (fixed before the runs; "within" = within 2 SE)

- **C1, integrator (NVE):** T_com − T_on equals (2/3)ΔT_half of the same frames, and is resolved (> 2 SE), at 1 fs; at 0.5 fs
  within 2 SE. Prediction: +3.60 K at 1 fs, +0.88 K at 0.5 fs.
- **C2, coupling strength:** for each NHC arm T_com − T_on − (2/3)ΔT_half = 0; τ 0.025 and 1 ps against 0.1 ps within 2 SE or
  0.5 K. **Coupling part** = the inverse-variance mean of that residual over the three 1 fs NHC arms.
- **C3, temperature definition (BAOAB):** T_com = T₀ and T_on = T₀ − ΔT_half (prediction 287.76 K), both γ.
- **C4, step:** NHC at 0.5 fs, T_com − T_on = (2/3)ΔT_half (prediction +0.88 K).
- **C5, shifted target:** `nhc-shift` T_com = 293.15 K.
- **C6, density:** BAOAB NPT (3 starts) against SC-1's 1 fs NHC mean (1.19428 g/cm³) and its Δt → 0 extrapolation
  ρ(0.5) + [ρ(0.5) − ρ(1)]/3 (SE propagated). "BAOAB changes the density" if above the 1 fs mean by > 2 SE; "BAOAB gives the
  Δt → 0 density" if within 2 SE of the extrapolation. Prediction: +0.31 % over 1 fs NHC.
- **P, pressure:** P_atomic − P_molecular equals its prediction, per arm and pooled over the unconstrained 1 fs arms
  (prediction −66.7 bar at 1 fs, −16.3 bar at 0.5 fs).
- **Reading:** C1 and C2 pass → the offset is the integrator's, and no part is the coupling: one bias row. C1 passes and
  C2 fails by more than 0.5 K → the coupling part is stated with its error and both rows stay. C3 and C6 decide whether
  statics may run at 1 fs with BAOAB; C5 whether transport may run at 1 fs with the shifted target. No run is added or
  dropped after looking; a hung run continues from its checkpoint (`run.py`).

## Running it

    python3 tools/queue/ucmd_queue.py submit command --needs gpu-hip-mixed --priority 2 --as agent-consistency \
        --title "V-3 job A" -- python3 studies/2026-11-28_v3-thermo-consistency/run.py A        (B, D, X likewise)
    python3 tools/queue/ucmd_queue.py submit command --needs gpu-hip-double --priority 2 --as agent-consistency \
        --title "V-3 job C (NVE)" -- python3 studies/2026-11-28_v3-thermo-consistency/run.py C
    HDF5_USE_FILE_LOCKING=FALSE ucmd-analysis/.venv/bin/python studies/2026-11-28_v3-thermo-consistency/analyze.py \
        studies/2026-11-28_v3-thermo-consistency/result.json

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
