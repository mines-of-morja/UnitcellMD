# Literature note on the papers added 2026-11-27 (task V-5)

- **Written by** agent "literature" (V-5), 2026-11-28.
- **What was read:** the 17 papers in `../Lit` that were new or newly renamed on 2026-11-27, read from `pdftotext` of the
  PDFs, plus the Gruber 2026 SI (CSV) and the Doherty 2017 SI2 (xlsx). The reading is section by section, not a
  word-by-word reading of every page.
- **Viscosity and transport first:** the short note [viscosity-transport.md](viscosity-transport.md) (committed earlier, for V-1 and
  V-2) has the measured η, D, ρ and κ tables. This README repeats only what each paper contributes.
- **Ledger:** every number we may compare with is in `docs/research/summary/literature.json` (15 new ids, listed in §7).
  - Each id records the table or page and the version read.
  - A number in this file without an id is context and must not be compared with.
- **"Ours"** marks our own arithmetic. It comes from [derived.py](derived.py) → `derived.json`, which reads only the ledger.
- **Quotations** are one sentence at most, with the page. No PDF is committed.

## 0. What changes

1. **No measured self-diffusion (pfg-NMR) of LiPF₆ in EC:EMC is in `../Lit`.**
   - The nearest is EC:DMC (Uchida 2021).
   - The EC:EMC source is Capiglia 1999 (2:8, named by Nyman 2008). It is on the missing list.
2. **The measured η at 1 M, 20 °C is 3.0–3.3 mPa s.** Two readings of Logan's data differ by 8 %, and Bergstrom's lab is 15–25 % higher
   at 30 °C. The reference is good to about ±10 %, not ±2 %.
3. **Other fixed-charge models of carbonates are too slow and too viscous as well**, and OPLS-type carbonates over-bind (§2).
   - The polarizable APPLE&P, whose parameters were not fitted to carbonate liquids, is right on ρ and ΔH_vap and slightly too fluid.
   - **The direction of our EMC error (over-cohesive, too dense, too slow) is the common direction of non-polarizable OPLS models.**
   - Its size (+30 % in ΔH_vap) has no published counterpart for EMC.
4. **Finite-size correction:**
   - Borodin 2009 (+10 to 16 % on D), Fan 2025 and Dajnowicz 2022 (its small ML boxes) apply Yeh–Hummer with the model's own η.
   - The other carbonate papers read do not correct.
   - The two "box-size independence" tests found only double the volume, which cannot resolve the correction (§1.1, §1.4).
5. **ECC-R:** the 2020 practical guide states the rule (p. 050901-4):
   > "As a general rule, a 5%–10% decrease in the ion radius allows us to recover the correct hydration structure; however, the
   > exact value is water model dependent."

   It is fitted to neutron scattering with isotopic substitution, in water, for monatomic ions. No polyatomic-anion or carbonate
   case was found (§4).
6. **Doherty 2017 did not refit LJ after scaling.**
   - It scales OPLS-2009IL charges by 0.8 and keeps every LJ term (p. 6133).
   - The [RMIM][PF₆] densities then fall by about 3 % (Table 2).
   - The ion-model README's description of it (§5 there) is wrong.
7. **"Jamali et al." is identified:**
   - S. H. Jamali et al., J. Chem. Theory Comput. 14, 5959 (2018), η from the finite-size effect of D, cited by Lehnert 2025 (ref. 101).
   - It is V-2's method. It is not a source of ζ or LJ choices.
8. **"Not found" claims:** every candidate-for-new claim of the 26 Nov summary §6 survives the papers read (§3).
   - Two need a qualification: pair-specific LJ terms do exist in a carbonate model (Ravikumar 2018), and the Maiti ρ(c) is only in a figure.

## 1. Per paper

Each entry gives: system; force field and ion charges; time step and constraints; ensemble during transport; box and
finite size; model against experiment with table or page; what it means for us.

### 1.1 Borodin & Smith 2009, J. Phys. Chem. B 113, 1763 (+SI)

- **Read:** VoR, main text in full. The SI holds only cluster geometries (Figs. S1–S2), nothing quantitative.
- **System:** LiPF₆ (≈ 1 M) in EC, DMC, EC:DMC 1:1 and 3:7 (mol), 298–363 K; pure EC (313 K) and DMC (298 K).
- **Force field:** APPLE&P, many-body polarizable (Thole), full ion charges.
  - Repulsion and dispersion come from alkanes, fluoroalkanes and DME. The carbonyl O shares the ether O parameters.
  - No EC or DMC liquid data were used in the fit (p. 1768).
  - The previous version had needed "a new R/D type for the carbonyl carbon … to describe thermodynamic data for carbonate liquids"
    (p. 1768; Borodin & Smith 2006, not read).
  - Li⁺–EC repulsion was scaled so that binding is 1.5 kcal/mol weaker than MP2, to match the measured ion dissociation (p. 1768).
- **Integration:** multiple time step, 0.5 / 1.5 / 3.0 fs. SHAKE on all bonds except P–F. Nosé–Hoover thermostat and barostat
  (p. 1769).
- **Ensemble:** NPT equilibration, then NVT sampling of 4.3–20.6 ns (Table 7).
- **Finite size:** Yeh–Hummer/Dünweg–Kremer, ΔD = 2.837 k_BT/(6πηL), with the model's own η (Eq. 10, p. 1773).
  - The correction is 10–16 %. Ion D values are scaled by the solvent's factor, 1.11–1.17.
  - Small and large boxes (240 against 480 solvent molecules) agree to < 10 % (p. 1773). A twofold volume changes the correction by
    only 21 % of itself (ours), so that test cannot see it.
- **η:** Einstein form with the symmetrized traceless stress tensor, all components (Eqs. 11–12). Collective quantities are trusted only
  up to 1–2 % of the run (p. 1774).
- **Against experiment** (Table 6; `borodin2009_table6_ec_dmc_pure`):

  | | ρ | ΔH_vap | D (+ FSC) | η |
  |---|---|---|---|---|
  | EC, 313 K | 1302 vs 1321 kg/m³ (−1.5 %) | 13.8 kcal/mol (no experiment printed) | 7.8 + 1.2 vs 8 (×10⁻¹⁰ m²/s) | 1.75 vs 1.85 cP (−5 %) |
  | DMC, 298 K | 1040 vs 1057 (−1.6 %) | 8.88 vs 9.01 kcal/mol (−1.4 %) | 22 + 3.4 vs 26 (303 K) | 0.47 vs 0.59 cP (−20 %) |

- **Electrolytes:**
  - densities only at 1 M, with no experimental comparison printed (Table 7);
  - κ overestimated by up to 37 % in EC and DMC, better in the mixtures (p. 1774, Fig. 12);
  - η of the electrolytes only as 1/η in Fig. 10.
- **Structure:** first Li–O(carbonyl) peak at 1.98 Å, "in close agreement with the separation of 2.04 Å derived from neutron
  scattering experiments" on PC/LiPF₆ (p. 1769, their ref. 22 = Kameda 2007). The neutron peak height is "around ∼30" (p. 1769).
- **For us:**
  - The polarizable model is slightly **too fluid** and correct on cohesion, the opposite of our EMC.
  - It is the only carbonate MD paper read that applies Yeh–Hummer with the model's η, and it reports the size.

### 1.2 Maiti et al. 2023, Phys. Chem. Chem. Phys. 25, 20350 (+ESI)

- **Read:** VoR main text and ESI in full. The publisher had refused it on 27 Nov; the PDFs are now in `../Lit`.
- **System:** LiPF₆ in EC:EMC 24:76 by mass, 0.21–2.44 M, 333 K; EC content 0–76 % at 0.95 M. FTIR of LP57 (1 M) and 2 M,
  EC:EMC 3:7.
- **Force fields:**
  - OPLS-AA with full ion charges;
  - OPLS-AA with ion charges × 0.8;
  - **APPLE&P** (Lucretius), the polarizable force field the ion-model README could not name.
- **Integration:**
  - OPLS: GROMACS, 2 fs, LINCS on H bonds; Nosé–Hoover 0.5 ps, Parrinello–Rahman 2 ps, **NPT during the analysed run**;
    PME 1.6 nm. Run length printed "1 ms" (p. 20352), probably 1 µs.
  - APPLE&P: multiple time step 0.5 / 1.5 / 3 fs, SHAKE on all bonds, Nosé–Hoover chains, NPT, 100 ns.
- **Finite size:** none. Box sizes were not found in the ESI text.
- **η:** Einstein form, six traceless components averaged. The result is independent of the pressure-tensor output interval below
  12 fs (ESI p. 7, Fig. S8).
  - APPLE&P values in ESI Table 2 (`maiti2023_esi_table2_eta_applep`): 1.22 cP at 0.95 M and 60 °C (24:76); 3.64 cP at 1.93 M and 50 °C.
  - The OPLS and OPLS × 0.8 values are only in Fig. 5a, ordered η(OPLS) > η(× 0.8) > η(APPLE&P) at 0.95 M (p. 20356).
- **Against experiment:**
  - κ: APPLE&P agrees with the HTS data. OPLS is "nearly one order of magnitude lower" at high salt, and × 0.8 "remains still lower"
    (p. 20353, Fig. 2a).
  - η (APPLE&P), extrapolated to lower T, agrees with Logan's data (p. 20356).
  - Density: only ESI Fig. S2. "charge rescaling reduces the density, which explains faster dynamics due to charge rescaling"
    (ESI p. 3). **No density numbers are printed.**
  - Li–O(carbonyl) peak at 1.95 Å (APPLE&P) against 2.05 Å (non-polarizable) (ESI p. 5).
- **For us:**
  - The same sign as ours: non-polarizable OPLS gives slow ions and a high η.
  - ×0.8 lowers both the density and η. So lower charges help the dynamics and hurt the density, the trade-off of T5.

### 1.3 Hou, Fong, Wang, Persson 2021, Chem. Sci. 12, 14740 (+ESI)

- **Read:** VoR and ESI.
- **System:** 1.2 M LiPF₆ in EC:EMC 3:7 w/w ("Gen2"), in EC, and both with 10 % FEC; 298 K.
- **Force field:** OPLS-AA EC/EMC with RESP charges. **Li⁺ is Jensen & Jorgensen 2006 (JJ06) and PF₆⁻ is Canongia Lopes & Pádua 2004
  (CL&P), our ion model, with full charges** (p. 14741, refs. 40–41).
- **Integration:** LAMMPS, PPPM, 1.5 nm cutoff. NPT 5 ns, annealing to 400 K, then **NVT, Nosé–Hoover 1 ps, 60 ns × 4 independent
  runs**. The time step is not stated.
- **Box:** 504 EC + 996 EMC + 166 LiPF₆, L ≈ 6.2 nm (ours). No finite-size correction.
- **Against experiment:**
  - D only in Fig. 5b. "the non-polarizable force field employed here underestimates the diffusivity" (p. 14747).
  - Measured κ(Gen2) = 9.79 mS/cm at 25 °C (ESI Table S4; `hou2021_table_s4_kappa_gen2`).
  - Nernst–Einstein overestimates the Green–Kubo κ of Gen2 by > 40 % (ESI Fig. S9).
  - EC ΔH_vap 62.39 kJ/mol at 313 K against 60.3 (at 383 K) (ESI p. 15).
- **For us:**
  - A full-charge version of our ion model in nearly our solvent, too slow, in a box 1.45 times longer than ours.
  - Its ζ = 0.8 counterpart is Ringsby 2021 (cited there as ref. 70), which is Lehnert's 1 M source.

### 1.4 Ravikumar, Mynam, Rai 2018, J. Phys. Chem. C 122, 8173 (+SI)

- **Read:** VoR and SI.
- **System:** LiPF₆ in EC only, 0.06–3.95 M, 330 K.
- **Force field:**
  - CFF93 bonded terms; EC from Soetens et al. 1998, J. Phys. Chem. A 102, 1055; Li⁺ and PF₆⁻ from Jorn et al. 2013 and Kumar &
    Seminario 2016 (refs. 26, 28, 29);
  - full charges (Li⁺ +1; P +1.07, F −0.345);
  - **pair-specific LJ terms** Li–O(carbonyl), Li–P, Li–O(ether), F–H and F–C(carbonyl) (Table 1).
- **Integration:** LAMMPS, 1 fs, PPPM, 12 Å LJ cutoff. NPT 15 ns, NVT 15 ns, then **NVE 30 ns** for production, ≥ 3 runs.
- **Box:** 220 EC + 17 LiPF₆ (initial edge 2.9 nm).
  - Size test with 440 + 34: D(Li⁺) 0.40 against 0.41, D(PF₆⁻) 0.67 against 0.66 (×10⁻¹⁰ m²/s; SI Fig. S2; `ravikumar2018_box_size_d`).
  - Hence "the results are box size independent" (p. 8175).
  - No error bars; the volume is only doubled (L × 1.26).
- **Against experiment:** D "match[es] well with the range of values reported in the literature" (Fig. 2); no density; no η.
- **For us:**
  - The nearest published case of pair-specific ion–solvent LJ in a carbonate electrolyte.
  - Those terms come from earlier parameter papers, not from a fit to solution densities.

### 1.5 Dajnowicz et al. 2022, J. Phys. Chem. B 126, 6271

- **Read:** VoR main text. The SI (Tables S1–S5, Figs. S6–S10) is **not in `../Lit`**.
- **System:** seven carbonates and LiPF₆. QRNN neural-network potential trained on ωB97X-D3BJ cluster data; OPLS4 (Desmond) as the
  benchmark.
- **Integration:** QRNN in ASE, 0.5 fs, Nosé–Hoover 0.05 ps, Parrinello–Rahman 2.5 ps. About 1000 atoms; 20 NVT replicas of 1 ns.
  OPLS4 boxes have 8 times the molecules (p. 6274).
- **Finite size:** the QRNN D "include a finite size correction for the small simulation boxes" (p. 6276).
  - With OPLS4: 1 ns is enough for η of the salt-free solvent; 2 m LiPF₆ needs 10 ns.
  - η at high viscosity "increases rapidly as simulation size is below 2000 atoms" (p. 6276).
- **Against experiment** (main text):
  - OPLS4 "systematically overestimates the experimental viscosities by a significant amount for all the pure carbonate solvents"
    (p. 6275). RMSE about 1.06 cP, against 0.31 for QRNN.
  - OPLS4 ΔH_vap RMSE 9.15 kJ/mol, against 3.23 for QRNN. The sign is not stated in the text.
  - Both potentials underestimate solvent D (Fig. 2).
  - EC:DMC 3:7 with 0–2 m LiPF₆ at 313 K: OPLS4 overestimates η at every c (Fig. 4, against Logan A21). QRNN agrees to 1 m.
- **For us:** a second OPLS family that is too viscous for pure carbonates, with its η error larger than its density error.

### 1.6 Nyman, Behm, Lindbergh 2008, Electrochim. Acta 53, 6356

- **Read:** VoR in full.
- **System:** LiPF₆ in EC:EMC 3:7 w:w, 25 °C, 0.2–2.0 mol/dm³. Electrochemical characterisation: concentration cells, galvanostatic
  polarisation, conductivity.
- **What it has:**
  - **No density table and no viscosity.**
  - Partial molar volumes, constant over 0–2 M: V̄(LiPF₆) = 59, V̄(solvent) = 87 cm³/mol (p. 6360, Fig. 5;
    `nyman2008_partial_molar_volumes_ec_emc`).
  - κ polynomial, Eq. 22 and Table 2, maximum 9.5 mS/cm at 1.0 M (`nyman2008_kappa_eq22_ec_emc_25C`).
  - Fickian salt D̃(c) and t₊(c) polynomials (Table 3).
  - Citations: Ding 2001 (κ = 8.7 mS/cm at 1 M, 25 °C, same solvent; p. 6357) and Capiglia 1999 (pfg-NMR of ⁷Li and ¹⁹F in EC:EMC 2:8).
- **Ours:**
  - The volumes imply ρ₀ = 1.135 g/cm³, 4.6 % above Landesfeind's 1.085 at 25 °C. So V̄(solvent) cannot give ρ₀.
  - The implied slope dρ/dc = 0.085–0.088 g cm⁻³ M⁻¹.
- **For us:**
  - V̄(LiPF₆) = 59 is a second measured salt volume (Landesfeind 55.7; model 70.6).
  - "Constant in c" means Nyman's data **cannot** resolve a curvature of V_φ (route-plan §7).

### 1.7 Bergstrom, Fong, McCloskey 2021, J. Electrochem. Soc. 168, 060543 (+SI3)

- **Read:** VoR and SI3. SI3 holds an error propagation, the solvent-to-centre-of-mass frame conversion t₊^COM = ω₀t₊ + ω₋ (Eq. S9), and
  COMSOL inputs (Table S1).
- **System:** LiPF₆ in EC:EMC 3:7 w:w, 30 °C, 0.05–1.5 mol/kg (Table I; `bergstrom2021_table1_ec_emc_3_7_30C`).
- **Viscosity:** EMS-1000s spinning viscometer: 3.04 ± 0.02 mPa s at 1.001 m (1.043 M).
  - This is 23 % above Logan's 2.47 (as transcribed) and 14 % above Lehnert's fit (2.66) at 30 °C (ours).
- **Density:** from weighing 100 µl pipetted volumes. −4.0 % to +2.4 % off Landesfeind's fit, slope 0.141 against 0.0912 (ours).
  **Not usable.**
- **κ and t₊:** κ "in good agreement with values reported in the literature". The paper's point is that Li-metal polarisation methods
  give unreliable t₊ and thermodynamic factors because of interfacial resistance.
- **For us:**
  - The measured η of this electrolyte scatters by 10–25 % between labs.
  - Eq. S9 is a ready check of our frame conversions (decision 10).

### 1.8 Gruber, Rutz, Hofmann, Weber 2026, J. Electrochem. Soc. 173, 120518 (+SI1 CSV)

- **Read:** VoR main text and the SI1 CSV in full (`gruber2026_si1_eta_rho_ec_dmc_emc_vc`).
- **System:** commercial LiPF₆ in EC:DMC:EMC 30:35:35 vol % + 1.5 wt % VC (E-Lyte), 10 nominal concentrations 0.25–3.0 M.
  - η and ρ: Anton Paar SVM 3001, ASTM D7042, 17 isotherms from −20 to 60 °C, 2 replicates (4 at 0.75 M, 1 at 1.75 M).
  - κ: EIS, 11 isotherms from −20 to 45 °C.
- **What it gives (ours, from the CSV):**
  - dρ/dc at 20 °C: 0.0916 (0.25–1 M), 0.0894 (1–2 M), 0.0804 (1.5–3 M).
  - A straight line through 0.25–3 M lies 0.31 % and 0.35 % above the data at the two ends and 0.40 % below at 2 M: the data curve.
  - E_a(η) = 16.1 kJ/mol at 1 M (15–25 °C). η(3 M)/η(1 M) = 17 at 20 °C.
  - This reproduces Jo's §6 to the printed digits. **Jo's "measurements from our group" are this published SI.**
- **Limits:**
  - not EC:EMC 3:7: DMC and VC are present;
  - concentrations nominal;
  - no salt-free row, so V_φ cannot be formed from the file alone.
- **For us:** a band, and the held-out prediction test of the route plan (Q8). It needs a DMC model and a decision on VC.

### 1.9 Logan, Tonita, Gering, Dahn 2018, J. Electrochem. Soc. 165, A3350 (the Logan in `../Lit`)

- **Read:** VoR.
- **What it is:** an evaluation of the Advanced Electrolyte Model against measured η and κ. The EC:EMC 30:70 viscosities are shown only as
  figures (Fig. 3a, Fig. 5g; Ostwald viscometer, 10–40 °C, ±2 % after interpolation).
  - The tables are in Logan et al. 2018, J. Electrochem. Soc. 165, A21 (and A705). **They are not in `../Lit`.**
- **The numbers in our notes** (1.0 m: 3.05 cP at 20 °C) are an earlier agent's transcription of A21 (`logan2018a21_eta_ec_emc_3_7`,
  marked unchecked).
- **Lehnert 2025 SI Table S8** fits Arrhenius curves to the same Logan data (their ref. [46] = A3350;
  `lehnert2025_table_s8_eta_fit_logan`).
  - The fit gives 3.30 cP at 1.0 m and 20 °C (ours). It is 5–8 % above the transcription at every temperature.
  - One of the two readings is off. Reading A21 settles it.

### 1.10 Uchida & Kiyobayashi 2021, Phys. Chem. Chem. Phys. 23, 10875 (+ESI)

- **Read:** VoR and ESI (numerical tables S I–S VII).
- **System:** 1.0 mol/kg LiPF₆ (and LiFSA) in EC:DMC, x_EC 0–0.67, 288–328 K.
  - PGSE NMR of ⁷Li, ¹⁹F and ¹H at 298 K; cone-plate η; pycnometer ρ (two decimals); κ; Raman with the activity correction of
    Borodin et al.
- **Ledger:** `uchida2021_si_lipf6_ec_dmc_1molal`, `uchida2021_table_s7_raman_solvation`.
- **Key numbers** (x_EC = 0.355, 298 K):
  - D(Li⁺) 2.25, D(PF₆⁻) 3.17, D(EC) 4.22, D(DMC) 5.74 ×10⁻¹⁰ m²/s;
  - η 3.26 mPa s; κ 12.1 mS/cm;
  - solvation numbers EC 1.73, DMC 1.78 (cis-trans 0.35 + cis-cis 1.43).
- **Also:**
  - The classical Stokes–Einstein relation "still quantitatively holds" for the hydrodynamic radii (abstract), with a shape factor
    of 3.5 for the solvents (ESI Fig. S8).
  - Pure DMC: η 0.57 mPa s, D 24.8 ×10⁻¹⁰ m²/s at 298 K.
- **For us:**
  - The only complete measured set (D, η, ρ, κ, shell) for LiPF₆ in a linear-carbonate mixture in hand.
  - It is EC:DMC, so a cross-check, not a target.

### 1.11 Su et al. 2019, Energy Environ. Sci. 12, 1249 (+ESI)

- **Read:** VoR and ESI.
- **System:** DOSY-based "solvating power series" of carbonate solvents; LiPF₆:solvent:EMC 1:4:4 (molar), with toluene as an internal
  reference. The temperature is not stated.
- **Numbers:** ESI Table S7, EC:EMC (`su2019_table_s7_dosy_ec_emc`): D(Li⁺) 1.33, D(EC) 1.97, D(EMC) 2.37 ×10⁻¹⁰ m²/s. EC is the
  stronger solvator (α_EC 0.68 against α_EMC 0.48).
- **For us:** not a transport target (toluene in the sample, about 1.4 M by our estimate, T unknown). It is a qualitative statement that
  EC out-solvates EMC.

### 1.12 Morita, Asai, Yoshimoto, Ishikawa 1998, J. Chem. Soc., Faraday Trans. 94, 3451

- **Read:** VoR.
- **What it has:** Raman solvation numbers. 1.0 M LiPF₆ in EC:DMC 50:50 by volume: EC 3.0, DMC 1.1 per Li⁺ (Table 2, p. 3454;
  `morita1998_table2_raman_solvation`).
- **Caveat:** Raman activities are not corrected. Borodin 2009 shows that such data overstate the EC preference, and Uchida applies the
  correction.
- **For us:** an upper bound on the EC share, not a target.

### 1.13 Duboué-Dijon, Javanainen, Delcroix, Jungwirth, Martinez-Seara 2020, J. Chem. Phys. 153, 050901 (`../Lit/050901_1_5.0017775.pdf`)

- **Read:** VoR (AIP).
  - This **is** the Duboué-Dijon 2020 "practical guide". It is **not missing**; it only needs a clear file name (§6).
- **Content for us:**
  - **ECC recipe:** scale every charged group to 0.75 of its nominal charge (ε_el ≈ 1.78 of water), then run classical MD (p. 050901-3).
  - **Overscaling:** water models already hold part of the electronic polarization, so factors "between 0.75 and 1 depending on the
    employed water model" are legitimate (p. 050901-4). Fits have given 0.85–0.94 (p. 050901-5).
  - **ECC-R rule** (p. 050901-4): the ion LJ must be re-adjusted. The quoted rule is a 5–10 % smaller radius to recover the hydration
    structure from neutron scattering with isotopic substitution, and the value depends on the water model.
  - **Organic solvents:** Table I lists ECC factors s = 1/n for some media: toluene 0.67, hexadecane 0.70, water 0.75. No carbonate is
    listed.
  - **Limit:** dielectric discontinuities (interfaces) are outside ECC (p. 050901-3). The Li⁺ shell in a low-ε EMC-rich medium is a
    gradient of the same kind (the ion-model README's point, from Kirby & Jungwirth).
- **For us:**
  - The source of the 5–10 % size rule (route-plan §7, item 1).
  - It is about water and biomolecules. Transfer to PF₆⁻ in carbonates is our extrapolation.

### 1.14 Fan, Mason, Cruces Chamorro, Shanks, Martinez-Seara, Jungwirth 2025, J. Chem. Theory Comput. 21, 9023 (+SI)

- **Read:** VoR main text. ESI skimmed (NDIS prefactors, pair LJ tables S3, S9).
- **What it fits:**
  - the scaling factor and ion LJ σ, ε, with Lorentz–Berthelot for cations and **pair-specific anion–water-O LJ**;
  - in the de novo ECC water ECCw2024 (ε = 45);
  - against NDIS structure, density **and viscosity** (p. 9024);
  - water D as a further check.
- **Settings:** GROMACS 2022, 2776 waters; Nosé–Hoover 1 ps, Parrinello–Rahman 5 ps; PME 1.2 nm. η from cosine-acceleration NEMD
  (0.020 nm/ps²; 25 × 2 ns).
  - D is corrected by Yeh–Hummer with the model η. Using the experimental η and L instead changes it by < 2 % (p. 9025).
- **Results:**
  - The optimal factor is 0.81; the top models lie at 0.78–0.83 (p. 9026). This agrees with the short-range factors the ion-model
    README cites from Kostal 2023 (not read).
  - Density deviations are typically < 0.5 %, but −3.5 % for 4 m CaCl₂ (p. 9027).
  - Madrid2019 "frequently overestimates viscosity by more than 25 % at high concentrations" (p. 9027).
  - Li–O(water) 1.94 Å against 1.90–2.25 measured (Table 2).
- **For us:**
  - A precedent for ζ ≈ 0.8 and pair-specific anion–solvent terms.
  - **η is a fit target there**, which our rule forbids (priorities 2026-11-28). The recipe can be borrowed only without that target.

### 1.15 Mendes de Oliveira, Zukowski, …, Jungwirth, Duboué-Dijon 2020, Phys. Chem. Chem. Phys. (doi 10.1039/D0CP02987D) (`../Lit/ms_r1-corr.pdf`)

- **Read:** the HAL author manuscript (hal-02964203v1), not the VoR.
- **System:** binding of Ca²⁺, Mg²⁺, Zn²⁺ and Na⁺ to acetate in SPC/E water. GROMACS, LINCS on H bonds, NpT with Parrinello–Rahman and
  v-rescale.
  - Full-charge force fields, ECC with 0.75, ECC with 0.8, and AMOEBA, all against Raman-MCR binding constants.
- **Result:** "for the ECC force field, in all the cases reported here, a 0.8 scaling performs significantly better than the
  standard 'physically-sound' 0.75 scaling" (manuscript p. 26).
- **For us:** one more case for ζ slightly above 0.75 when the solvent model is not ECC-consistent. Divalent cations in water, so only
  indirect.

### 1.16 Doherty, Zhong, Gathiaka, Li, Acevedo 2017, J. Chem. Theory Comput. 13, 6131 (+SI2.xlsx)

- **Read:** VoR main text.
  - SI2.xlsx holds only the compiled experimental data (density, ΔH_vap, Cp, η, surface tension, D).
  - The anion parameters (SI Tables S3–S5) are in a PDF SI that is **not in `../Lit`**.
- **What it is:** OPLS-2009IL revisited for MD, new anion bonded terms, and a test of charges × 0.8.
  - **No LJ term was refitted after scaling:** "All Lennard-Jones parameters also came from the OPLS-AA parameter set except when
    explicitly stated" (p. 6133). Table 1 shows the same σ, ε for both charge sets.
- **Settings:** GROMACS, 500 ion pairs, 1 fs, LINCS on H bonds; v-rescale, Berendsen (equilibration); 40 ns.
  - η by periodic-perturbation NEMD: Green–Kubo was judged "unreliable" for ionic liquids (p. 6136).
- **Effect of ×0.8 with LJ unchanged, PF₆⁻ salts at 298 K:**
  - **density down by about 3 %**: [BMIM][PF₆] 1.356 → 1.315 g/cm³ against 1.363 (Table 2);
  - ΔH_vap close to experiment: [BMIM][PF₆] 193.8 → 148.7 against 146.5 kJ/mol (Table 3);
  - D much better;
  - η: MAE 9.5 % → 11.0 % (Table 6; [BMIM][PF₆] 287.8 → 264.4 against 282.0 cP).
- **For us:**
  - In an ionic liquid as well, scaling charges without touching LJ makes the PF₆⁻ salt too voluminous, our V_φ excess in another
    medium.
  - It is **not** a precedent for a refit after scaling. The OPLS-VSIL description in `ion-model/README.md` §5 does not fit this paper.

### 1.17 Lehnert et al. 2025, new readings only (VoR and SI, already in the ledger)

- **Transport protocol:**
  - LAMMPS, velocity Verlet 1 fs, no constraints stated;
  - Nosé–Hoover thermostat 100 fs and barostat 1000 fs;
  - NVT production 50–170 ns, three runs;
  - PPPM 10⁻⁵, 14 Å LJ cutoff (SI S1.1).
- **No finite-size correction, no Green–Kubo.**
  - η is a Stokes–Einstein estimate with a particle radius fitted to Logan's η: r(c) = 2.78 Å − 0.65 Å/M · c (SI Tables S8–S9, Fig. S13).
  - The main text names Green–Kubo and finite-size effects as alternatives (p. 6, refs. 101–103 = Jamali 2018, Schoen & Hoheisel 1985,
    Hess 2002).
- **Their 1 M box is our box:** 47 LiPF₆, 168 EC, 332 EMC (SI Table S1). Their κ and D carry the same finite-size bias as ours.

## 2. Are other models of these electrolytes over-cohesive or too viscous?

| model | cohesion | density | η | ions | source |
|---|---|---|---|---|---|
| OPLS-AA LigParGen EMC (ours, M1) | ΔH_vap 53.2 against ≈ 40.5 kJ/mol (+30 %) | +2.8 % (pure EMC) | not measured yet (V-1) | κ_NE a factor ≈ 1.7 low | SC-7 step 0; summary 26 Nov |
| OPLS4 (Desmond), seven carbonates | ΔH_vap RMSE 9.15 kJ/mol (sign not stated) | RMSE 0.029 g/cm³ | **"systematically overestimates"**, RMSE ≈ 1.06 cP; electrolyte η too high at all c | solvent D too low | Dajnowicz 2022 pp. 6275–6276 |
| OPLS-AA (RESP), JJ06/CL&P full charges, EC:EMC 3:7 | EC ΔH_vap 62.4 at 313 K vs 60.3 (at 383 K) | not given | not computed | D too low | Hou 2021 p. 14747; ESI p. 15 |
| OPLS-AA (GROMACS), full and ×0.8 ion charges, EC:EMC 24:76 | — | lower with ×0.8 (figure only) | η(OPLS) > η(×0.8) > η(APPLE&P) | κ up to 10× low (full), still low (×0.8) | Maiti 2023 p. 20353, 20356; ESI p. 3 |
| APPLE&P (polarizable) | DMC ΔH_vap −1.4 % | −1.5 % (EC), −1.6 % (DMC) | −5 % (EC), −20 % (DMC) | κ up to +37 % (EC, DMC electrolytes) | Borodin 2009 Table 6, p. 1774 |
| OPLS-2009IL ×0.8, PF₆⁻ ILs | ΔH_vap right after scaling | −3 % after scaling | MAE 11 % | D much better | Doherty 2017 Tables 2, 3, 6 |

- **Reading:**
  - Every non-polarizable OPLS variant read is too slow, and where η was computed it is too high.
  - The one family whose LJ came from non-carbonate liquids plus QM (APPLE&P) is slightly too fluid.
  - So "too cohesive → too viscous → too slow" for our EMC is the common pattern, not a peculiarity.
  - **No paper gives an EMC ΔH_vap for an OPLS model**, so the +30 % itself has no published comparison.
- **For V-1:**
  - OPLS4's pure-solvent η error is about +1 cP on solvents of 0.6–2 cP (RMSE; per-solvent values in its SI, not in `../Lit`).
  - An η(EMC) of the model 1.5–2 times 0.65 cP would therefore not be unusual for this force-field family. This is our reading of an
    RMSE, not a per-molecule number.

## 3. Which "not found" claims survive

### 3.1 Summary of 26 November, §6

| claim | status after these papers |
|---|---|
| "Not read: Maiti 2023 full text and SI, Hou 2021, Ravikumar 2018, Dajnowicz 2022, Borodin & Smith 2009, Nyman 2008" | **all read now** (Dajnowicz without SI) |
| Agrees row: "dynamics largely underestimated" for non-polarizable [6], "abstract only" | **confirmed in the full text** (Maiti p. 20353, Fig. 2a; η ordering Fig. 5a) |
| Agrees row: charge scaling lowers density and speeds dynamics [6], "SI excerpt only" | **confirmed**, ESI p. 3; still a figure, no numbers |
| New 1: "Not found: a carbonate paper that tests a scaled-charge model's ρ(c) over 0.1–3 M against experiment with numbers" | **survives.** Maiti shows ρ(c) for OPLS, ×0.8 and APPLE&P only as ESI Fig. S2; Borodin, Hou, Ravikumar and Dajnowicz give no electrolyte density against experiment. Qualification: Maiti's figure should be digitized before the claim goes into a paper. |
| New 2: the charge scale cannot fix the salt volume; "We found it shown for no carbonate" | **survives** for carbonates. Supporting evidence now in hand: in PF₆⁻ ionic liquids, ×0.8 without an LJ refit lowers ρ by about 3 % (Doherty Table 2); the guide's 5–10 % radius rule (p. 050901-4) |
| New 3: second explanation for the 3 M κ excess | not touched by these papers |
| New 4: "Not found: a published sensitivity of κ to the solvent LJ parameters of a carbonate" | **survives.** Maiti varies whole force fields, not LJ terms |
| New 5: time-step bias, "a number for this electrolyte was not found" | **survives.** No paper read tests Δt for transport |
| Proposal c: "The Madrid-2019 recipe for a carbonate … Not found for carbonates" | **survives with a qualification:** Ravikumar 2018 uses pair-specific Li–O, Li–P, F–H and F–C LJ in EC, taken from earlier parameter papers, not fitted to ρ(c,T). Fan 2025 is the newest aqueous version (pair anion–O terms), and it fits η. |

### 3.2 `emc-literature/sc7-sources.md` (agent note, unchecked)

- **"No published LJ refit of EMC to density and Δ_vap H was found":** survives for EMC.
  - New: Borodin 2009 (p. 1768) states that the earlier APPLE&P version introduced a carbonyl-carbon repulsion–dispersion type "to
    describe thermodynamic data for carbonate liquids". That is Borodin & Smith 2006, J. Phys. Chem. B 110, 6279, not read.
  - It is the nearest published precedent for SC-7 (a carbonate LJ type refitted to liquid thermodynamics). **Read it before SC-7 Q1–Q7
    are answered.**
- **Borodin & Smith 2006 "validated on ρ and ΔH_vap (from memory, unverified)":** for the 2009 version this is confirmed on EC and DMC
  (Table 6; −1.5 % / −1.6 % in ρ, −1.4 % in ΔH_vap of DMC).
- **Soetens, Millot, Maigret 1998 "citations from memory":** the citation is confirmed by Ravikumar 2018 (ref. 28: J. Phys. Chem. A
  102, 1055). Masia et al. 2004 appears as J. Phys. Chem. B 108, 2016 in Borodin's ref. 30.
- **EMC η 0.65 cP at 25 °C:** still secondary only (Logan quoting Barthel & Gores; Hou p. 14747 quoting refs. 73–74). No primary EMC
  viscosity measurement is in `../Lit`.

### 3.3 `ion-model/README.md` (agent note, unchecked)

| item there | status |
|---|---|
| §1.2: "Nyman 2008 … the density part was not obtained" | read: **no densities**, only V̄(LiPF₆) = 59 and V̄(solvent) = 87 cm³/mol, constant over 0–2 M (§1.6) |
| §1.2: Gruber 2026 "the SI might tabulate it" | yes: η and ρ at 170 (c, T) points (§1.8) |
| §2.4: "I could not identify a Jamali et al. paper" | identified: Jamali et al., JCTC 14, 5959 (2018), η from finite-size D (Lehnert ref. 101). Not a ζ or LJ source |
| §3: Maiti "which polarizable FF was used is not read" | APPLE&P (Lucretius), §1.2 |
| §3: Borodin 2009 "density accuracy not read"; "D and κ agree well" (review snippet) | pure solvents −1.5/−1.6 %; electrolytes no experimental density; κ up to +37 % in EC and DMC, better in the mixtures |
| §3 gap: "no carbonate paper that reports ρ(c) for scaled-charge OPLS against experiment over 0–3 M with numbers" | survives (§3.1) |
| §4.3: ECC-R "reduction factors were not checked" | the guide's rule: 5–10 % smaller radius, fitted to the neutron hydration structure, water-model dependent (p. 050901-4). Kohagen 2016 itself still not read |
| §4.2: Kostal 2023 short-range factors 0.78–0.83 | Kostal not read; Fan 2025 finds 0.81 optimal, top models 0.78–0.83 (p. 9026), independently |
| §5: Kumar & Seminario "about 2016, unverified" | confirmed as J. Phys. Chem. C 120, 16322 (2016) (Ravikumar ref. 29), with Li⁺ pair terms in EC (Ravikumar Table 1) |
| §5: Doherty 2017 "OPLS-VSIL … LJ of selected atoms refitted after charge scaling" | **wrong for this paper:** OPLS-2009IL revisited, ×0.8 with LJ unchanged (§1.16). OPLS-VSIL must be another paper, not identified here |
| §5 summary: "no paper that refit pair-specific ion–solvent LJ against salt-solution densities" (carbonates) | survives; Ravikumar's pair terms are not density-fitted |

## 4. Answers to `ion-model/route-plan.md` §7

1. **ECC-R factors and targets; is a σ reduction near 5 % for a large anion precedented?**
   - The guide gives 5–10 % in radius for monatomic ions in water, fitted to neutron (NDIS) hydration structure (p. 050901-4).
   - Fan 2025 fits anion–water-O pair terms rather than one σ. Its anions have σ smaller than Madrid2019's by 0.5 Å on average (p. 9026),
     but that compares two scaled models, not a scaled model with its full-charge parent.
   - **No polyatomic anion and no carbonate solvent is among the precedents read.** A 5 % PF₆⁻ σ is inside the general rule's range, but
     transferring it is our extrapolation.
   - The precedent's target (neutron RDF of the ion) does not exist for PF₆⁻ in carbonates in what we have. The README's "density only, one
     target per parameter" weakness of route B stands.
2. **Doherty 2017:** no LJ term was refitted after the 0.8 scaling. Density, ΔH_vap, D, η, Cp and surface tension were *tested*, not fitted.
   Its result is a ≈ 3 % density loss of PF₆⁻ ILs on scaling (§1.16). The PF₆⁻ parameters themselves are in the missing PDF SI.
3. **Fan 2025:**
   - fits ζ and ion LJ (+ anion–O pairs) to NDIS structure, density and viscosity;
   - tests on water D (Yeh–Hummer-corrected), temperature of maximum density and contact-ion-pair numbers;
   - ζ = 0.81.
   - Because η is fitted, it is a precedent for the *form* of route A, not for its target set.
4. **Maiti 2023:** the polarizable force field is APPLE&P. ρ(c) appears only as ESI Fig. S2, with no numbers printed (digitizing would
   give them with a reading error).
5. **Borodin & Smith 2009:**
   - no ρ(c) of the electrolyte against experiment, only the 1 M densities of Table 7;
   - Li–O(carbonyl) first peak 1.98 Å, compared by the authors with 2.04 Å from neutron diffraction on PC/LiPF₆ (p. 1769).
6. **Nyman 2008 and the Landesfeind SI, curvature of V_φ(c):** neither resolves it.
   - Nyman reports constant partial molar volumes over 0–2 M (no densities).
   - The Landesfeind SI's 16 points sit at 0, 1, 2 and 3 M and scatter by 0.0066 g/cm³ around the plane (`landesfeind-density/README.md`).
   - **The only curved data in hand are Gruber's ternary ones** (line minus data +0.31 % at 0.25 M, +0.35 % at 3 M, −0.40 % at 2 M;
     ours). They are a different solvent.
7. **Kameda 2007 and Self 2024 in the original:** neither PDF is in `../Lit`.
   - Kameda's 2.04 Å is now read in a secondary source (Borodin 2009 p. 1769), still not in the original.
   - Self 2024 is in the ledger (`self2024_drs_free_ec`, VoR, checked in an earlier session).
   - **New structural cross-checks** (ledger):
     - Uchida's corrected Raman: EC 1.73 per Li⁺ at x_EC 0.355 in EC:DMC;
     - Morita's uncorrected Raman: EC 3.0 per Li⁺ in EC:DMC 1:1 vol, an upper bound;
     - model Li–O peaks 1.94–2.05 Å in four force fields (context only: Maiti ESI p. 5, Ravikumar Fig. 5, Dajnowicz p. 6277).

## 5. Missing papers for the author to download

| priority | paper | why |
|---|---|---|
| 1 | E. R. Logan et al., J. Electrochem. Soc. **165**, A21 (2018), doi 10.1149/2.0271802jes (open access) | the EC:EMC 3:7 η tables; resolves the 8 % between our two readings |
| 1 | C. Capiglia et al., J. Power Sources **81–82**, 859 (1999) | pfg-NMR D of ⁷Li and ¹⁹F in LiPF₆ EC:EMC 2:8 (via Nyman 2008); the closest measured D |
| 1 | I.-C. Yeh, G. Hummer, J. Phys. Chem. B **108**, 15873 (2004), doi 10.1021/jp0477147 | V-2's correction |
| 1 | S. H. Jamali, R. Hartkamp, C. Bardas, J. Söhl, T. J. H. Vlugt, O. A. Moultos, J. Chem. Theory Comput. **14**, 5959 (2018) | η from the finite-size effect of D (V-2's method; Lehnert ref. 101) |
| 1 | O. Borodin, G. D. Smith, J. Phys. Chem. B **110**, 6279 (2006) | the carbonyl-carbon LJ type refitted to carbonate liquid thermodynamics (SC-7 precedent) |
| 2 | S. A. Krachkovskiy et al., J. Electrochem. Soc. **164**, A912 (2017) (Landesfeind ref. 35) | pfg-NMR, EC:DMC 1:1 |
| 2 | Z. Feng, K. Higa, K. S. Han, V. Srinivasan, J. Electrochem. Soc. **164**, A2434 (2017) (Landesfeind ref. 29) | pfg-NMR, EC:DEC 1:1 |
| 2 | K. Hayamizu, J. Chem. Eng. Data **57**, 2012 (2012) | pfg-NMR D(T) of LiPF₆ in EC, PC, DEC, EC:DEC (cited by Landesfeind, Hou, Dajnowicz) |
| 2 | K. Hayamizu et al., J. Phys. Chem. B **103**, 519 (1999) | pure-solvent D and η used by Borodin and Dajnowicz |
| 2 | Y. Shao, K. Shigenobu, M. Watanabe, C. Zhang, J. Phys. Chem. B **124**, 4774 (2020), doi 10.1021/acs.jpcb.0c02544 | box-size dependence of the Nernst–Einstein deviation (Jo §1) |
| 2 | M. P. Eastwood et al., J. Chem. Theory Comput. **6**, 2045 (2010), doi 10.1021/ct9002916 | integrator bias of the kinetic temperature (V-3); **citation as given by Jo, "from memory", not verified** |
| 2 | M. Kohagen, P. E. Mason, P. Jungwirth, J. Phys. Chem. B **120**, 1454 (2016) (citation confirmed in the 2020 guide's reference list) | ECC-R factors for NaCl |
| 2 | Y. Kameda et al., J. Phys. Chem. B **111**, 6104 (2007) | Li–O 2.04 Å (neutron, PC/LiPF₆), structural target |
| 2 | E. J. Maginn et al., Living J. Comput. Mol. Sci. **1**, 6324 (2019) (Dajnowicz ref. 74) | best practices for D and η from equilibrium MD (V-1, V-2) |
| 2 | B. Hess, J. Chem. Phys. **116**, 209 (2002) (Lehnert ref. 103, Maiti ref. 56) | shear viscosity from MD, including periodic perturbation (a V-1 alternative) |
| 3 | T. Goldberg, V. Herdegen, A. S. Braeuer, J. Chem. Eng. Data **71**, 4756 (2026), doi 10.1021/acs.jced.6c00429 | EMC vapour pressure (SC-7) |
| 3 | H. Y. Oh, J.-E. Gu, S.-J. Park, Fluid Phase Equilib. (2018), doi 10.1016/j.fluid.2018.05.033 | EMC density (SC-7); ledger entry read via ThermoML only |
| 3 | E. R. Logan et al., J. Electrochem. Soc. **165**, A705 (2018) (Maiti ref. 59) | low-EC and EC-free viscosities |
| 3 | Dajnowicz 2022 SI; Doherty 2017 SI (PDF, Tables S3–S5) | OPLS4 per-solvent η, ΔH_vap and box tests; the OPLS-2009IL PF₆⁻ parameters |
| 3 | J. Self, N. T. Hahn, K. A. Persson 2024 (PDF) and D. Kostal, P. Jungwirth, H. Martinez-Seara, J. Phys. Chem. Lett. **14**, 8691 (2023) | to reread the DRS target and the short-range ζ in the original |
| 3 | N. Kumar, J. M. Seminario, J. Phys. Chem. C **120**, 16322 (2016); A. J. Ringsby et al., J. Electrochem. Soc. **168**, 080501 (2021) | Li⁺ pair terms in EC; the ζ = 0.8 model behind Lehnert's 1 M box |
| 3 | B. Dünweg, K. Kremer, J. Chem. Phys. **99**, 6983 (1993) (Borodin ref. 68) | the original finite-size result |

- **Already in `../Lit`, so not missing:** Duboué-Dijon 2020 (`050901_1_5.0017775.pdf`).
- **Downloads failed in this session:** automated downloads were blocked here (the permission system refused an open-access fetch), so
  nothing was fetched from the web.

## 6. Suggested file names (for the author; nothing renamed)

- `050901_1_5.0017775.pdf` → `Duboue-Dijon_2020_J._Chem._Phys._153_050901.pdf`
- `ms_r1-corr.pdf` → `MendesDeOliveira_2020_Phys._Chem._Chem._Phys._AM_hal-02964203.pdf` (author manuscript; doi 10.1039/D0CP02987D)

## 7. Ledger entries added by V-5 (all in `docs/research/summary/literature.json`)

| id | version read | checked against VoR |
|---|---|---|
| `logan2018a21_eta_ec_emc_3_7` | **not read here**: an earlier agent's transcription of the A21 PDF | **no** |
| `lehnert2025_table_s8_eta_fit_logan` | VoR SI | yes |
| `gruber2026_si1_eta_rho_ec_dmc_emc_vc` | authors' SI CSV (sha256 8c1318676a5252fd) + VoR | yes |
| `bergstrom2021_table1_ec_emc_3_7_30C` | VoR | yes |
| `nyman2008_partial_molar_volumes_ec_emc` | VoR | yes |
| `nyman2008_kappa_eq22_ec_emc_25C` | VoR | yes |
| `uchida2021_si_lipf6_ec_dmc_1molal` | VoR ESI | yes |
| `uchida2021_table_s7_raman_solvation` | VoR ESI | yes |
| `borodin2009_table6_ec_dmc_pure` | VoR | yes |
| `maiti2023_esi_table2_eta_applep` | VoR ESI | yes |
| `hou2021_table_s4_kappa_gen2` | VoR ESI | yes |
| `hou2021_quoted_solvent_viscosities` | VoR (secondary quotation) | yes, of the quotation |
| `ravikumar2018_box_size_d` | VoR SI | yes |
| `su2019_table_s7_dosy_ec_emc` | VoR ESI | yes |
| `morita1998_table2_raman_solvation` | VoR | yes |
