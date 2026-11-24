# Experiments on the Li⁺ shell: what each method counts

Sources for UnitcellMD#2 (decision 11 of [publication.md](publication.md): dielectric spectroscopy,
Raman and NMR together). The values are in the ledger (`summary/literature.json`); this note says
what they mean and how our MD would be compared with each.

| method | "coordinated" means | needs an assumption about | ledger entry |
|---|---|---|---|
| Dielectric (Self 2024) | the molecule no longer takes part in the free-solvent relaxation | dipole correlations; kinetic depolarization | `self2024_drs_free_ec` |
| Raman | the molecule's band is shifted by Li⁺ (EC 893 → 904, 715 → 730; EMC 928/937 → 946 cm⁻¹). Number = bound / total band area × solvent per Li⁺ | the ratio of Raman activity of bound and free molecules, and the deconvolution of overlapping bands | `raman_phelan2025_bands_ec_emc` (positions only) |
| NMR diffusion (IR-DOSY, Su 2018, 2019) | the molecule diffuses with Li⁺: D = α D_Li + (1 − α) D_free, D_free from the viscosity change of an inert reference (toluene) | a bound molecule moves exactly like Li⁺ (their Eq. 5), and exchange is averaged over the NMR time (ms) | `nmr_su2018_dosy_ec_emc_dmc`, `nmr_su2018_dosy_emc`, `nmr_su2019_dosy_ec_emc` |
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
- **NMR, EC and EMC only:** Su 2019, 1:4:4 (molar): α_EC/α_EMC = 1.41, so **EC is 59 % of the bound
  solvent at equal amounts** (1.41/2.41, my arithmetic). The individual α and the coordination
  number are in SI Table S2–S10, not read.
- **Raman, EC:EMC 3:7, 0.5–4 m:** Phelan 2025 (preprint) gives band positions and the trend,
  **no coordination number**.

**Against our models (indication only):** in EC:EMC 1:1 with one Li⁺, EC is 17.7 ± 1.4 % (M0) and
30.4 ± 3.1 % (M1) of the first-shell carbonyl O, 39.2 ± 2.1 % (M1) within 0.516 nm (STATUS,
2026-11-21). The NMR ratio says about
59 % at equal amounts, at a much higher concentration and by another definition. The sign of the
deviation agrees with the dielectric estimate (EC missing from the shell).

## Not found, or not readable here

| what | why it is missing |
|---|---|
| A Raman coordination number for LiPF₆ in EC:EMC | none found; fallback sources below |
| Morita et al. 1998 (10.1039/a806278a), Raman, EC+DMC, apparent number ≈ 3.9 at 1.5 M LiPF₆ | the publisher refuses automated reading; the number is from a search excerpt, so it is **not** in the ledger |
| Uchida & Kiyobayashi 2021 (10.1039/d1cp00967b), Raman and NMR diffusion, LiPF₆ in EC/DMC, EC about twice as preferred as DMC | same (open access, readable in a browser) |
| Yang 2018 (10.1021/acsnano.8b05038, OSTI 1471928), IR, Raman, SERS, EC:DEC | numbers only in Fig. 8 |
| Bogle 2013 (10.1021/jz400661k), ¹⁷O NMR, EC/DMC | not read |
| Su 2019 SI (α for 1:4:4 LiPF₆:EC:EMC) | not at OSTI |

**For ../Lit, if the author can download them:** Uchida & Kiyobayashi 2021 with its SI, the SI of
Su 2019, Morita 1998.

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
