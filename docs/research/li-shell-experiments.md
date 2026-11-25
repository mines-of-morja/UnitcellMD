# Experiments on the Li⁺ shell: what each method counts

Sources for UnitcellMD#2 (decision 11 of [publication.md](publication.md): dielectric spectroscopy,
Raman and NMR together). The values are in the ledger (`summary/literature.json`); this note says
what they mean and how our MD would be compared with each.

| method | "coordinated" means | needs an assumption about | ledger entry |
|---|---|---|---|
| Dielectric (Self 2024) | the molecule no longer takes part in the free-solvent relaxation | dipole correlations; kinetic depolarization | `self2024_drs_free_ec` |
| Raman | the molecule's band is shifted by Li⁺ (EC 893 → 904, 715 → 730; EMC 928/937 → 946 cm⁻¹). Number = bound / total band area × solvent per Li⁺ | the ratio of Raman activity of bound and free molecules, and the deconvolution of overlapping bands | `raman_morita1998_ec_dmc`, `raman_uchida2021_ec_dmc` (EC/DMC); `raman_phelan2025_bands_ec_emc` (positions only) |
| NMR diffusion (IR-DOSY, Su 2018, 2019) | the molecule diffuses with Li⁺: D = α D_Li + (1 − α) D_free, D_free = D in the neat solvent × the slowing of an inert reference (toluene) | a bound molecule moves exactly like Li⁺ (their Eq. 5), and exchange is averaged over the NMR time (ms) | `nmr_su2018_dosy_ec_emc_dmc`, `nmr_su2018_dosy_emc`, `nmr_su2019_dosy_ec_emc` |
| NMR shift (¹⁷O, ¹³C) | a weighted average of the bound and free shifts | the shift of the bound state | none yet (below) |
| MD, ours | carbonyl O within 0.28 nm (first shell) or 0.516 nm (Lehnert's radius) of Li⁺ | the cut-off | trials T2, T6 |

**The definitions are not interchangeable.** Only MD counts by distance. Raman and dielectric
spectroscopy see a molecule within its picosecond environment; DOSY sees whether it travels with
Li⁺ for milliseconds. For a solvent whose residence time is short (tens of ps for EC in our
runs), "travels with Li⁺" is an average over many exchanges. A fair test computes the
experiment's own quantity from the MD: for DOSY, α from our own D of Li⁺, EC, EMC (the same
equation, with D_free from the neat solvent), not the count of neighbours.

## What was found

- **NMR, EC and EMC with a third solvent:** Su 2018, LiPF₆:EC:EMC:DMC 1:3:3:3 (molar): α = 0.61 EC,
  0.37 EMC, 0.42 DMC; coordination number 4.2 ± 0.1. Per Li⁺ that is 1.83 EC, 1.11 EMC, 1.26 DMC (my
  arithmetic, 3α).
- **NMR, EC and EMC only:** Su 2019, 1:4:4 (molar), SI Table S7: α = 0.68 EC, 0.48 EMC, coordination
  number 4.61. So **EC is 59 % of the bound solvent at equal amounts** (0.68/1.16). Per Li⁺ that is
  2.7 EC and 1.9 EMC (4α). Recomputed from the printed D: α 0.674 and 0.477, number 4.61, ratio 1.41.
- **Raman, EC and DMC, 1 mol/kg:** Uchida 2021, SI Table S VII: 3.4–3.6 solvent molecules per Li⁺ for
  every x_EC from 0.13 to 0.67; EC 1.73 at x_EC = 0.355, 2.34 at 0.569. Corrected with calculated
  activity ratios (EC 1.18).
- **Raman, EC and DMC 1:1 (volume):** Morita 1998, Table 2: EC 3.2, 3.0, 2.6 and DMC 1.2, 1.1, 1.3 at
  0.5, 1.0, 1.5 mol/L; sum 4.4 to 3.9. No activity correction. Uchida quotes Borodin's reassessment
  at 1 mol/L: EC 2.8, DMC 1.2 (second-hand).
- **Raman, EC:EMC 3:7, 0.5–4 m:** Phelan 2025 (preprint) gives band positions and the trend,
  **no coordination number**.

## EC preference: experiments and our models on one scale

P = (n_EC/n_linear) · (1 − x_EC)/x_EC: 1 if the shell has the composition of the solvent, above 1 if
EC is preferred. P removes the composition, so different mixtures can be compared. Script:
[li-shell/ec_preference.py](li-shell/ec_preference.py).

| source | system | P |
|---|---|---|
| Su 2019, DOSY | LiPF₆:EC:EMC 1:4:4 | **1.41 ± 0.11** |
| Su 2018, DOSY | 1:3:3:3 with DMC | 1.65 (EC/EMC), 1.45 (EC/DMC) |
| Uchida 2021, Raman | EC/DMC, 1 mol/kg, x_EC 0.13 → 0.67 | 2.1 → 1.6 (1.77 at 0.355) |
| Morita 1998, Raman, uncorrected | EC/DMC, 0.5, 1.0, 1.5 mol/L | 2.1, 2.1, 1.6 |
| **M0, trial T2** (1 M, 3:7 w:w), 0.28 nm / 0.516 nm | x_EC 0.336 | **0.25 / 0.49** (± 0.01) |
| **M1, trial T2**, 0.28 nm / 0.516 nm | x_EC 0.336 | **0.58 / 0.76** (± 0.01) |
| Lehnert 2025, their MD, 0.516 nm | x_EC 0.336 | 1.75 ± 0.10 (plot reading) |

The ± 0.11 is our propagation of 2 % per D (Su 2018's typical error; Su 2019 prints none). It does
not contain the systematic error below. The ± of our runs is the SE over three seeds.

**What this says:** all four experiments in the table put P above 1 (¹⁷O NMR does not, below); both our models are below 1, M1 about a factor
of 2.4 below Su 2019. M1 moved in the right direction (0.25 → 0.58). The mixtures with DMC are
comparable because Su 2019 finds DMC and EMC nearly equal (1.02).

**EC per Li⁺ near our composition:** Raman gives 1.73 (EC/DMC, x_EC 0.355, 11.2 solvents per Li⁺), M1
0.97 (EC/EMC, x_EC 0.336, 10.6 per Li⁺). Dielectric spectroscopy gives an **upper bound** of about
2.2 (trial T2). The three are consistent with a true value between M1 and the bound. T6's decision
rule is fixed and unchanged; T6 reports P and the Raman count next to it (its Amendment 6).

**What this does not say**

- No Raman number exists for EC:EMC; the Raman rows are EC/DMC.
- **The size of α in DOSY is uncertain.** It rests on toluene telling how much a free solvent
  molecule slows down. With the viscosity ratio in its place (Uchida's D and η), the same equation
  gives **negative α for DMC at every x_EC, and for EC at four of six** (down to −0.90 and −0.70). A
  molecule of fixed Stokes radius is therefore not a valid free reference. Whether toluene is a
  better one is not tested in these papers. The **sign is robust**: EC and EMC diffuse equally in
  the neat solvent (8.93, 9.00) and EC slower with salt (1.97, 2.37), so P > 1 for every toluene ratio
  that gives positive α; P would be 1.65 at 0.33 and 1.23 at 0.45 (Su: 0.369).
- Raman numbers count ion-paired Li⁺ too and depend on the calculated activity ratio.
- **¹⁷O NMR disagrees:** Uchida analyses Bogle 2013 the same way and finds P ≈ 1 or below (EC/DMC, above
  30 % EC). Uchida's explanation is that ¹⁷O counts the second shell (up to nine molecules). Our 0.516 nm
  counts (P 0.49 and 0.76) are still below 1.
- The temperature is 298 K (Morita ± 5 K), "room temperature" (Uchida) or not stated (Su); ours is
  293 K.

## Still missing

| what | why |
|---|---|
| A Raman coordination number for LiPF₆ in EC:EMC | none found |
| Bogle 2013 (10.1021/jz400661k), ¹⁷O NMR, EC/DMC | not read; quoted by Uchida |
| Borodin 2016 (10.1039/c5cp05121e, ref. 21 of Uchida), Raman activity ratios | not read; the values are used by Uchida |
| Yang 2018 (10.1021/acsnano.8b05038, OSTI 1471928), IR, Raman, SERS, EC:DEC | numbers only in Fig. 8 |

Su 2019 with SI, Uchida 2021 with SI and Morita 1998 were read in full text from `../Lit` on
2026-11-25; table values were compared with the page images.

# Refractive indices: coverage (UnitcellMD#3)

| solvent | temperatures (°C) | sources in the ledger (`nD_…`) | gap |
|---|---|---|---|
| EMC | 25 | Oh 2018 only | no temperature dependence, one source |
| EC | 45 | Oh 2018 only | one temperature (liquid; melts at about 36 °C); no value for the supercooled liquid |
| PC | 20, 25, 35, 40 | Comelli 2006, 2010; Arbad 2006 | — |
| DEC | 20, 25–50 | Comelli 2006, 2010; Arbad; Ottani; Narendra | 40 °C: Ottani 0.0010 below Comelli |
| DMC | 20, 25, 35, 40 | eight sources | 40 °C: Ottani 0.0014 below Comelli 2010; Moosavi 2016 irregular, not recommended |
| EC:EMC 3:7 | — | none found | a mixing rule would be our choice, not a measurement |

All n_D are from the **NIST ThermoML records of the papers**, not the papers; every value was
compared with the record by script (37 of 37). The spread between sources (at most 0.0014)
changes ζ = 1/n_D by less than 0.0008, far below any other error of the charge scaling.
