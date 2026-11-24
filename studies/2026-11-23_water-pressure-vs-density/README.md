# 2026-11-23 — pressure against density for SPC/Fw water (NVT, GPU)

- **Label:** exploration.
- **Question:** the NPT runs of rung W settle at ρ = 1.0072 g/cm³ (CPU twin 1.0079, GPU twin 1.0089),
  0.5 % below Wu's 1.012. The NVT viscosity run at 1.012 g/cm³ and 300.2 K gave
  P = 26 ± 7 bar (10 blocks of 3.8 ns, `studies/2026-11-20_water-spcfw-viscosity-cpu`). With a
  compressibility near 4.5·10⁻⁵ per bar that pressure implies an NPT density of about 1.011, not
  1.007. **Is the engine's NPT density consistent with its own NVT pressure?**
- **Design:** three NVT runs of 512 SPC/Fw molecules at 298.16 K (the NPT temperature), 2 ns at
  1 fs, Nosé–Hoover chain τ = 1 ps, cutoff 0.9 nm, PME 10⁻⁶, tail correction, as rung W. GPU
  (HIP, double precision, bridge of `e25-constraints`). Pressure every 0.1 ps. First 0.5 ns
  skipped; errors from 5 blocks.

  | System (recipe) | ρ (g/cm³) | Meaning |
  |---|---|---|
  | `spcfw_512_rho1000` | 1.000 | below both |
  | `spcfw_512_rho10072` | 1.0072 | the NPT density found |
  | `spcfw_512_rho1012` | 1.012 | Wu's density |

- **Pass criteria, fixed before the runs:**
  1. **Consistent** if |P(1.0072) − 1.013| ≤ 30 bar (30 bar is 0.14 % in density at
     4.5·10⁻⁵ per bar) **and** the slope of P against ρ from the three points gives a
     compressibility between 3.5·10⁻⁵ and 6·10⁻⁵ per bar. Then the barostat and the pressure are
     sound and the 0.5 % gap to Wu belongs to the model or the setup (box size, PME, tail).
  2. **Inconsistent** if P(1.0072) lies outside ±30 bar. Then the NPT average and the NVT pressure
     disagree, which points to the barostat (C-rescale `every = 25`, compressibility input) or to
     the pressure estimate, and is the next thing to chase.
  3. Between the two (slope outside the range with P(1.0072) inside): reported as unresolved.
- **Comparison with the CPU:** P(1.012) here (GPU, bridge pressure) against 26 ± 7 bar (CPU engine
  virial, 300.2 K). A difference beyond the combined error means the two pressure estimates
  differ. The 2 K difference in temperature matters: with Wu's α = 4.98·10⁻⁴ K⁻¹ and
  κ_T = 4.5·10⁻⁵ atm⁻¹ for SPC/Fw the thermal pressure coefficient is about 11 bar/K, so P(1.012)
  at 298.16 K is expected near 26 − 22 ≈ 4 bar if the two estimates agree. That would put the
  equilibrium density at 1 atm and 298.16 K near 1.012, which makes the NPT result of 1.0072 an
  even larger discrepancy (about 100 bar).
- **Analysis:** `analyze.py` (mean pressure over 0.5–2 ns with 5 block errors, drift test, slope of P against ρ, verdict by the criteria above, refused if a run drifts); `python3 analyze.py runs analysis/results.json`.
- **Cost:** about 40 min of GPU per run at 72 ns/day, 2 h with hang padding.

## Notes

- **11:40Z first attempt failed in all three runs** (2.6, 3.6 and 5.1 ps): the bridge's identity
  tracker read positions every 0.1 ps and found a water molecule ambiguous (ratio 0.55–0.58 against
  the 0.5 limit). The limit was not loosened; the bridge now reads every 0.025 ps (0.01 ps in the
  first 5 ps), commit 0b92d8c of `e25-constraints`. All three runs restarted from the start or
  from their first checkpoint. Throughput with the new cadence: about 50 ns/day (CPU load 18).

## Result of the first scan (2026-11-23): the bridge's pressure drifted

All three runs finished (2 ns each, 51 ns/day, 0 failures, conformance with the engine 8.4·10⁻⁸ in
energy and 8.9·10⁻⁸ in forces, worst identity ratio 0.36, 1.88·10⁶ label corrections in rho1012).
Potential energy, temperature (298.2–298.3 K) and the conserved quantity are stationary.
**The pressure is not**: it rose linearly at fixed volume. The data are kept locally in
`logs/unfixed-bridge/`.

| Run | ρ (g/cm³) | P fit at 5 ps (bar) | drift (bar/ns) | mean 0.5–2 ns (bar) |
|---|---|---|---|---|
| rho1000 | 1.000 | 24 | 383 | 496 |
| rho10072 | 1.0072 | 144 | 489 | 740 |
| rho1012 | 1.012 | 242 | 445 | 793 |

(Linear fit over 5–2000 ps, 3200 pressure samples per run; sample scatter 610–620 bar.)

The pre-registered criteria were **not applied** to these numbers. Read literally, P(1.0072) =
740 bar would be criterion 2 ("inconsistent"); the pressure is an artefact, so that reading is void.
This departs from the rule fixed before the runs; the author may overrule it.

### Why the pressure drifted (found the same day)

The bridge took the pressure from `MonteCarloBarostat.computeCurrentPressure`, asked of the
**stepping** context. Experiments, all on the HIP/double bridge (scripts in
`ucmd-engine/validation/openmm-pressure/`):

1. Same final state of rho1012 (2000 ps): in-run value +454 bar; the checkpoint loaded into a fresh
   context, **−608 bar**; an energy-only calculation (scale the molecule centres by (1±10⁻³)^(1/3),
   difference the energy of a second context) **−610 bar**. The fresh value is the right one.
2. A real bridge run of 100 ps with a second, fresh context evaluated on the same state at every
   call: in-run minus fresh = +28, +68, +80, +79, +98 bar in the five 20 ps blocks; fresh minus
   energy-only 2, 2, 4, 24, −4 bar.
3. The calls on the stepping context also **relabelled identical molecules** (37 251 label
   corrections in 40 ps, 93 844 in 100 ps). A stepping loop with the same system but without the
   barostat calls: 0 exchanges in 40 000 steps. So the estimator call itself changes the
   stepping context's internal state, and the bias grows with the number of calls
   (4000 calls in 2 ns). The mechanism inside OpenMM is not identified.
4. A second, separate effect: two `computeCurrentPressure` calls in a row on the same context,
   with no state read in between, gave −1645.7 and +40 395 bar (OpenMM 8.5, HIP). The bridge
   always read the state first; the new probe does so itself.

**Fix** (bridge commit c2cc427): `PressureProbe` evaluates each state (positions, velocities, box
of the stepping context) in a second context that never steps. 40 ps check: last in-run 953.55 bar,
after a checkpoint reload 953.6 bar (before the fix: 696 against 565 bar).

**Consequences.** Pressure columns of all earlier GPU runs of the bridge in the thermo files are
biased upward, growing with run time (about 0.5 bar/ps for water at 1 fs); energies, temperature,
trajectories are not affected. The NPT densities should not be either (the density follows
OpenMM's own barostat moves, which do not use the estimator), but that is not shown; the CPU
engine's NPT agrees with the GPU's (1.0079 against 1.0089), which argues against it.
Which of those runs entered a result needs checking before they are cited: rung W (ΔH_vap, ε, D, η,
ρ do not use the pressure column), the electrolyte GPU runs (not yet looked at).

## Second scan (same design, bridge c2cc427): result

All three runs finished 2026-11-24 (2 ns, about 53 min each, `python3 analyze.py runs analysis/results.json`).
Mean T 298.09 / 297.97 / 298.31 K, potential energy drift below 5 kJ/mol/ns.

| Run | ρ (g/cm³) | P mean 0.5–2 ns (bar) | drift (bar/ns) |
|---|---|---|---|
| rho1000 | 1.000 | −122.4 ± 11.0 | −39 ± 20 |
| rho10072 | 1.0072 | **1.6 ± 21.8** | −34 ± 56 |
| rho1012 | 1.012 | 122.6 ± 11.9 | −5 ± 32 |

No run drifts significantly (first scan: +380 to +490 bar/ns). dP/dρ = 20 170 ± 770 bar/(g/cm³),
κ_T = 4.9·10⁻⁵ per bar. **Verdict by the pre-registered rule: criterion 1, consistent.**
P(1.0072) = 1.6 ± 22 bar is within 30 bar of 1 atm, and κ_T lies in 3.5–6·10⁻⁵. The engine's NPT
density (1.0072) is the density at which its own NVT pressure is 1 atm; the barostat and the
pressure estimate agree. The 0.5 % gap to Wu's 1.012 belongs to the model or the setup, not to
the barostat.

**Open, not resolved.** P(1.012) = 122.6 bar here against 26 ± 7 bar from the CPU engine's virial
at 300.2 K (expected about 4 bar at 298.16 K if both agreed). That is a difference of about
100 bar in the pressure of the same system at the same density. The CPU twin's NPT density
(1.0079) agrees with the GPU's, so the CPU's NVT run in `2026-11-20_water-spcfw-viscosity-cpu` is
the odd one out; what differs between it and these runs (thermostat, cutoff, PME, tail
correction, temperature) has not been compared yet. It does not change the verdict above.
