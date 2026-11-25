# Sensitivity scan at 1 M: which parameters move the ions?

- **Question:** κ_NE of the current model (M1) is about 60 % of the experimental κ. Which
  parameter changes the ion mobility at all, and by how much?
- **Requested by** the author, 2026-11-24 (several parameters, about 5 ns, plot the trends); this
  design was approved the same day. **Written before any run.**
- **A map, not a fit.** The values are probes. No parameter is chosen from this study, and
  transport is not used to choose one (trials rule 2, strategy §2). Parameters come from density,
  viscosity, n_D or QM.

## Runs

The 1 M box of trial T2 (47 LiPF₆, 168 EC, 332 EMC, 7036 atoms), M1, 20 °C, NPT, 5 ns, T2 protocol.

| Knob | Baseline | Probes |
|---|---|---|
| `zeta`: ion charge scale, Li⁺ and PF₆⁻ | 0.75 | 0.65, 0.70, 0.80, 0.85 |
| `sigmaLi`: σ of Li⁺, all its LJ pairs (geometric rule) | ×1 | ×0.90, 0.95, 1.05, 1.10 |
| `epsEMC`: LJ ε of all EMC atom types | ×1 | ×0.85, 0.90, 0.95, 1.05 |

- Three baselines (packing seeds of T2) and one run per probe, 15 runs. All probes start from
  the minimized seed-1 package of T2 M1 (not minimized again); the velocities differ per run.
- `make_packages.py` writes the packages; the change is in each package's provenance.
- **Side effect of the geometric rule:** `epsEMC` also scales the EMC–other ε by the square root
  of the factor, and `sigmaLi` the Li–other σ likewise.
- **Engine and bridge:** `ucmd` 2ea7e82, bridge c2cc427 (pressure from a context that never
  steps), HIP mixed precision. T2 used engine c9098de and the bridge before that fix; the new baselines
  therefore stand on their own, and T2 is compared with them.

## Reading rule (fixed before the runs)

- The first 1.5 ns are skipped, the last 3.5 ns analysed (T2: the shell settles in 1–1.5 ns).
- **Noise:** the SD of ln y pooled over the two sets of three baselines (here and T2 M1). T2
  M1 gave about 10 % in κ_NE per run with 1 ns skipped and 5.5 % with 1.5 ns skipped (three seeds).
- **Trend per knob:** ln y = a + b ln x, least squares. A knob **moves transport** if κ_NE changes
  by at least 0.2 in ln over the scanned range and by at least 2 SE. Below that it is not resolved,
  which is not the same as no effect.
- **T6:** if `sigmaLi` moves transport, the held ωB97M-V cluster energies are run (after the
  author's decision on Amendment 5). If not, T6 becomes a side result. The author decides.
- **Not analysed:** full κ and t₊ (3.5 ns is too short: the 20 ns pilot had ±20 % in κ).
- **Already seen:** T2 results (κ_NE 0.447, 0.499, 0.543 S/m for the M1 seeds), κ_exp 0.84 S/m.

`analyze.py` computes it.

## Result (2026-11-25, all 15 runs; `analyze.py`, output `docs/research/summary_261125/data/scan.json`)

Every run finished at 5 ns, no molecule label corrections. One GPU hang (zeta_0.65, 1.14 ns) and several game pauses
were continued from checkpoints. Trend of κ_NE (ln κ_NE = a + b ln x), over the scanned range:

| Knob | exponent b | change of ln κ_NE | verdict by the reading rule |
|---|---|---|---|
| `zeta` | −3.6 ± 0.5 | −0.97 ± 0.14 | **moves** transport |
| `epsEMC` | −4.0 ± 0.6 | −0.84 ± 0.13 | **moves** transport |
| `sigmaLi` | −0.4 ± 0.7 | −0.09 ± 0.14 | **not resolved** |

- **T6:** `sigmaLi` does not move transport by this rule, so T6 becomes a side result and the ωB97M-V energies stay off.
  The author decides.
- **What `sigmaLi` did change:** EC per Li⁺ within 0.28 nm, 0.57 (×0.90) to 1.16 (×1.10). A change of κ_NE of
  −0.36 to +0.18 in ln over the range cannot be excluded (2 SE). ×0.90–1.10 moves the Li–O σ by about ±5 % only
  (geometric rule), so a larger step could differ.
- **`epsEMC`** changes D(Li⁺) and D(EMC) by about the same exponent (−3.9 ± 0.6 and −4.2 ± 0.5) and moves the density
  (1.171 to 1.201 g/cm³). Consistent with a viscosity change, not a proof of it: the scan measured no viscosity (T4).
- **Noise:** pooled SD of ln κ_NE 0.107, i.e. 11 % per run. The three baselines gave 0.476, 0.628 and 0.522 S/m.
- **Not decided here:** any parameter value (a map, not a fit). Full κ and t₊ were not analysed.
- **Not in the runs:** the liquid is about 3.4 K warmer than displayed (1 fs step; `docs/research/water-pressure`).

