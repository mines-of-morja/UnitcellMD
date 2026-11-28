# Ion model for LiPF₆ in EC:EMC: which interactions set both the volume and the dynamics?

> **Agent note, unchecked (2026-11-27).** Written by a literature agent for unitcellmd-c8; copied unchanged. Values marked DB,
> SNIPPET or derived are not ledger values. Nothing here is used before it is read in the original and entered in the ledger.

- **Date:** 2026-11-27. Literature research for the question "figure out what describes the interactions well that we need".
- **Scope:** the measured apparent molar volume of LiPF₆ in carbonates; how other groups' force fields do on ρ(c); the physics
  of electrostriction under charge scaling (ECC, ECC-R); pair-specific ion–solvent terms; ranked routes for us.
- **How each number is marked:**
  - **[read]** I read it in the original paper during this session (full text or the relevant section).
  - **[abstract]** Only the abstract or a database record was available.
  - **[repo]** Taken from this repo's notes. I did not re-read the original.
  - **[ours]** Our own calculation from cited numbers. The arithmetic is given.
  - **[unverified]** From general knowledge and not checked in this session. These items carry no numbers and must be read before anyone uses them.
- **Not available in this session:** ACS (J. Phys. Chem. B/C, JCTC) and RSC full texts were blocked or paywalled. Several key
  force-field papers are therefore marked [abstract] or [unverified].

---

## 0. Bottom line

1. **The measured V_φ of LiPF₆ in the solvents nearest to EC:EMC is 38–60 cm³/mol. It depends on the solvent and only weakly on c.**
   The model's 70.6 (1 M) and 72.3 (3 M) are about 15–17 cm³/mol too large, against Landesfeind's 55.7 at 20 °C.
2. **The same slope deficit is built into Lehnert 2025's boxes.** Their ion counts were tuned until the simulated c matched the
   target at 20 °C. The implied densities give dρ/dc ≈ 0.073–0.076 g cm⁻³ M⁻¹, and 3 M lands at −2.0 %, the same as ours (§2).
   Lehnert's solvents are Maestro OPLS, ours are Caleman EC and LigParGen EMC. The deficit is therefore a property of the
   **ion model (JJ06 Li⁺ + CL&P PF₆⁻ at ζ = 0.75)**, not of the solvent.
3. **Charge scaling alone cannot fix it.** Our dV_φ/dζ falls from −74 (1 M) to −45 cm³/mol (3 M). At 3 M even ζ = 1
   extrapolates to about 61 cm³/mol, still above 55.7 [ours]. So part of the excess volume is not "missing electrostriction" but
   **ion size and packing**: the short-range repulsion of the ions, especially PF₆⁻, and the ion–solvent and ion–ion contact distances.
4. **The physics agrees.**
   - The ion LJ parameters (JJ06 in TIP4P water; CL&P PF₆⁻ in ionic liquids) were fitted with **full** charges, so the full
     Coulomb attraction compressed the contacts.
   - Scaling the charges by 0.75 without refitting the LJ makes the ions effectively larger.
   - This is the stated reason for ECC-R's reduced σ (Jungwirth group) and for refitting ion–water LJ in Madrid-2019.
   - In Madrid-2019, changing the ion charge from 0.85 to 1 with the LJ fixed changes the melt and solid density by about 20 % and 8 % [read].
5. **Dynamics.**
   - Lowering the charges lowers the density and speeds up the dynamics (Maiti 2023, SI statement) [abstract].
   - Polarizable models fix the dynamics and the Li⁺ shell together (Maiti 2023) [abstract].
   - A fixed-charge model that is repaired for density may move κ the wrong way. If it does, that points to many-body polarization as the missing physics.
6. **Ranking (§7):**
   - **A:** ECC plus pair-specific LJ (NBFIX) fitted to solution densities in several solvents plus structure and QM. This is the Madrid-2019 recipe, and spec 0.1.2 can already carry it.
   - **B:** ECC-R, a single rescaled PF₆⁻ (and Li⁺) σ, as the cheap first step of A.
   - **C:** an explicit polarizable model (Drude, CL&Pol type, or APPLE&P). This means spec changes and bridge work.

---

## 1. Measured densities and molar volumes of LiPF₆ in carbonates

### 1.1 Formulas used here

- **Apparent molar volume:** V_φ = [M_e − 1000 (ρ − ρ₀)/c] / ρ₀ (cm³/mol; ρ in g/cm³; c in mol/L).
- **Partial molar volume:** V̄_e = (M_e − dρ/dc) / (ρ − c dρ/dc), with ρ in g/L (Newman).
- **M(LiPF₆):** 151.905 g/mol (as used by Wang 2020).

### 1.2 Table

| System | T | Correlation, as printed | V_φ / V̄_e (cm³/mol) | Mark |
|---|---|---|---|---|
| **LiPF₆ in EC:EMC 3:7 (w:w)**, Landesfeind & Gasteiger, *J. Electrochem. Soc.* 166, A3079 (2019), doi:10.1149/2.0571912jes, SI Eq. S1, Table S1 | 10–50 °C, 0–3 M | ρ = 1.41 + 0.0912 c − 0.00109 T (g/cm³, M, K) | Linear in c, so V_φ = V̄_e = (151.905 − 91.2)/ρ₀: **55.7 (20 °C), 55.9 (25 °C)**. It is c-independent by construction, so the fit cannot resolve curvature. | fit [repo, read twice in SC-8]; V_φ [ours] |
| **LiPF₆ in EMC**, Wang, Hou, Karanjavala, Monroe, *Electrochim. Acta* 358, 136688 (2020), doi:10.1016/j.electacta.2020.136688 (accepted manuscript, ORA, CC BY-NC-ND), Table 2 | 20 / 25 / 30 °C, 0–2 M | ρ = 1013.1 + 113.19 c − 7.8842 c^{3/2} (20 °C); 1007.1 + 114.20 c − 8.1212 c^{3/2} (25 °C); 1001.1 + 115.13 c − 8.3005 c^{3/2} (30 °C) (g/L) | 20 °C: V_φ(c→0) = **38.2**, V_φ(1 M) = **46.0**, V_φ(2 M) = **49.2**; V̄_e(1 M) = 49.7, V̄_e(2 M) = 54.1. 25 °C: V_φ(c→0) = 37.4, V_φ(1 M) = 45.5. The text says V̄_e rises about 33.5 % over 0–2.2 M and V̄_solvent falls about 1 %. | correlation and text [read]; V values [ours] |
| **LiPF₆ in PC**, Hou & Monroe, *Electrochim. Acta* 332, 135085 (2020), doi:10.1016/j.electacta.2019.135085 (CC BY), Table 1 | 20 / 25 / 30 °C, 0.2–2.1 M | ρ = ρ₀ + ρ₁c + ρ₂c^{3/2}. 20 °C: 1205.03, 84.578, 2.699; 25 °C: 1199.73, 84.972, 2.760; 30 °C: 1194.43, 85.369, 2.823. The PDF text lost the minus signs. ρ₂ must be **negative**, because the text says V̄_e rises about 5 mL/mol (9 %) from 0.5 to 2.1 M, and that only follows with ρ₂ < 0. | 20 °C: V_φ(c→0) = **55.9**, V_φ(1 M) = **58.1**, V_φ(2 M) = **59.0**; V̄_e(1 M) = 59.2 | table [read], sign [ours, inferred]; V values [ours] |
| **LiPF₆ in EC:DEC 1:1 (w:w)**, Lundgren, Behm, Lindbergh, *J. Electrochem. Soc.* 162, A413 (2015), doi:10.1149/2.0641503jes | 10 / 25 / 40 °C | — | V̄_e = 57.0 / 56.8 / 56.5 | [repo: docs/design/A1.5.md] |
| **LiPF₆ in PC**, standard state, Marcus & Hefter, *Chem. Rev.* 104, 3405 (2004), doi:10.1021/cr030047d, Table 14 | footnote d: 40 °C (table head: 25 °C) | — | V°(LiPF₆) = **62.4** (one source, unconfirmed). For comparison: LiClO₄ 37.1, LiAsF₆ 63.6, LiBF₄ 35.5 | [read] |
| **Single ions in PC**, Marcus & Hefter Table 15, TPTB convention, 25 °C, ±2 | | — | V°(Li⁺) = **−9**; V°(PF₆⁻) = **72** (derived from LiPF₆); V°(AsF₆⁻) = 72 | [read] |
| **LiPF₆ in EC**, Marcus & Hefter Table 12 | 40 °C | — | 14.6, called "probably a misprint". Li⁺ in EC: 5 (N-extrapolation, "not considered reliable") | [read] |
| **LiClO₄ in DMC**, Marcus & Hefter Table 38 | 25 °C | — | 26 (no LiPF₆ value for DMC) | [read] |
| Intrinsic volumes, Marcus & Hefter Table 40 | — | — | V_int(Li⁺) = 1.1 (r = 0.069 nm); V_int(AsF₆⁻) = 68.3 (r = 0.243 nm). PF₆⁻ is not listed. | [read] |

- **Not found or not read:**
  - Nyman, Behm, Lindbergh, *Electrochim. Acta* 53, 6356 (2008), doi:10.1016/j.electacta.2008.04.023: LiPF₆ in EC:EMC 3:7, 25 °C, 0.2–2 M. The density part was not obtained in this session.
  - Valøen & Reimers 2005, doi:10.1149/1.1872737 (PC:EC:DMC): not read.
  - Stewart & Newman 2008, doi:10.1149/1.2904526: not read.
  - Logan et al. 2018 (doi:10.1149/2.0471814jes, in `../Lit`) has no density data (grep of the full text) [read].
  - Gruber et al. 2026 (doi:10.1149/1945-7111/ae7d5b, in `../Lit`, EC:DMC:EMC 30:35:35 v/v + 1.5 wt % VC, 0.25–3 M, −20 to 60 °C) shows ρ(c,T) only as a figure (Fig. 1c). The SI might tabulate it [read; SI not read].

### 1.3 What the data say about the physics

- **Linear EMC is more compressible.**
  - In pure EMC the salt's limiting V_φ is about 38 cm³/mol, much lower than in PC (about 56). Strong electrostriction in a compressible, low-ε solvent is one reading. Ion pairing is the other: in EMC, ion association dominates even at high dilution (Wang 2020 abstract [read]).
  - V_φ in EMC then rises steeply with c, by about 11 cm³/mol from 0 to 2 M. Electrostriction is lost as the ions share solvent and pair up.
- **In PC the salt is nearly ideal-additive.** V_φ is 56–59 and changes by only about 3 cm³/mol over 0–2 M.
- **EC:EMC 3:7 sits at the PC end.** Its V_φ is 55.7, although 70 % of the solvent mass is EMC. This fits a Li⁺ shell enriched in
  cyclic carbonate: Self et al. 2024 DRS gives about 2 EC per Li⁺ at 1 M [repo]. This is our reading, a hypothesis.
- **Single-ion split (Marcus & Hefter, TPTB).**
  - Li⁺ has a negative V° (−9 in PC). Its electrostriction outweighs its intrinsic volume of 1.1.
  - PF₆⁻ has V° ≈ 72, close to the intrinsic volume of the isoelectronic-size AsF₆⁻ (68.3), so its electrostriction is small.
  - Marcus & Hefter §6.1.3 [read]: "Anions with r ≥ 0.18 nm … have relatively large V_int values but small (negative) V_el values"; for
    small univalent ions "the sum of the electrostrictive volume, V_el, and the intrinsic volume, V_int, adequately accounts for" V°.
- **Consequence for the model.** With these numbers, V° of LiPF₆ ≈ V_int(PF₆⁻) + V_el(Li⁺) + small terms:
  - the anion's **size** carries most of the salt volume;
  - Li⁺'s **electrostriction** subtracts about 10 cm³/mol.

---

## 2. The model against the data, and what Lehnert's boxes imply

### 2.1 Our model (coordinator's measured values)

- V_φ at 20 °C: 70.6 (1 M) and 72.3 (3 M), against 55.7.
- dV_φ/dζ: −74 (1 M) and −45 (3 M).
- Linear extrapolation to ζ = 1: 1 M ≈ 70.6 − 0.25·74 = **52.1**; 3 M ≈ 72.3 − 0.25·45 = **61.1** [ours]. So:
  - At 1 M, full charges would roughly close the gap.
  - At 3 M they would not.
  - The ζ needed grows with c. That is the signature of a ζ-independent excess, ion size or packing, that is hidden at low c
    by the charge-dependent electrostriction.

### 2.2 Crude electrostriction bookkeeping [ours, an order-of-magnitude argument]

- **Assumption:** Drude–Nernst form, V_el = −B z²/r (Marcus & Hefter Eq. 38 [read]), with z → ζ. This ignores dielectric saturation.
- **Model's electrostriction:** V_el ∝ ζ² gives V_el(ζ = 0.75) ≈ ζ/2 · dV_φ/dζ = −28 cm³/mol at 1 M. With saturation the true exponent is
  below 2, and |V_el| would be larger still.
- **Model's intrinsic part:** V_φ − V_el ≈ 70.6 + 28 ≈ **99 cm³/mol**.
- **Experimental intrinsic part:** about 70 (V_int(AsF₆⁻) 68.3 + V_int(Li⁺) 1.1 as a proxy; PF₆⁻ is not listed).
- **Reading:** if this holds, the model's ions plus their first-shell packing take about 30 cm³/mol too much. The model's
  electrostriction looks too large rather than too small. Both numbers rest on the crude assumption, so they are only a pointer.
- **Test:** the pointer is testable. dV_φ/dσ(PF₆⁻ F) and dV_φ/dσ(Li–O) at fixed ζ would show it (§7).

### 2.3 Lehnert 2025 boxes [ours, from SI Table S1 [read]]

- **Input:** the SI says ion numbers were tuned "with varying ion numbers" until the simulated concentration matched the target at
  20 °C. The 1 M row was taken from Ringsby 2021, which used ζ = 0.8.
- **Implied density:** ρ = mass / (N_pairs / (N_A c)).

| c (M) | pairs | implied ρ (g/cm³) | Landesfeind fit at 20 °C | deviation |
|---|---|---|---|---|
| 0.1 | 9 | 1.1120 | 1.0996 | +1.1 % |
| 0.5 | 23 | 1.1489 | 1.1361 | +1.1 % |
| 1.0 | 47 | 1.2021 | 1.1817 | +1.7 % |
| 1.5 | 74 | 1.2283 | 1.2273 | +0.1 % |
| 2.0 | 103 | 1.2622 | 1.2729 | −0.8 % |
| 2.5 | 134 | 1.3006 | 1.3185 | −1.4 % |
| 3.0 | 168 | 1.3371 | 1.3641 | −2.0 % |

- **Slope:** dρ/dc = 0.0757 (all points) or 0.0726 g cm⁻³ M⁻¹ (0.5–3 M). Implied V_φ ≈ 68–71 cm³/mol.
- **Comparison with ours:** our 3 M point is 1.3365 (SC-4), Lehnert's implied 1.3371.
- **Caveats:**
  - The integer counts and the unknown tolerance of their "most consistent" match limit the precision, by about 1/N_pairs in c.
  - Lehnert's paper does not report densities. These numbers are inferred.
- **Reading:** the 20 % flat slope does not depend on the solvent parameters. It belongs to the JJ06/CL&P ions at ζ = 0.75.

### 2.4 Jamali et al.

- I could not identify a Jamali et al. paper on this system in the Lehnert author circle, nor one with ζ and LJ choices for LiPF₆/carbonates.
- The Lehnert 2025 author list is Lehnert, Lorenz, Juarez, Schammer, Nojabaee, Schönhoff, Horstmann (arXiv 2512.13225 [read]).
- If the author has a specific paper in mind, its DOI is needed.

---

## 3. Force-field families and the density over c

| Family | Example | What is known about ρ(c) | Transport | Mark |
|---|---|---|---|---|
| OPLS, ζ = 0.75–0.8, unmodified ion LJ | Lehnert 2025 (Maestro OPLS, JJ06, CL&P, ζ = 0.75, fitted to κ); Ringsby, *J. Electrochem. Soc.* 168, 080501 (2021), doi:10.1149/1945-7111/ac1735 (ζ = 0.8, "between 0.7 and 0.8" in the literature) | Lehnert's implied slope 0.073–0.076 (§2.3). Ringsby reports no density (full text grep). | Lehnert: κ fitted. Ringsby: D compared with experiment | [read] / [ours] |
| Same, ζ scanned | Maiti, Krishnamoorthy, Mabrouk, Mozhzhukhina, Matic, Diddens, Heuer, *Phys. Chem. Chem. Phys.* 25, 20350 (2023), doi:10.1039/d3cp01236k, LiPF₆ in EC/EMC | SI (snippet): "charge rescaling reduces the density, which explains faster dynamics"; the polarizable model gives "decent agreement with experiment". No numbers seen. | Non-polarizable variants "substantially underestimate the dynamics". The polarizable FF agrees much better for κ, t₊ and η "across a wide range of salt concentrations and EC:EMC ratios", and best with FTIR coordination. | [abstract]. Which polarizable FF was used is not read; must be checked. |
| Scaled solvent charges | Chaudhari, Nair, Pratt, Soto, Balbuena, Rempe, *J. Chem. Theory Comput.* 12, 5709 (2016), doi:10.1021/acs.jctc.6b00824 (OSTI 1339276) | Solvent densities computed. No ρ(c) of the salt. | They chose 80 % (EC) and 90 % (PC) solvent charges partly from **diffusion coefficients**: "the diffusion constants … in 80% charged EC and 90% charged PC come closest to the averaged experimental values". Under our rules transport was a fit target, so the scaling cannot be adopted. | [read] |
| Polarizable APPLE&P | Borodin & Smith, *J. Phys. Chem. B* 113, 1763 (2009) (LiPF₆ in EC:DMC); solvent set Borodin & Smith, *J. Phys. Chem. B* 110, 6279 (2006) | Density accuracy not read in this session | A review snippet says D and κ agree "well" with experiment, without numbers | [unverified]; read before use |
| Polarizable CL&Pol (Drude) | Goloviznina, Canongia Lopes, Costa Gomes, Pádua, *J. Chem. Theory Comput.* (2019), doi:10.1021/acs.jctc.9b00689; extension to electrolytes: Goloviznina, Gong, Costa Gomes, Pádua, ChemRxiv/HAL 2021 (journal version not verified) | Validated "through comparison with experimental data on density, viscosity, and ion diffusion coefficients". Tang–Toennies damping is needed for Li⁺. | Same | [abstract]. From memory, not checked: when Drudes are added, CL&Pol scales down the LJ ε of fragment pairs with a SAPT-based factor. This must be read before use. |
| ML potential, density-aligned | Gong et al. (BAMBOO), arXiv 2404.07181 v5 (2025), LiPF₆ carbonate electrolytes | "Density alignment" with 13 experimental densities: the MLFF is retrained to a pressure shift from the computed compressibility. Density error falls from about 0.05 to **0.01 g/cm³**. It transfers to unseen solvents and to salt concentrations up to 3.78 mol/kg, beyond the training maximum of 2.22. | After alignment: viscosity deviation 17 %, κ deviation 26 % (both as test). Alignment "also decreases errors in predictions of other properties beyond density, such as viscosity and ionic conductivity". | [read] main text; SI not read |
| Aqueous analogue: scaled charges + pair LJ refit | Zeron, Abascal, Vega, *J. Chem. Phys.* 151, 134504 (2019), doi:10.1063/1.5121392 (Madrid-2019), charges ±0.85 | Fit targets (§II): "Densities of the aqueous solution at moderate (around 1 molal) and high concentrations", "Position of the main peak of the ion-water radial distribution function and hydration numbers", and limited clustering near solubility. Lorentz–Berthelot only for like-sign ion pairs; explicit pair terms elsewhere. With fixed LJ, the melt and solid density "increases by about 20/8 per cent when the charge of the ions changes from 0.85 to 1". "we failed to reproduce simultaneously the densities of the melt and those of the solution." For LiCl, JC/TIP4P-Ew "predicts a much less steeper slope". | Viscosity and diffusion **not** fitted, evaluated as tests. "Viscosities are also described quite well for concentrations up to 3 m." | [read] (arXiv 2401.13164) |

**Gaps:**
- I found no carbonate paper that reports ρ(c) for scaled-charge OPLS against experiment over 0–3 M with numbers.
- Our SC-4 result and the Lehnert-implied table are the clearest such data I know of.
- Plausible candidates, not checked:
  - Hou, Fong, Wang, Persson, *Chem. Sci.* (2021);
  - Ravikumar, Mynam, Rai, *J. Phys. Chem. C* (2018);
  - Dajnowicz et al., *J. Phys. Chem. B* (2022) (NN potential, EC/EMC);
  - the Maiti 2023 SI.

---

## 4. Physics: why scaled charges change the volume, and what restores it

### 4.1 Electrostriction

- **Drude–Nernst** (Marcus & Hefter §6.1.2 [read]): V_el = −(N_A e²/8πε₀) z² r⁻¹ (∂ ln ε/∂P)/ε. The solvent is compressed by the ion's field,
  "∼40 GPa (400 kbar)" at the surface of Na⁺. The more realistic version includes dielectric saturation and a shell-by-shell
  integration over κ_T and ∂ ln ε/∂P (their Eq. 43).
- **Under ECC** the field from an ion of charge ζe is ζ times weaker, so a fixed-charge model's electrostriction shrinks roughly as ζ²
  (less with saturation).
- **Short-range repulsion.** The ion's own short-range repulsion was parameterized against full-charge attraction. Scaling the charge
  therefore also moves the ion–solvent contact distance outwards. Both effects enlarge V_φ.
- **Evidence for the second effect:** Zeron 2019's 20 %/8 % melt/solid density change at fixed LJ [read].

### 4.2 ECC

- **Sources:**
  - Leontyev & Stuchebrukhov, *Phys. Chem. Chem. Phys.* 13, 2613 (2011), doi:10.1039/c0cp01971b [read, abstract and key passages];
  - Kirby & Jungwirth, *J. Phys. Chem. Lett.* 10, 7531 (2019), doi:10.1021/acs.jpclett.9b02652 [read].
- **What ECC says:** ζ = 1/√ε_el.
  - Kirby & Jungwirth: "ions in solutions should have charges scaled by 1/√1.78 = 0.75".
  - LJ interactions "are unaffected by these considerations". So ECC itself gives no rule for LJ.
- **Where it fails** (Kirby & Jungwirth): non-polarizable models "cannot be expected to properly handle gradients or discontinuities of
  high-frequency permittivity". This applies to the Li⁺ first shell and to a low-ε EMC-rich medium.
- **Short-range ζ.** Kostal, Jungwirth, Martinez-Seara, *J. Phys. Chem. Lett.* 14, 8691 (2023), doi:10.1021/acs.jpclett.3c02231 [read via PMC]:
  - AIMD in a non-aqueous (argon-like, ε_el = 1.52) solvent gives fitted factors of 0.75–0.78 at large ion–ion separation;
  - and **0.78–0.83 at short separation**;
  - "slightly larger factors may be useful at short range".
- **prosECCo75** (Nencini et al., *J. Chem. Theory Comput.* 20, 7546 (2024), doi:10.1021/acs.jctc.4c00743 [read via PMC]):
  - "we do not modify the LJ σ values in prosECCo75, contrary to our previous ECC-lipids work";
  - new Br⁻ and I⁻ ions were fitted "using densities and structural data from neutron scattering";
  - AIMD suggests about 0.8 for short-range ion pairs.

### 4.3 ECC-R (rescaled σ)

- **Sources:**
  - Kohagen, Mason, Jungwirth, *J. Phys. Chem. B* 120, 1454 (2016), NaCl;
  - Martinek et al., *J. Chem. Phys.* 148, 222813 (2018), Ca²⁺;
  - Duboué-Dijon et al., *J. Phys. Chem. B* 122, 3296 (2018), Mg²⁺/Zn²⁺;
  - Duboué-Dijon, Javanainen, Delcroix, Jungwirth, Martinez-Seara, *J. Chem. Phys.* 153, 050901 (2020), the "practical guide".
- **Status:** cited in Kirby & Jungwirth [read]. The ECC-R papers themselves [unverified].
- **Method, from memory and not checked:** after scaling the charge, the ion σ is reduced until the ion–water RDF matches neutron
  scattering or AIMD. The reduction factors were not checked and must be read before use.
- **The physical reason** is the one in §4.1: the weaker attraction lets the shell drift out, and a smaller σ pulls it back.
- **Bruce & van der Vegt,** *J. Chem. Phys.* 148, 222816 (2018) ("Does an electronic continuum correction improve effective short-range
  ion–ion interactions?"): cited [read in refs], content [unverified].

### 4.4 Which parameter controls the ion–solvent volume?

The ranking below is our reasoning. It rests on Marcus & Hefter's decomposition and on our own scans.

1. **PF₆⁻ size: CL&P F σ and ε, and P–F 0.1606 nm.**
   - The anion's intrinsic volume is the largest term in V°(LiPF₆), about 70 of 56–62 cm³/mol.
   - CL&P PF₆⁻ was fitted in ionic liquids with full charges. At ζ = 0.75 its contacts with Li⁺ and with solvent H atoms are no longer compressed by full Coulomb.
   - This is the most likely place for a ζ-independent excess that grows with c (the 3 M result).
2. **Li⁺–O(carbonyl) and Li⁺–F contact distance and coordination number** (pair term).
   - Li⁺'s V° is negative (−9 in PC) because of electrostriction. Our Li⁺ σ scan had no effect on density. With JJ06's tiny ε
     (0.0005 kcal/mol, geometric mixing) the Li–O repulsion is soft, and a σ change does little.
   - A **pair-specific Li–O term** acts directly on the first-shell distance and is the natural lever.
   - **Structural target:** neutron diffraction with ⁶Li/⁷Li substitution, 10 mol % LiPF₆ in PC-d₆ (Kameda et al., *J. Phys. Chem. B* 111, 6104 (2007),
     doi:10.1021/jp072597b):
     - Li⁺···O(PC) = **2.04(1) Å**;
     - 4.5(1) PC per Li⁺;
     - ∠Li⁺···O=C = 138(2)° [abstract].
   - A later MD paper argues that part of the 4.5 is Li–F (Skarmoutsos et al., *J. Phys. Chem. C* 119, 4502 (2015), arXiv 1411.7171 [abstract/snippet]).
   - **Liquid-state check:** Chaudhari 2016 [read]: FF Li⁺–O first peak at 2 Å in EC/PC, consistent with AIMD and experiment. In water, FFMD put it at 1.8 Å against 1.95–1.97 Å (AIMD/neutron).
3. **PF₆⁻ charge distribution** (P +1.34, F −0.39 in CL&P, times ζ).
   - The F charge sets the field at the anion's surface, and hence the anion's electrostriction of the solvent.
   - Marcus & Hefter say anion V_el is small, so this is a secondary lever.
4. **ζ itself.** It moves V_φ (−74 → −45 cm³/mol per unit ζ) but extrapolates beyond 1 at 3 M. It also slows the ions (our scan: κ_NE exponent −3.6).
   It cannot be the lever for volume.

---

## 5. Studies that tuned Li–O or anion–solvent terms (carbonates)

| Study | What was tuned | Targets | Transport | Mark |
|---|---|---|---|---|
| Chaudhari et al. 2016 (above) | solvent charges (80 % EC, 90 % PC) | RDF against AIMD, dielectric constants, **D and t₊** | t₊ 0.35 (EC) and 0.31 (PC) against NMR 0.31 and 0.34; D prefactors in EC: model 2.12 (Li⁺) and 3.85 (PF₆⁻) against experiment 1.82 and 3.63 | [read]; transport was a target, so not admissible for us |
| Skarmoutsos, Ponnuchamy, Vetere, Mossa 2015 | none. Rigid EC/PC, force fields "adopted from previous studies" that "predict … tetrahedral coordination" | DFT clusters for comparison | — | [read §2]; MD puts DMC ahead of EC in the Li⁺ shell |
| Olguin, Borodin et al., *Phys. Chem. Chem. Phys.* 18, 164 (2016) (G4 Li⁺–carbonate binding) | reference data, not a fit | — | — | [repo]; already our layer-0 reference |
| Borodin & Smith 2006/2009 (APPLE&P) | polarizable Li⁺–O terms fitted to QM | QM binding and dimer energies | reportedly good D and κ | [unverified] |
| Kumar & Seminario (Li⁺/EC, J. Phys. Chem. C, about 2016) | Li⁺ terms | not checked | not checked | [unverified]: title, year and content to be checked |
| Doherty, Zhong, Gathiaka, Li, Acevedo, *J. Chem. Theory Comput.* (2017; volume and pages not checked) (OPLS-VSIL, ionic liquids incl. PF₆⁻, charges 0.8) | LJ of selected atoms refitted after charge scaling | densities, ΔH_vap, structure | viscosity, D (test) | [unverified]: the closest IL precedent for "scale charges, then refit LJ to densities" |

**Summary:**
- In carbonates I found no paper that refit pair-specific ion–solvent LJ against salt-solution **densities** and then tested transport.
- The documented precedent for that recipe is aqueous, Madrid-2019 [read].
- For the electrolyte the closest are: APPLE&P, with QM-fitted polarizable terms; and BAMBOO, whose density alignment carries over to transport [read].

---

## 6. Lehnert 2025: what they used

- **Force field:** OPLS (Banks 2005). Solvent parameters and charges from Maestro 2021-1. Li⁺ from JJ06, PF₆⁻ from CL&P 2004.
- **ζ:** 0.75 for EC:EMC 3:7, fitted to κ at 1 M, averaged over −20…20 °C, constant over c and T (SI S1.1, S1.4, Table S3) [read; repo notes].
- **Other settings:** geometric mixing, 1.4 nm cutoff, PPPM 10⁻⁵. No LJ modification or pair overrides are mentioned [read].
- **Density:** not reported. The implied densities are in §2.3.
- **Their own caveat** (main text [read]): a constant ζ neglects the concentration dependence of the screening; "at elevated concentrations …
  yielding elevated conductivities in the MD simulations" (EC:EMC and EC:DMC:PC at 3 M).

---

## 7. Ranked routes for us

**Rules (from the task):**
- every parameter cites a source;
- fit only to non-transport data: QM, pure-liquid ρ and ΔH_vap, structure, solution densities;
- κ, D and t₊ are tests only.

**Precondition for all routes:** the solvent offset near 0 M (+2.8 %, LigParGen EMC) belongs to layer 1 and must be repaired or
held fixed first. Otherwise a fitted V_φ absorbs the solvent error.

### Route A: ECC charges plus a few pair-specific LJ terms, fitted to solution densities, structure and QM (Madrid-2019 recipe)

- **What changes:** keep ζ physical (0.75 from ECC, or a short-range value from Kostal 2023's 0.78–0.83; author's choice), then fit
  NBFIX-type pair terms:
  - (i) PF₆⁻ F with solvent atoms, or the F σ itself;
  - (ii) Li⁺–O(carbonyl), separately for EC and EMC if QM demands;
  - optionally (iii) Li⁺–F.
- **Fit set** (all non-transport, all cited):
  - ρ(c,T) of EC:EMC 3:7 (Landesfeind 2019);
  - **transferability checks:** ρ(c) of LiPF₆ in EMC (Wang 2020) and in PC (Hou & Monroe 2020). These are strong, because the same ion
    parameters must give V_φ ≈ 38 → 49 in EMC and about 56 → 59 in PC;
  - Li–O 2.04 Å and CN about 4–4.5 (Kameda 2007, PC);
  - about 2 EC per Li⁺ at 1 M (Self 2024 DRS, as a check);
  - Li⁺–EC and Li⁺–EMC binding energies (Olguin 2016; our MP2).
- **Test set:** κ(c,T), D, t₊ and η.
- **Needs:**
  - `pair_overrides` already exist in spec 0.1.2. No engine or spec change.
  - A small fitting loop. Each density point costs about 1.5 GPU h. Three to four parameters against about 10–15 targets.
  - The author's approval of the targets and of "fitted by us to cited data" as each parameter's source.
- **Why first:** it is the documented route in which scaled charges plus pair LJ reproduce ρ(c) while transport stays a prediction
  (Madrid-2019). It acts on the term that §2 identifies: ion size and packing at fixed ζ.
- **Risk:**
  - Repairing the volume in a fixed-charge model may lower κ further (Maiti 2023: lower density means faster dynamics in rescaled models).
  - If it does, that is a measured failure that motivates Route C, not a reason to fit κ.

### Route B: ECC-R, one rescaled ion σ (PF₆⁻ first), as the cheap first step of A

- **What changes:** one or two scalars, the PF₆⁻ F σ and/or Li⁺ σ, reduced after scaling.
- **Source:** the ECC-R methodology (Kohagen 2016; Duboué-Dijon 2020; still to be read). Target: ρ(c) slope plus Li–O / Li–F distance.
- **Needs:** no new code. 3–4 runs per candidate (as in SC-4).
- **What it decides:** whether one σ can fix both V_φ(1 M) and V_φ(3 M). If not, go to the pair terms of A.
- **Weakness:** ECC-R's own target is a neutron RDF of the ion. For PF₆⁻ in carbonates I found no such data, so the fit would rest on density alone (one target per parameter).

### Route C: explicit polarization (Drude: CL&Pol type; or APPLE&P)

- **Why:**
  - It removes the need for a constant ζ and gives concentration-dependent screening.
  - In the one carbonate comparison I found, the polarizable FF beat scaled and unscaled fixed charges on κ, t₊, η and FTIR shell statistics together (Maiti 2023 [abstract]).
  - Its LJ must be re-balanced against the induction energy. CL&Pol does this with SAPT-based ε scaling [unverified detail].
- **Needs:**
  - spec changes: Drude particles, Thole screening, Tang–Toennies damping for Li⁺;
  - bridge work: OpenMM DrudeForce plus a dual thermostat;
  - about 2–4× compute;
  - parameters for EC, EMC, Li⁺ and PF₆⁻ from a published polarizable set. Availability and licence must be checked.
- **When:** only after A or B fails in a measured way, for example density fixed but κ_NE still below about 60 % of experiment.

**Not recommended:**
- raising ζ to fix density: extrapolates beyond 1 at 3 M and slows the ions;
- solvent-charge scaling as in Chaudhari 2016: fitted to D;
- an ML potential for production: about 10²–10³× the cost. BAMBOO is still useful as evidence that density can be a transferable alignment target.

---

## 8. Open checks before any parameter is proposed

1. Read the Maiti 2023 full text and SI: which polarizable FF; ρ(c) numbers; the ζ used.
2. Read the ECC-R papers for the actual σ reduction factors and targets.
3. Read Borodin & Smith 2009 for APPLE&P's ρ(c) error and Li–O distance.
4. Get the Nyman 2008 density data (EC:EMC 3:7, 25 °C) as a second source for the target system. Landesfeind's fit is linear and cannot show V_φ(c) curvature.
5. **Cheap diagnostics** (cost about 1 GPU h each):
   - V_φ of the model salt at about 0.5–1 M in pure EMC and in pure PC or EC, against 46 (EMC, 1 M, 20 °C) and 58 (PC, 1 M, 20 °C).
     This tells whether the excess is solvent-specific.
   - dV_φ/dσ_F(PF₆⁻) at fixed ζ, to confirm §4.4 item 1.
