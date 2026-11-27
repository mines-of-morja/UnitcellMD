# A1.7 target 2: the thermodynamic factor of NaCl in SPC/E water

Second known-answer test of the structure-factor method (design `docs/design/A1.7-tdf.md` §4.2). Target 1, the
binary Lennard-Jones mixture, passed, but its non-ideal part is close to zero
(`ucmd-analysis/validation/a17-lj/REPORT.md`). This target has a large one. **Plan, reference and criterion are
written and committed before any run.** Approved by the author on 2026-11-27 ("yes, add it to the queue"); the
papers were put into `../Lit` the same day.

## Target

**Γ(m) = 1 + d ln γ± / d ln m** (molality scale) of NaCl in SPC/E water with Joung–Cheatham ions, 298.15 K, 1 bar,
from Mester & Panagiotopoulos 2015 (ledger `mester2015_jc_spce_lngamma`, version of record and SI read):
ln γ± at nine molalities (SI Table IV) and their fit (Eq. 3, SI Table XIII). This Γ is `TDF_molal` of ucmd-analysis
(ions as one species, water as the solvent).

| m (mol/kg) | Γ_ref | uncertainty |
|---|---|---|
| 1 | 1.078 | 0.029 |
| 2 | 1.389 | 0.075 |
| 3 | 1.760 | 0.146 |

`reference.py` → `reference.json`: Γ_ref is the derivative of the authors' fit. The uncertainty comes from refitting
b, C, D of Eq. 3 (A, B as printed) to Table IV with each ln γ drawn from its printed error, 20 000 draws, times the
Birge ratio √(χ²/dof) = 2.08: Eq. 3 does not fit Table IV within its errors (the two lowest molalities). The refit
itself gives 1.074, 1.401, 1.789, inside these bands.

**Why Mester and not Cheng's figure:** Mester prints numbers with errors; Cheng 2022 (Fig. 4) and Wang et al. show
excess chemical potentials only as plots. Benavides et al. 2016 (in `../Lit`) is not used for the verdict.

## Model (builder set `nacl-jc-spce`, branch `claude/a17-nacl-spce`, 5f2bcae, not pushed)

- **SPC/E** (Berendsen, Grigera, Straatsma 1987, p. 6271): rigid, O–H 0.1 nm, tetrahedral H–O–H, −0.8476/+0.4238 e,
  LJ from the printed A = 0.37122 (kJ/mol)^1/6 nm and B = 0.3428 (kJ/mol)^1/12 nm (σ 0.316556 nm, ε 0.650170 kJ/mol).
- **Na⁺, Cl⁻** (Joung & Cheatham 2008, Table 5, SPC/E column): Rmin/2 1.212 and 2.711 Å, ε 0.3526418 and
  0.0127850 kcal/mol; Lorentz–Berthelot.
- Cross-check: Mester's SI Tables I–II print the same values as σ, ε (agreement to their last digit; ε of the ions
  1·10⁻⁵ higher in their print, a conversion factor of about 4.18404).

## Systems (`recipes/`, `make_packages.sh`)

| system | water | NaCl | m (mol/kg) | Mester's composition × |
|---|---|---|---|---|
| nacl_m1_w4000 | 4000 | 72 | 1 | 8 |
| nacl_m2_w4000 | 4000 | 144 | 2 | 8 |
| nacl_m3_w4000 | 4000 | 216 | 3 | 8 |
| nacl_m3_w2000 | 2000 | 108 | 3 | 4 (box-size check) |

Packed with Packmol at Mester's volume (SI Table IV), minimized here (FIRE with the constraints, `ucmd` 2ea7e82),
validated (`ucmd-spec`). 3 mol/kg is below the model's solubility, 3.59 ± 0.04 mol/kg (Mester, SI Table XI).

**Box size.** About 4000 water, not Cheng's 32 640: in a box that large the slowest concentration mode relaxes in
about 2 ns, and a judged run needs ten blocks of five relaxation times, some 100 ns at about 100 000 atoms. The
2000-water box at 3 mol/kg tests whether the size matters here.

## Protocol (`study.toml`)

Mester's (p. 044507-5): NPT, 298.15 K, 1 bar, 2 fs, Nosé–Hoover 1 ps, barostat 2 ps, LJ and Coulomb cut at 0.9 nm,
LJ potential-shift, PME 10⁻⁶. Here: Nosé–Hoover chain of 3, C-rescale (on the GPU the bridge's Monte Carlo barostat;
the same ensemble, so the same averages), PME order 5 (Mester 6). **Assumption:** no long-range dispersion
correction, because none is mentioned. 42 ns per system (21·10⁶ steps), the first 2 ns not analysed, frames every
5 ps, GPU (`gpu-hip-mixed`, mixed precision as admitted for thermostatted production by ADR 0012).

## Criterion (fixed before the runs)

For each of the three 4000-water systems: **|Γ − Γ_ref| ≤ 2 √(SE² + σ_ref²)**, with Γ = `TDF_molal` from all analysed
frames (every second frame, 10 ps), form `matrix` (ions merged into one species), k ≤ 4 nm⁻¹, SE the standard error
over 10 blocks. The code refuses blocks shorter than five relaxation times of the slowest mode; such a run is
continued, not judged. **Target 2 passes if all three pass.**

Nothing is tuned on the result. A failure is reported as one.

## Reported, not used for the verdict

- the 2000-water box at 3 mol/kg against the 4000-water box (difference in combined SE);
- k ≤ 3 and 5 nm⁻¹, the forms `coulomb` (Na⁺ and Cl⁻ apart in the fit) and `scalar`;
- Newman's molar TDF and the partial molar volume of the salt;
- the volume per 500 water against Mester's ⟨V⟩ (SI Table IV, the same compositions): a check of the model and the
  protocol, independent of the method. A difference above 0.5 % is reported as a model or protocol difference.

## Seen before the runs

- The four minimized starts (energies in `work/*/minimize.log`) and a 10-step and a 300-step CPU run of the
  2000-water box to test the engine and the analysis (`work/check`, `work/plumbing`). The analysis refused the
  0.6 ps trajectory, as it should. The volume printed there is the packed start's, not a result.
- Mester's data and their fit (the table above).

## Cost

Not measured on the GPU (the queue holds it). Estimate: about 12 400 atoms, 0.9 nm cutoff, 2 fs; from the 1 M box
(7000 atoms, 1.4 nm, 1 fs, about 90 ns/day) perhaps 100–200 ns/day, so 5–10 h per 4000-water run, 20–40 h in all.
The worker's first run gives the measured speed.

## Commands

```sh
bash make_packages.sh                         # already done: packages/*.ucsys
python3 tools/queue/ucmd_queue.py submit study 2026-11-27_a17-nacl-jc-spce --needs gpu-hip-mixed --as <session>
../../ucmd-analysis/.venv/bin/python -I reference.py
HDF5_USE_FILE_LOCKING=FALSE PYTHONPATH=../../ucmd-analysis-tdf/src ../../ucmd-analysis/.venv/bin/python analyze.py
../../ucmd-analysis/.venv/bin/python -m pytest test_analyze.py
```
