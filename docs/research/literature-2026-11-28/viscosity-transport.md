# Viscosity, diffusion, density, conductivity: measured values and other groups' transport MD

- **Early output of task V-5** (agent "literature", 2026-11-28), for V-1 (Green–Kubo η) and V-2 (box-size series).
  The full per-paper note is [README.md](README.md).
- **Every published number** has a ledger id in `docs/research/summary/literature.json` (publication.md rule 3) with
  table or page and the version read.
- **"Ours"** marks our own arithmetic. It comes from [derived.py](derived.py) → `derived.json`, which reads only the ledger.
- **Units** as printed: 1 cP = 1 mPa s; D in 10⁻¹⁰ m²/s unless stated.

## 1. Bottom line for V-1 and V-2

1. **The target η at 1 M, 20 °C is about 3.0–3.3 mPa s, and it is uncertain by about 10 %.**
   - Logan's EC:EMC 3:7 at 1.0 mol/kg (≈ 1.04 M): 3.05 cP, as transcribed by an earlier agent (`logan2018a21_eta_ec_emc_3_7`, not re-read).
   - Lehnert's Arrhenius fit of the same Logan data: 3.30 cP (`lehnert2025_table_s8_eta_fit_logan`, ours).
   - Gruber's EC:DMC:EMC + VC: 3.16 mPa s. It is a different solvent, so it gives a band only (`gruber2026_si1_eta_rho_ec_dmc_emc_vc`).
   - Bergstrom at 30 °C is 3.04, against 2.47 (Logan) and 2.66 (fit) (`bergstrom2021_table1_ec_emc_3_7_30C`).
   - So two labs disagree by 15–25 % on the same electrolyte.
   - **The 25 % margin of T4's decision rule is therefore about the size of the experimental spread.** A model η within about ±10 % of
     3.1 cannot be called wrong.
2. **Pure solvents:**
   - EMC 0.65 cP at 25 °C, quoted twice from secondary sources, never from a measurement we read;
   - EC:EMC 3:7 without salt: 1.11 cP at 20 °C (Logan, transcribed);
   - DMC 0.57 (Uchida) and 0.59 cP (Hayamizu, via Borodin) at 25 °C;
   - EC 1.85 cP at 40 °C (Hayamizu, via Borodin).
   These are the η(EMC) and η(solvent) checks for V-1.
3. **No measured self-diffusion coefficient (pfg-NMR) of LiPF₆ in EC:EMC 3:7 is in `../Lit`.**
   - The nearest is Uchida 2021: 1 mol/kg LiPF₆ in EC:DMC at 25 °C. At x_EC = 0.355: D(Li⁺) 2.25, D(PF₆⁻) 3.17, D(EC) 4.22, D(DMC) 5.74,
     with η 3.26 mPa s (`uchida2021_si_lipf6_ec_dmc_1molal`).
   - For scale, our M1 box at 20 °C (uncorrected, 26 Nov summary) gives D(Li⁺) 0.54 and D(PF₆⁻) 0.76, in the same units.
   - That is a factor of about 4. The solvent, the temperature and the box differ, so this is an orientation, not a test.
   - The EC:EMC sources are on the missing list (§6).
4. **Finite-size practice is split.**
   - Borodin 2009 applies Yeh–Hummer (Dünweg–Kremer) with the **model's own** η: +10 to +16 % on D. Dajnowicz 2022 corrects its small ML
     boxes the same way.
   - Lehnert 2025, Hou 2021, Maiti 2023 and Ravikumar 2018 do not correct.
   - Two papers "test" box size by doubling the volume and see no change: Ravikumar < 2 % without error bars; Borodin < 10 %.
   - But doubling the volume changes L by only 1.26, and the correction by 21 % of itself (ours). Neither test can see the correction.
   - **For V-2: use a factor ≥ 2 in L, not in volume.** A box with 8× the atoms of ours is about 56 000 atoms.
5. **Green–Kubo or Einstein η in practice** (V-1):
   - Maiti averages all six independent traceless components (Pxy, Pxz, Pyz and three diagonal differences).
   - Maiti finds the result **independent of the pressure-tensor output interval below 12 fs** and dependent on it above (ESI Fig. S8).
   - Borodin's Einstein form uses the same symmetrized traceless tensor, with weight 4/3 on the diagonal.
   - Borodin trusts collective correlation functions only up to about **1–2 % of the run length**.
   - Dajnowicz (OPLS4 test): 1 ns of NVT is enough for the salt-free solvent but **10 ns is needed at 2 mol/kg**; viscosity **rises in boxes below
     about 2000 atoms** at high η.

## 2. Measured viscosity

| system | T | η | how measured | ledger id |
|---|---|---|---|---|
| LiPF₆ EC:EMC 3:7 w:w, 0 m | 10/20/30/40 °C | 1.30/1.11/0.97/0.87 cP | Ostwald, ±2 % | `logan2018a21_eta_ec_emc_3_7` (transcribed by an agent, PDF not in ../Lit, **unchecked**) |
| same, 1.0 m (≈ 1.04 M) | 10/20/30/40 °C | 3.88/3.05/2.47/2.06 cP | same | same |
| same, Lehnert's Arrhenius fit of Logan | 1.0 m, 10/20/25/30/40 °C | 4.17/3.30/2.96/2.66/2.16 cP (ours, from η₀, E_a) | fit, SI Table S8 | `lehnert2025_table_s8_eta_fit_logan` |
| same fit, 0.5 / 1.5 / 2.0 m | 20 °C | 1.90 / 6.36 / 11.6 cP (ours) | fit | same |
| LiPF₆ EC:EMC 3:7 w:w | 30 °C; 0.051/0.101/0.50/1.001/1.50 m | 1.21/1.33/1.97/3.04/7.03 mPa s (±0.01–0.03) | EMS rotating, triplicate | `bergstrom2021_table1_ec_emc_3_7_30C` |
| LiPF₆ EC:DMC:EMC 30:35:35 vol + 1.5 wt % VC (**band, not 3:7**) | 20 °C; 0.25/0.5/1.0/1.5/2/3 M | 1.40/1.83/3.16/5.75/12.1/54.0 mPa s | Stabinger SVM 3001 (ASTM D7042) | `gruber2026_si1_eta_rho_ec_dmc_emc_vc` |
| same, 1 M | 10/20/25/30/40/50 °C | 4.02/3.16/2.83/2.56/2.12/1.79 mPa s; E_a = 16.1 kJ/mol at 15–25 °C (ours) | same | same |
| LiPF₆ 1 mol/kg EC:DMC, x_EC 0 / 0.248 / 0.355 / 0.476 | 25 °C | 1.60 / 2.68 / 3.26 / 4.19 mPa s | cone-plate | `uchida2021_si_lipf6_ec_dmc_1molal` |
| pure EMC | 25 °C | 0.65 cP | quoted by Logan (from Barthel & Gores) and by Hou 2021 p. 14747 (refs. 73–74 there) | `logan2018a21_eta_ec_emc_3_7`, `hou2021_quoted_solvent_viscosities` |
| pure DMC | 25 °C | 0.57 mPa s (Uchida); 0.59 cP (Hayamizu 1999 via Borodin) | cone-plate; — | `uchida2021_si_lipf6_ec_dmc_1molal`, `borodin2009_table6_ec_dmc_pure` |
| pure EC | 40 °C | 1.85 cP (Hayamizu 1999 via Borodin) | — | `borodin2009_table6_ec_dmc_pure` |

- **The two readings of Logan differ by 5–8 % at every temperature** (ours: Lehnert's fit over the transcribed 1.0 m values is +7.5, +8.3, +7.5 and
  +5.0 % at 10, 20, 30 and 40 °C).
  - An Arrhenius fit of the four transcribed values would not be off by 8 % at all points.
  - So either the transcription or Lehnert's digitizing is off.
  - **Read Logan A21 Tables II–V** (missing paper 1) before a model η is judged at the 10 % level.
- **The activation energy of η at 1 M is about 16 kJ/mol** in all three sources: Gruber 16.1 (ours), Lehnert's fit of Logan 16.1. Use it to move
  V-1's 25 °C result to 20 °C if needed.
- **At 3 M and 20 °C, η is 17 times the 1 M value** (Gruber; ours). A 3 M Green–Kubo run is far more expensive than 1 M.

## 3. Measured self-diffusion (pfg-NMR / DOSY)

| system | T | D(Li⁺) | D(anion) | D(solvent) | ledger id |
|---|---|---|---|---|---|
| 1 mol/kg LiPF₆ in DMC (x_EC 0) | 25 °C | 3.76 | 4.43 | DMC 9.42 | `uchida2021_si_lipf6_ec_dmc_1molal` (ESI Table S IV) |
| same, x_EC 0.248 / 0.355 / 0.476 | 25 °C | 2.58 / 2.25 / 1.85 | 3.49 / 3.17 / 2.76 | EC 5.00 / 4.22 / 3.83; DMC 6.56 / 5.74 / 4.64 | same |
| pure DMC; EC:DMC x_EC 0.356 | 25 °C | — | — | 24.8; EC 13.8, DMC 15.4 | same |
| LiPF₆:EC:EMC 1:4:4 molar (with toluene, T not stated, ≈ 1.4 M by our estimate) | ? | 1.33 | — | EC 1.97, EMC 2.37 | `su2019_table_s7_dosy_ec_emc` (not a target) |
| pure DMC (303 K), EC (313 K) | — | — | — | 26; 8 | `borodin2009_table6_ec_dmc_pure` (from Hayamizu 1999) |

- **Not in `../Lit`, but named in the papers read:**
  - Capiglia et al. 1999: ⁷Li and ¹⁹F pfg-NMR in LiPF₆ EC:EMC 2:8, cited by Nyman 2008. **This is the closest EC:EMC source.**
  - Hayamizu 2012: EC, PC, DEC and EC:DEC with LiPF₆, against T. Cited by Landesfeind (ref. 32), Hou and Dajnowicz.
  - Krachkovskiy 2017: EC:DMC 1:1. Landesfeind ref. 35.
  - Feng 2017: EC:DEC 1:1. Landesfeind ref. 29.
- **Salt (Fickian) diffusion, not self-diffusion:** Nyman 2008 Table 3 gives D̃_LiPF₆(c) for EC:EMC 3:7 at 25 °C.
  - At 1 M it evaluates to 1.77 × 10⁻¹⁰ m²/s (ours, from the printed polynomial; not in the ledger).
  - This is a different quantity from D_self. It would only enter through Maxwell–Stefan, not as a check on D.

## 4. Measured density and salt volume

| source | system | what | ledger id |
|---|---|---|---|
| Landesfeind 2019 (SI) | EC:EMC 3:7, 0–50 °C | ρ = 1.41 + 0.0912 c − 0.00109 T; already the reference | `landesfeind2019_density_fit_ec_emc_3_7` |
| Gruber 2026 (SI CSV) | EC:DMC:EMC + VC (band) | 20 °C: 1.1662 (0.25 M), 1.2349 (1 M), 1.3994 (3 M) g/cm³. Slopes 0.0916 (0.25–1 M), 0.0894 (1–2 M), 0.0804 (1.5–3 M) (ours) | `gruber2026_si1_eta_rho_ec_dmc_emc_vc` |
| Nyman 2008 | EC:EMC 3:7, 25 °C, 0–2 M | V̄(LiPF₆) = 59, V̄(solvent) = 87 cm³/mol, constant in c | `nyman2008_partial_molar_volumes_ec_emc` |
| Bergstrom 2021 | EC:EMC 3:7, 30 °C | pipette-weighed densities; **not usable**: −4.0 % to +2.4 % off Landesfeind's fit, slope 0.141 (ours) | `bergstrom2021_table1_ec_emc_3_7_30C` |
| Uchida 2021 | EC:DMC, 25 °C, two decimals | 1 mol/kg: 1.18 (x_EC 0) to 1.29 (0.476) | `uchida2021_si_lipf6_ec_dmc_1molal` |

- **Jo's section 6 is the published Gruber SI.** Its slopes and E_a reproduce from the CSV to the printed digits (ours).
  - The CSV has no 0 or 0.01 M row, so Jo's "0–1 M" slope is our 0.25–1 M one (0.0916).
- **Nyman's V̄(LiPF₆) = 59 cm³/mol** is a second measured salt volume for EC:EMC 3:7, next to Landesfeind's 55.7. Our model has 70.6 at 1 M.
  - Nyman's V̄(solvent) = 87 implies ρ₀ = 1.135 g/cm³ (ours, with M = 98.71 g/mol). That is 4.6 % above Landesfeind's 1.085 at 25 °C.
  - So the solvent volume is too coarse, or defined differently, to give ρ₀.
  - The implied slope dρ/dc = M − V̄ρ₀ is 0.085–0.088 (ours), against 0.0912.

## 5. How others ran transport MD of these electrolytes

| paper | model; ion charges | Δt; constraints | ensemble during transport | box | length | η method | finite size |
|---|---|---|---|---|---|---|---|
| Lehnert 2025 (SI S1.1) | OPLS (Maestro) EC/EMC, JJ06 Li⁺, CL&P PF₆⁻; ζ = 0.75 fitted to κ | 1 fs, velocity Verlet, no constraints stated | NVT, Nosé–Hoover (damping 100 fs; barostat 1000 fs in NPT) | 47 LiPF₆ + 168 EC + 332 EMC at 1 M (= ours) | 50–170 ns × 3 | **none computed**: Stokes–Einstein with a radius fitted to Logan's η (SI S1.9) | none; GK η and Jamali 2018 named as alternatives (main text, p. 6, viscosity paragraph) |
| Borodin 2009 | APPLE&P polarizable, QC-fitted, full charges | MTS 0.5/1.5/3.0 fs; SHAKE on all bonds except P–F | NVT (NPT for equilibration), Nosé–Hoover | 240–520 solvent + 18–49 LiPF₆ (ours, from Table 7 ratios); L ≈ 3.0–4.2 nm (ours) | 3–21 ns | Einstein, symmetrized traceless tensor, all components | **Yeh–Hummer with model η: +10 to +16 %**; ions scaled by the solvent's factor (1.11–1.17) |
| Maiti 2023 | OPLS-AA, OPLS-AA × 0.8 (ions), APPLE&P | OPLS: 2 fs, LINCS on H bonds; APPLE&P: MTS 0.5/1.5/3 fs, SHAKE all bonds | **NPT throughout** (Nosé–Hoover 0.5 ps + Parrinello–Rahman 2 ps; APPLE&P NH chains) | not found in the ESI text | OPLS "1 ms" as printed (p. 20352; probably 1 µs); APPLE&P 100 ns | Einstein, six components; output ≤ 12 fs | none |
| Hou 2021 | OPLS-AA, RESP charges, full ion charges | not stated | NVT, Nosé–Hoover 1 ps | 504 EC + 996 EMC + 166 LiPF₆ (1.2 M); L ≈ 6.2 nm (ours) | 60 ns × 4 independent | none | none |
| Ravikumar 2018 | CFF93 + Soetens EC, pair-specific LJ (Li–O, F–H, F–C), full charges; EC only, 330 K | 1 fs | **NVE** production after NPT and NVT | 220 EC + 17 LiPF₆ (L ≈ 2.9 nm); check at 440 + 34 | 30 ns × ≥ 3 | none | "box size independent" from a 2 % change at 2× volume |
| Dajnowicz 2022 | QRNN ML potential; OPLS4 benchmark | QRNN 0.5 fs; OPLS4 in Desmond (settings in its SI, not in ../Lit) | NVT replicas, Nosé–Hoover 0.05 ps | QRNN ≈ 1000 atoms; OPLS4 8× | 20 × 1 ns (QRNN) | from MD; OPLS4 needs 10 ns at 2 m | QRNN D corrected for finite size; η grows below 2000 atoms at high η |

- **Thermostat during transport:**
  - Most groups use Nosé–Hoover in NVT; Maiti even uses NPT.
  - Nobody reports a check of D or η against an NVE run. Ravikumar runs NVE but does not compare.
  - Our planned NVE check (V-3) has no published counterpart for these electrolytes.
- **Time step:** Lehnert 1 fs flexible (our protocol); Maiti 2 fs with H constraints; the polarizable and ML models 0.5 fs (inner).
  - Nobody reports a Δt test of transport. The "time-step bias" candidate of 26 Nov §6, item 5, survives.
- **Other models are too slow or too viscous as well:**
  - Dajnowicz: OPLS4 "systematically overestimates the experimental viscosities" of all pure carbonates (RMSE about 1.06 cP) and underestimates D.
  - Dajnowicz: the RMSE of OPLS4 ΔH_vap is 9.15 kJ/mol against 3.23 for the ML model (p. 6275).
  - Maiti: non-polarizable variants have "largely underestimated" dynamics; at 0.95 M, η(OPLS) > η(OPLS × 0.8) > η(APPLE&P) (Fig. 5a).
  - Hou: the OPLS-AA force field "underestimates the diffusivity" (p. 14747). Hou's EC ΔH_vap is 62.4 kJ/mol at 313 K against 60.3 (at 383 K).
  - By contrast, the polarizable APPLE&P is slightly **too fluid** for pure DMC (η 0.47 against 0.59 cP) and right on its ΔH_vap (8.88 against
    9.01 kcal/mol). A 30 % excess as in our EMC is not seen there.

## 6. Missing papers that V-1 and V-2 would use (full list in README §missing)

1. Logan et al., J. Electrochem. Soc. 165, A21 (2018), doi 10.1149/2.0271802jes: the viscosity tables (open access).
2. Logan et al., J. Electrochem. Soc. 165, A705 (2018): EC-free and low-EC EC:EMC viscosities (Maiti's ref. 59).
3. Yeh & Hummer, J. Phys. Chem. B 108, 15873 (2004); Dünweg & Kremer, J. Chem. Phys. 99, 6983 (1993) (Borodin's ref. 68).
4. Jamali et al., J. Chem. Theory Comput. 14, 5959 (2018): η from the finite-size effect of D (Lehnert's ref. 101). This is V-2's method,
   and it is the "Jamali et al." that `ion-model/README.md` §2.4 could not identify.
5. Maginn et al., Living J. Comput. Mol. Sci. 1, 6324 (2019): best practices for D and η from equilibrium MD (Dajnowicz ref. 74).
6. Hess, J. Chem. Phys. 116, 209 (2002): shear viscosity from MD (Lehnert ref. 103, Maiti ref. 56).
7. pfg-NMR: Capiglia et al., J. Power Sources 81–82, 859 (1999); Hayamizu, J. Chem. Eng. Data 57, 2012 (2012); Krachkovskiy et al.,
   J. Electrochem. Soc. 164, A912 (2017); Feng et al., J. Electrochem. Soc. 164, A2434 (2017).
8. Dajnowicz 2022 SI (OPLS4 Tables S2–S5, box and run-length tests, Figs. S7–S8).
