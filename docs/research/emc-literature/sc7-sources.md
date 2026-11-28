# SC-7 sources: EMC vapour pressure, Δ_vap H, density; EC/DMC checks; how others refit carbonate LJ

> **Agent note, unchecked (2026-11-27).** Written by a literature agent for unitcellmd-c8; copied unchanged. Values marked DB,
> SNIPPET or derived are not ledger values. Nothing here is used before it is read in the original and entered in the ledger.

- **Label:** literature search by an agent, 2026-11-27, for task SC-7. Nothing here is in the ledger.
- **How each value was read** is given in its own column, in four classes:
  - **ORIGINAL**: read in the paper itself, or in the authors' own data file.
  - **DATA-FILE**: read in the authors' deposited raw data.
  - **DB**: read only in a database (NIST ThermoML XML, NIST WebBook). The paper was not read.
  - **SNIPPET**: read only in an abstract, search snippet or secondary page.
- **Derived** values are this agent's own fits, not published values. The scripts are in the scratchpad
  (`scripts/goldberg_dh.py`, `scripts/fit.py`, `scripts/water.py`). Under publication rule 3 they must be committed before any use.
- **Not reachable:** ScienceDirect, ACS (pubs.acs.org), ECHA, Wiley and Springer PDFs all returned HTTP 403. The NIST/TRC
  Web Thermo Tables need a subscription.
- **Key new finding:** a second, independent EMC vapour-pressure set exists, from Goldberg, Herdegen and Braeuer, J. Chem.
  Eng. Data 2026. Its raw data are deposited under CC BY 4.0, and I read them.

---

## 1. Vapour pressure of pure EMC

### 1a. Goldberg, Herdegen, Braeuer 2026 (new; second independent source)

- **Paper:** T. Goldberg, V. Herdegen, A. S. Braeuer, "Isobaric Vapor–Liquid Equilibria of Binary and Multicomponent Organic
  Carbonate Mixtures (DMC, EMC, DEC, EC, and PC) at 101.3, 25.0, and 5.0 kPa", *J. Chem. Eng. Data* **71**(11), 4756–4777
  (2026), doi [10.1021/acs.jced.6c00429](https://doi.org/10.1021/acs.jced.6c00429). The paper is CC BY 4.0 (Crossref licence),
  but the ACS PDF returned 403, so **the paper was not read**.
  - The abstract (Crossref/Semantic Scholar) says: "Vapor pressure curves of all substances were determined and correlated,
    together with statistically screened literature data, using the Antoine equation."
  - **Their Antoine parameters, standard uncertainties and EMC purity are in the paper and still unread.**
- **Raw data:** TU Bergakademie Freiberg OPARA, doi [10.25532/OPARA-1547](https://doi.org/10.25532/OPARA-1547), file
  `Vapor_pressure_data.txt`, CC BY 4.0.
  - Method (dataset abstract): all-glass dynamic recirculation still "Labodest VLE 602" (i-Fischer). This is in effect
    ebulliometry.
  - The columns give the standard deviation *during the measurement*. The file says the standard uncertainties are in the
    paper.

| T / K | std T / K | p / kPa | std p / kPa | read |
|---|---|---|---|---|
| 292.66 | 0.01 | 2.52 | 0.002 | DATA-FILE |
| 305.42 | 0.02 | 5.00 | 0.004 | DATA-FILE |
| 313.51 | 0.01 | 7.49 | 0.005 | DATA-FILE |
| 319.70 | 0.02 | 9.99 | 0.006 | DATA-FILE |
| 328.60 | 0.02 | 14.97 | 0.010 | DATA-FILE |
| 335.49 | 0.01 | 19.98 | 0.010 | DATA-FILE |
| 340.62 | 0.02 | 24.97 | 0.010 | DATA-FILE |
| 345.64 | 0.01 | 29.99 | 0.013 | DATA-FILE |
| 349.64 | 0.01 | 34.96 | 0.013 | DATA-FILE |
| 353.30 | 0.01 | 39.98 | 0.017 | DATA-FILE |
| 359.54 | 0.01 | 49.97 | 0.024 | DATA-FILE |
| 364.86 | 0.01 | 59.99 | 0.022 | DATA-FILE |
| 369.49 | 0.01 | 69.97 | 0.023 | DATA-FILE |
| 373.63 | 0.01 | 79.95 | 0.028 | DATA-FILE |
| 377.36 | 0.01 | 89.95 | 0.029 | DATA-FILE |
| 380.61 | 0.01 | 101.29 | 0.022 | DATA-FILE |

The same file also holds pure DMC (290.47–363.17 K), DEC, PC and EC (402–495 K) curves, used in §3.

### 1b. Dougassa et al. 2014 (the earlier source)

- **Paper:** Y. R. Dougassa, J. Jacquemin, L. El Ouatani, C. Tessier, M. Anouti, "Low pressure methane solubility in
  lithium-ion batteries based solvents and electrolytes as a function of temperature. Measurement and prediction",
  *J. Chem. Thermodyn.* **79**, 49–60 (2014), doi [10.1016/j.jct.2014.07.004](https://doi.org/10.1016/j.jct.2014.07.004).
  - It is J. Chem. Thermodyn., not J. Chem. Eng. Data.
  - It is a **gas-solubility paper**: the solvent vapour pressures are a by-product of the isochoric saturation technique.
- **The paper was not read.** ScienceDirect returned 403. The Queen's University Belfast portal has only the bibliographic
  record, no manuscript.
  - So its table number, fitted equation and any Δ_vap H it reports are **unknown**.
- **ThermoML** ([trc.nist.gov/ThermoML/10.1016/j.jct.2014.07.004.xml](https://trc.nist.gov/ThermoML/10.1016/j.jct.2014.07.004.xml)):
  - Method: "Closed cell (Static) method".
  - EMC sample purity 99.99, commercial source.
  - The "±" column below is the expanded uncertainty given in ThermoML. It is about 10 % of p, with a floor of 0.13 kPa.

| T / K | p / kPa | ± / kPa | read |
|---|---|---|---|
| 277.96 | 0.958 | 0.131 | DB |
| 282.06 | 1.285 | 0.132 | DB |
| 283.15 | 1.516 | 0.158 | DB |
| 288.15 | 2.008 | 0.202 | DB |
| 293.15 | 2.439 | 0.246 | DB |
| 298.15 | 3.658 | 0.368 | DB |
| 303.15 | 4.534 | 0.456 | DB |
| 308.15 | 5.801 | 0.583 | DB |
| 310.74 | 6.739 | 0.677 | DB |
| 314.83 | 7.885 | 0.794 | DB |
| 323.15 | 12.281 | 1.233 | DB |
| 328.15 | 15.258 | 1.531 | DB |
| 333.15 | 18.284 | 1.833 | DB |

**Quality check (derived), from the same ThermoML file:**
- **Water:** Dougassa's water points deviate from IAPWS-95 (Wagner–Pruss auxiliary saturation equation) by −6.7 % to +11.6 %,
  e.g. +2.0 % at 298.44 K and +8.8 % at 310.74 K.
- **DMC:** their DMC at 298.15 K is 6.982 kPa. That is 6.7 % below a Clausius–Clapeyron fit through the Kozlova 2008
  transpiration data (7.48 kPa).
- **EMC against Goldberg:** their EMC points lie −5.6 % to +7.2 % from an Antoine fit to Goldberg's points (inside 292–333 K).
  At 298.15 K they are +7.2 %.
- **Conclusion:** the set is consistent with its stated ~10 % uncertainty, but its scatter is large. **Goldberg 2026 is the
  more precise set.**

### 1c. Other EMC vapour-pressure or boiling-point data

| quantity | value | T | method | source | read |
|---|---|---|---|---|---|
| p(EMC) | 43 hPa | 25 °C | EC Method A.4 | ECHA registration dossier 5747, §4.6 | SNIPPET (ECHA returned 403). It is **26 % above** Goldberg's 3.41 kPa: do not use. |
| p(T) of EMC, used in an adsorption study | ? | ? | ? | F. Stehmann, P. Prziwara, C. Bradtmöller, M. Schoenitz, S. Scholl, "Adsorption Equilibria of Dimethyl Carbonate and Ethyl Methyl Carbonate onto Activated Carbon", *Chem. Ing. Tech.* **88**, 327–335 (2016), doi [10.1002/cite.201500130](https://doi.org/10.1002/cite.201500130) | **not read.** Franke 2025 cites it (ref. 36) as experimental EMC vapour-pressure data for its Fig. 5b. It may hold a third set. |
| T_b of EMC at 101.3 kPa | ? | — | VLE still | X. Zhang, J. Zuo, C. Jian, *J. Chem. Eng. Data* **55**, 4896 (2010), doi [10.1021/je100494z](https://doi.org/10.1021/je100494z) | not read. Its ThermoML file has no pure-EMC entry. Franke cites it (ref. 47) for EMC vapour pressure. |
| **normal boiling point** | **380.61 K at 101.29 kPa** (std 0.01 K) | — | recirculating still | Goldberg 2026 raw data | DATA-FILE. My Antoine fit gives T_b(101.325 kPa) = 380.6–381.0 K. |
| T_b (model) | 381.3 K; Δ_vap H(T_b) = 36.1 kJ/mol | — | CALPHAD assessment | Franke 2025, Table II | ORIGINAL (PDF). Calculated, not measured. |

### 1d. Δ_vap H of EMC at 298.15 K

| value / kJ mol⁻¹ | basis | source | read |
|---|---|---|---|
| **39.9–40.2** | Clausius–Clapeyron on Goldberg's p(T) (ideal gas, no virial or V_l correction) | **derived.** Fits: 3-term ln p = a + b/T + c ln T gives 40.08 (all 16 points) and 39.94 (p ≤ 30 kPa, 292–346 K). Antoine gives 40.22 and 39.96. p(298.15 K) = 3.411 kPa in every fit. | own fit of DATA-FILE |
| 40.7 ± 0.6 (1σ of slope) | Clausius–Clapeyron, 2-parameter, on Dougassa's 13 points, at T_mean = 302 K | **derived** (reproduces the earlier "about 40.7") | own fit of DB |
| 40.7 | "calculated in this work" from the assessed Gibbs energies | P. Franke, *J. Electrochem. Soc.* **172**, 070520 (2025), doi [10.1149/1945-7111/adee4e](https://doi.org/10.1149/1945-7111/adee4e), Table II (liq./gas row at 298.15 K, no reference number = this work) | **ORIGINAL (PDF).** Its EMC vapour-pressure inputs are refs. 25 (Dougassa), 36 (Stehmann) and 47 (Zhang), so it is **not independent of Dougassa** and predates Goldberg. |
| ≈ 41.2 | Arithmetic mean of DMC (38.0, Kozlova) and DEC (≈ 44.5 at 298 K, my CC fit of Kozlova's DEC transpiration points: 44.77 at 292 K) | **derived estimate**, a homologous-series interpolation only | — |
| 43.08 | ChemSep correlation | Cheméo | SNIPPET. Calculated: do not use. |

**Calibration of the Goldberg-based derivation on DMC (derived):**
- The same procedure on Goldberg's DMC curve (290–363 K) gives Δ_vap H(298.15 K) = **36.2–37.0 kJ/mol** and
  p(298.15 K) = 7.31–7.36 kPa.
- Calorimetric and transpiration values are 38.0 ± 0.2 (Kozlova 2008) and 37.7 ± 0.2 (Steele 1997); see §3.
- So the Goldberg-slope route reads DMC **1–1.8 kJ/mol (3–5 %) low**. If EMC carries the same bias, its true value is about
  41 kJ/mol.
- **Working conclusion:** Δ_vap H(EMC, 298.15 K) = 40–41 kJ/mol, ±1 kJ/mol. No calorimetric or transpiration measurement of
  EMC was found.
- **Gas-phase nonideality** (Z_g − Z_l < 1) would lower a Clausius–Clapeyron value by a few tenths of a percent at 3–7 kPa.
  This is an estimate of size only; no EMC second virial coefficient was found.
- **Not EMC:** Kozlova et al. 2008 (Verevkin group, transpiration) covers DMC, DEC, dipropyl, dibutyl and dibenzyl carbonate.
  This was checked in their ThermoML file. **No Verevkin-group EMC paper was found.**
- **Chickos & Acree:** the NIST WebBook entry for EMC compiled by Acree and Chickos lists only Δ_fus H (11.24 kJ/mol at
  219.4 K, Ding 2004). It has **no Δ_vap H**.

---

## 2. Density of liquid EMC

| ρ / kg m⁻³ | T / K | method | uncertainty as stated | purity | source | read |
|---|---|---|---|---|---|---|
| **1006.88** | 298.15 | vibrating tube | ± 0.13 (ThermoML) | 99.9 (ThermoML) | H. Y. Oh, J.-E. Gu, S.-J. Park, "Solid-liquid equilibria and thermo-physical properties of liquid electrolyte systems for lithium ion batteries", *Fluid Phase Equilib.* (2018), doi [10.1016/j.fluid.2018.05.033](https://doi.org/10.1016/j.fluid.2018.05.033) | DB. Their DMC value (1060.87) is 0.23 % below other 25 °C values. |
| 1010 (given as 1.01 g cm⁻³) | 298.15 | not stated in table | "precision and accuracy … close to (1×10⁻² and 5×10⁻²) g·cm⁻³" | mole fraction 0.9999, water < 10 ppm, Aldrich | Dougassa, Tessier, El Ouatani, Anouti, Jacquemin, *J. Chem. Thermodyn.* **61**, 32–44 (2013), doi [10.1016/j.jct.2012.12.025](https://doi.org/10.1016/j.jct.2012.12.025) | **ORIGINAL** (accepted manuscript, QUB portal), Tables 1 and 2. Too coarse for a target. |
| curve, 10–70 °C | 283–343 | density/specific-gravity meter KEM DA-505 | not stated | not stated | N. Nambu, Y. Sasaki, *Open J. Metal* **5**, 1–9 (2015), doi [10.4236/ojmetal.2015.51001](https://doi.org/10.4236/ojmetal.2015.51001), CC BY | ORIGINAL (PDF). EMC is **only plotted** (Fig. 2a), not tabulated. Digitising is possible but weak. |
| critically evaluated, 218.4–560 K | — | TDE evaluation | — | — | NIST/TRC Web Thermo Tables | not accessed (subscription) |
| 1.006 g mL⁻¹ | 25 °C | supplier | — | — | supplier listing (ChemicalBook snippet) | SNIPPET, secondary |

- **No second precise, independent EMC density series against temperature was found** (the target is 10–50 °C).
- The NIST ThermoML archive (through 2019) has 9 entries containing EMC. Only Oh 2018 has an EMC density. This was checked
  through the ThermoML API by InChIKey JBTWLSYIZRCDFO-UHFFFAOYSA-N.

---

## 3. Method check: EC and DMC at 298.15 K

### 3a. Δ_vap H

| compound | value / kJ mol⁻¹ | T | method | source | read |
|---|---|---|---|---|---|
| DMC | 38.0 ± 0.2 | 298.15 (from 274–304 K data) | transpiration ("GS") | S. A. Kozlova, V. N. Emel'yanenko, M. Georgieva, S. P. Verevkin, Y. Chernyak, B. Schäffner, A. Börner, *J. Chem. Thermodyn.* **40**, 1136–1140 (2008), doi [10.1016/j.jct.2008.02.012](https://doi.org/10.1016/j.jct.2008.02.012) | DB (NIST WebBook, Acree & Chickos compilation). The raw p(T) is in ThermoML (purity 99 %, transpiration). |
| DMC | 37.7 ± 0.2 | 298.15 (from 311–397 K) | ebulliometry ("EB") | W. V. Steele, R. D. Chirico, S. E. Knipmeyer, A. Nguyen, N. K. Smith, *J. Chem. Eng. Data* **42**, 1037–1052 (1997), doi [10.1021/je9700986](https://doi.org/10.1021/je9700986); data in **42**, 1008–1020, doi [10.1021/je970102d](https://doi.org/10.1021/je970102d) | DB (NIST WebBook) |
| DMC | 36.4 | 341 K | — | A. Rodríguez, J. Canosa, A. Domínguez, J. Tojo, *Fluid Phase Equilib.* **198**, 95 (2002) | DB (WebBook) |
| DMC | 38.4 | 298.15 | assessment (calculated) | Franke 2025, Table II | ORIGINAL |
| DMC | 36.2–37.0 | 298.15 | **derived** from Goldberg 2026 DMC p(T) | — | own fit; reads low, see §1d |
| DMC | p(298.15) = 7.48 kPa | — | **derived**, CC fit of Kozlova's transpiration points | — | own fit of DB |
| DMC | static p(T), 258–… K (mostly over solid DMC) | — | static | V. Pokorný et al., *J. Chem. Eng. Data* **62**, 3206–3215 (2017), doi [10.1021/acs.jced.7b00295](https://doi.org/10.1021/acs.jced.7b00295) | DB only. Their recommended Δ_vap H(298.15) is in the paper, **not read**. |
| EC (supercooled liquid) | 62.4 | 298.15 | assessment (calculated) | Franke 2025, Table II | ORIGINAL |
| EC | 61.9 | 298.15 | **derived**: 3-term fit of Pokorný 2017 static p(T) of liquid EC, 293–363 K, 54 points (purity 99.9) | V. Pokorný, V. Štejfa, M. Fulem, C. Červinka, K. Růžička, *J. Chem. Eng. Data* **62**, 4174–4186 (2017), doi [10.1021/acs.jced.7b00578](https://doi.org/10.1021/acs.jced.7b00578) | own fit of DB. Their published value was **not read** (ACS 403). |
| EC | 60.0 | 298.15 | **derived**: 3-term fit of Verevkin 2008 transpiration p(T) of liquid EC, 310–370 K, 29 points (purity 99.98) | S. P. Verevkin, A. V. Toktonov, Y. Chernyak, B. Schäffner, A. Börner, *Fluid Phase Equilib.* **268**, 1–6 (2008), doi [10.1016/j.fluid.2008.03.013](https://doi.org/10.1016/j.fluid.2008.03.013) | own fit of DB. Their published value was **not read**. |
| EC | WebBook "80 ± 80" (average of 6) | — | — | NIST WebBook | DB. Unusable; individual values are 55–60 kJ/mol at 383–433 K (Hong et al. 1982, ebulliometry). |

- **For EC, read the Δ_vap H(298.15) recommended by Pokorný 2017 and by Verevkin 2008 in the papers.** My two fits differ by
  2 kJ/mol, because EC at 298 K needs extrapolation and a ΔC_p.

### 3b. Density

The ledger already holds these from SC-5 (`docs/research/solvent-densities/README.md`; all DB, ThermoML, papers unread):
- **DMC:** 1063.3 kg m⁻³ at 25 °C (3 values) and 1069.8–1069.9 at 20 °C.
- **EC:** 1320.4 at 40 °C (interpolated) and 1315.7 ± 0.2 at 318.15 K (Oh 2018, ThermoML, vibrating tube).
  - EC has no stable liquid at 298.15 K (T_triple = 309.47 K).
- **For an EC check, use 40 °C, not 25 °C.**

---

## 4. Held-out checks: measured EMC viscosity (not fit targets)

| η | T | method | source | read |
|---|---|---|---|---|
| 0.65 cP | 25 °C | quoted from Barthel & Gores, not measured by Logan | Logan et al., *J. Electrochem. Soc.* **165**, A21 (2018), doi [10.1149/2.0271802jes](https://doi.org/10.1149/2.0271802jes), Table I | ORIGINAL (earlier session) |
| 0.68 mPa s (with ε_r = 2.93) | 25 °C | quoted in the introduction from the authors' earlier work | Nambu & Sasaki 2015, doi [10.4236/ojmetal.2015.51001](https://doi.org/10.4236/ojmetal.2015.51001) | ORIGINAL (p. 1–2) |
| curve, 10–70 °C | — | Ostwald viscometer (Shibayama SS-290S) × DA-505 density | Nambu & Sasaki 2015, Fig. 3b | ORIGINAL, figure only |
| 0 m EC:EMC 30:70 w:w: 1.30 / 1.11 / 0.97 / 0.87 cP | 10 / 20 / 30 / 40 °C | Ostwald, ± 2 % | Logan 2018, Tables II–V | ORIGINAL (earlier session); mixture, not pure EMC |

---

## 5. How others refit or parametrise carbonate LJ

**No published LJ refit of EMC to density and Δ_vap H was found.** What exists:

| work | molecules | what was changed | targets | errors reported | read |
|---|---|---|---|---|---|
| Z.-F. Luo, S. A. Burrows, S. Smoukov, X.-L. Fan, E. Boek, "Extension of the TraPPE Force Field for Battery Electrolyte Solvents", *J. Phys. Chem. B* (2023), doi [10.1021/acs.jpcb.2c06993](https://doi.org/10.1021/acs.jpcb.2c06993) (hybrid OA, ACS 403) | EC, PC, DMC, DEC, DME (**no EMC** per abstract) | **charges and dihedrals optimised.** LJ taken from the most similar TraPPE ether, acrylate and cyclic-ether types (snippet). | density, D, ε, η, surface tension | average absolute errors "approximately 15 %" across properties (abstract). DMC density 1.064 vs exp. 1.063 g cm⁻³, DEC 0.973 vs 0.980 (snippet, unverified). | abstract + SNIPPET |
| L. S. Dodda, J. Z. Vilseck, J. Tirado-Rives, W. L. Jorgensen, *J. Phys. Chem. B* **121**, 3864 (2017), doi [10.1021/acs.jpcb.7b00272](https://doi.org/10.1021/acs.jpcb.7b00272) (PMC5813481) | organic-liquid test set | charges only (LBCC on 1.14*CM1A) | ΔG_hyd; checked on ΔH_vap and ρ | "average errors of 1.40 kcal/mol and 0.024 g/cm³, similar to those for 1.14*CM1A" | abstract. This is the baseline accuracy of the current LigParGen model. |
| C. Caleman, P. J. van Maaren, M. Hong, J. S. Hub, L. T. Costa, D. van der Spoel, *J. Chem. Theory Comput.* **8**, 61–74 (2012), doi [10.1021/ct200731v](https://doi.org/10.1021/ct200731v) | 146 liquids, OPLS/AA and GAFF; carbonates among them (DEC named in a snippet) | none (benchmark) | ρ, Δ_vap H, C_p, γ, κ_T, α_P, ε | per-molecule numbers not read | abstract |
| M. I. Chaudhari, J. R. Nair, L. R. Pratt, F. A. Soto, P. B. Balbuena, S. B. Rempe, *J. Chem. Theory Comput.* **12**, 5709–5718 (2016), doi [10.1021/acs.jctc.6b00824](https://doi.org/10.1021/acs.jctc.6b00824) | EC, PC (OPLS-AA) | **charges scaled**, LJ unchanged | ε, Li⁺ solvation, D | — | only a Sandia poster (OSTI 1404799) read; no density or ΔH_vap errors there |
| L. B. Silva, L. C. G. Freitas, *J. Mol. Struct. THEOCHEM* **806**, 23–34 (2007), doi [10.1016/j.theochem.2006.10.014](https://doi.org/10.1016/j.theochem.2006.10.014) | EC, PC (Monte Carlo) | unknown | likely ρ and ΔH_vap (title: "structural and thermodynamic properties") | — | **not read** (DOI confirmed via Crossref) |
| O. Borodin, G. D. Smith, *J. Phys. Chem. B* **110**, 6279 (2006), doi [10.1021/jp055079e](https://doi.org/10.1021/jp055079e) | ether, alkane and carbonate solvents (APPLE&P, polarizable) | QC-fitted repulsion and dispersion and polarisabilities | validated on ρ and ΔH_vap (from memory, unverified) | — | **not read** |
| Soetens, Millot, Maigret, *J. Phys. Chem. A* **102**, 1055 (1998); Masia, Probst, Rey, *J. Phys. Chem. B* **108**, 2016 (2004) | EC, PC, DMC / EC | own LJ and charge sets | — | — | **not read; citations from memory, DOIs not confirmed** (Crossref query failed) |
| General guidance: liquid density is set mainly by σ, Δ_vap H mainly by ε | — | — | — | — | arXiv physics/9902056 (simplex force-field optimisation), SNIPPET only |
| Beauchamp et al., arXiv 1506.00262 (GAFF/AM1-BCC against ThermoML densities and ε) | DMC among the largest density outliers | — | — | — | SNIPPET only |

**Implication for SC-7 (my reading, not from a source):**
- None of these groups published a σ/ε refit of linear-carbonate OPLS types with stated density and ΔH_vap errors that I
  could read.
- The TraPPE extension refit charges and dihedrals and borrowed LJ. Chaudhari scaled charges.
- An SC-7 refit of EMC LJ is therefore new work, not a reproduction. Its method check has to come from refitting DMC (and EC)
  the same way.
- The obvious candidates are the carbonyl and ester oxygens and the carbonyl carbon (σ for density, ε for ΔH_vap). This is a
  design choice for the author, not a literature value.

---

## 6. What is still missing

1. **Goldberg 2026 full text:** their Antoine parameters, standard uncertainties of T and p, EMC purity and their screened
   literature list. The paper is CC BY but ACS blocks automated download, so fetch it by hand from
   doi 10.1021/acs.jced.6c00429.
2. **Dougassa 2014 full text:** the table number, the equation, and whether it reports Δ_vap H. ScienceDirect is blocked and
   no accepted manuscript was found.
3. **A calorimetric or transpiration Δ_vap H of EMC:** none found. The Verevkin group has measured DMC, DEC and the cyclic
   carbonates, but no EMC was found.
4. **Stehmann 2016:** check whether it contains EMC p(T). It would be a possible third set.
5. **EMC density against temperature (10–50 °C) from a second precise source:** not found. Options:
   - NIST/TRC WTT (subscription);
   - digitise Nambu 2015 Fig. 2a (weak);
   - post-2019 JCED/JCT/FPE papers not in the ThermoML archive (none found).
6. **EC and DMC recommended Δ_vap H(298.15):** read them in Pokorný 2017 (both papers) and Verevkin 2008. Only the raw p(T)
   was read, in ThermoML.
7. **ECHA EMC dossier** (43 hPa at 25 °C, method A.4) was not readable. It disagrees with both measured sets.
8. **Commit the Δ_vap H derivation as a script** (scratchpad `scripts/goldberg_dh.py`) before any ledger entry.
