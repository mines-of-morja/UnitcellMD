# SC-4: density of model M1 over concentration and temperature (go/no-go)

- **Label:** confirmatory (go/no-go). Plan, criterion and `analyze.py` (with tests) are committed before the first run.
- **Question:** does model M1 (T2: EC from Caleman 2012, EMC LigParGen, JJ06 Li⁺, CL&P PF₆⁻, ζ = 0.75) give the measured density
  of LiPF₆ in EC:EMC 3:7 (w:w) across concentration and temperature, or only at 1 M, 20 °C? A slope against c points to the ion
  model, a common offset to the solvent.
- **Requested by:** task SC-4. The author confirmed the grid and the 1.5 % limit on 2026-11-25, and on 2026-11-27 asked to submit
  the required runs overnight.

## Points

| Point | Folder | Box |
|---|---|---|
| 0.1, 2 and 3 M, 20 °C | this one | counts of Lehnert 2025 SI Table S1 (`ucmd-builder/examples/EC/boxes.csv`): 13392, 7484, 8004 atoms; M1 force field as T2 |
| 1 M, 10 and 50 °C | `2026-11-27_density-temperature-M1` | minimized package `base_s1` of the 1 M scan (7036 atoms) |
| 1 M, 20 °C | the three 0.5 fs runs of SC-1 (`2026-11-25_timestep-1M-0p5fs`) | the same packages; 5 ns, first 1.5 ns skipped |

One run per new point. The spread between seeds at 1 M is 0.045 % (SC-1, three seeds), small against the 1.5 % limit and the
reference's ±0.6 %.

## Protocol and why this length (trials rule 6)

- **0.5 fs** (SC-1: the 1 fs step reads the density 0.2–0.3 % low). The author still has to choose between 0.5 fs and a
  multiple time step. A multiple time step does not exist yet, and its goal is the small-step result, so these runs stay valid
  under either choice.
- Everything else is SC-1's 1 M protocol: NPT 1 atm, Nosé–Hoover τ 0.1 ps, C-rescale (on the GPU the Monte Carlo barostat),
  1.4 nm, PME 10⁻⁵, LJ tail, HIP mixed, `ucmd` 2ea7e82 and bridge c2cc427. Every interval is the same in time.
- **3 ns, the first 1 ns skipped.** Measured settling at 0.5 fs, from the minimized start: the density is within 0.1 % of its final
  value after 0.25–0.5 ns, in all three 1 M runs and all three EMC runs (250 ps windows). 1 ns is twice the slowest of these, a
  margin for 3 M and 10 °C, which relax more slowly. 2 ns analysed gives a statistical error far below 1.5 %.
- **Cost:** about 8.5 h of GPU (0.1 M about 2.6 h, the others about 1.4–1.5 h each).

## Criteria, fixed before the runs

The reference is the fit of Landesfeind & Gasteiger 2019 (SI Eq. S1, Table S1): ρ = 1.41 + 0.0912 c − 0.00109 T (g/cm³, mol/L,
K), read twice (SC-8), good to about ±0.6 %, stated for 0–50 °C and 0.1–3 M with data at 10–50 °C and 0–3 M. It is evaluated at
the **box's own concentration**: LiPF₆ pairs / (N_A · mean volume).

1. **Each point:** pass if the density is within **1.5 %** of the fit (the task's acceptance line: "within 1.5 % at every point,
   and the fitted d(rho)/dc reported against 0.0912 g/cm3 per M"). Otherwise FAIL.
2. **Overall:** go if every point passes; no-go if any point fails.
3. **Settling check:** a point whose two halves of the analysed window differ by more than 0.3 % is *not settled*. It is not
   judged, and the overall verdict is then *unresolved*. No run is extended after looking.
4. **Reported, not judged:** dρ/dc from the four 20 °C points (least squares) against 0.0912 g/cm³ per M, and dρ/dT from the three
   1 M points against −0.00109 g/cm³ per K, each with its SE from the residuals.

**Prediction (task SC-4, ideal mixing of the model's pure solvents; an extrapolation):** about +2.2 % at 0.1 M, falling to −0.8 %
at 3 M at 1 fs. SC-1 adds about +0.25 % at 0.5 fs, so **0.1 M is expected to fail** (about +2.4 %) and 3 M to pass (about −0.5 %).

**Already seen:** the 1 M, 20 °C point, +1.33 % (1.1970 against 1.1813 g/cm³ at c = 0.996 M). The new points have not been run.

## Running it

    submit study 2026-11-27_density-concentration-M1 --needs gpu-hip-mixed
    submit study 2026-11-27_density-temperature-M1 --needs gpu-hip-mixed

Then `python3 analyze.py OUT.json`.
