# Ion model: route plan (plan only)

- **Written by** unitcellmd-40 on 2026-11-28, at unitcellmd-b4's request.
- **What this is not:** no parameter is chosen and no run is submitted here. Every value an ion model would change needs
  the author (CLAUDE.md).
- **Inputs:**
  - the literature notes in [README.md](README.md) (agent notes, unchecked);
  - the 3 M ζ map (`docs/research/density-c-T/v_phi_zeta.json`);
  - the PF₆⁻ size map (`studies/2026-11-27_pf6-size-3M`, Result);
  - SC-4;
  - the layer-0 QM results (`tools/ffcheck`, `tools/qm`);
  - strategy M3 and M4 and its principles (`forcefield-strategy.md`);
  - T5 (charge scaling).
- **Literature:** for the charge-scaling papers (the 2020 JCP practical guide, Fan 2025, Doherty 2017), the reading of
  agent-literature (V-5) in `docs/research/literature-2026-11-28/` is used once it lands. Section 7 lists what that
  reading must settle.

## 1. What is to be fixed, in numbers

| Observation | Value | Source |
|---|---|---|
| Salt volume too large | V_φ of the model 70.6 (1 M), 72.3 cm³/mol (3 M), against 55.7 (Landesfeind fit, 20 °C) | SC-4, `apparent_volume.json` |
| ρ(c) slope too small | 0.0710 ± 0.0009 against 0.0912 g cm⁻³ M⁻¹ (22 %) | SC-4 |
| Lehnert's model the same | slope 0.072 ± 0.004 g cm⁻³ M⁻¹, weighted by the integer ion step; −2.0 % at 3 M | `summary_261126-corrections/` row 11 |
| ζ is not the lever | dV_φ/dζ = −74 (1 M), −45 cm³/mol (3 M); closing the gap would need ζ ≈ 0.95–0.98 at 1 M and 1.12 at 3 M; ζ also slows the ions (κ_NE exponent −3.6) | `v_phi_zeta.json`, scan |
| Anion size carries part of it | PF₆⁻ σ × 0.95 removes 5.4 of 16.2 cm³/mol at 3 M (0.34), linear and symmetric; the whole excess would need about σ × 0.85 | PF₆⁻ size map |
| Li⁺ σ does nothing | no density response in the 1 M scan; JJ06's ε is tiny, so the Li–O repulsion is soft under geometric mixing | scan; README §4.4 |
| Li⁺ shell too poor in EC | EC share 28 % (M1) against Lehnert's model 47 % and the DRS estimate of about 2.2 bound EC per Li⁺ | T2 |
| Li⁺ binding (gas phase) | QM prefers EC over EMC by 6.24 kcal/mol (MP2/aug-cc-pVTZ, ours); M1 by 1.24. QM Li–O 0.175 nm, force fields 0.194–0.204 nm. Both force fields under-bind by 12–18 kcal/mol (missing induction) | `tools/qm`, strategy layer 0 |

**Two of these numbers move before any ion fit:**

- **The excess rests on an extrapolated ρ₀.** From ∂V_φ/∂ρ₀ = (1000/c − V_φ)/ρ₀: if V-4 measures ρ₀ 0.8 % lower than the
  extrapolation (+2.4 % instead of +3.2 %, Jo §3a), V_φ falls by about 7 cm³/mol at 1 M but only about 2 at 3 M (ours). So the
  share the anion size carries at 3 M changes little. The 1 M excess could halve.
- **The target V_φ is from a straight-line fit.** Landesfeind's ρ(c) is linear, so V_φ = 55.7 at every c. Measured V_φ rises with c in
  similar carbonates:
  - 46 → 49 cm³/mol from 1 to 2 M in EMC (Wang 2020, via the README);
  - in the ternary data of Gruber 2026 as well, by Jo's feedback §3b. Its numbers enter through V-5's ledger, not from the
    feedback file.

  If EC:EMC 3:7 curves the same way, the 3 M target lies a few cm³/mol above 55.7, and the 3 M excess is smaller than 16.
  Measured points (Landesfeind SI, Nyman 2008) replace the line as the target.

## 2. What has to come first

The rule is strategy principle 1: no ion parameter may compensate a solvent error.

1. **SC-7, the EMC refit** (author: Q1–Q7). EMC is 30 % over-cohesive and +2.8 % too dense. While it is, a fitted V_φ absorbs
   the solvent error. SC-7 Q5 already asks for this order.
   - SC-7's DMC calibration (Q7) was cancelled with soricel-pc away. It is a CPU-only gas-phase job and can run on the
     workstation's CPU worker instead.
2. **V-4, the measured ρ₀ of the M1 solvent**, and with it V_φ at 0.1, 1, 2 and 3 M recomputed. Done by agent-finite-size.
3. **ζ fixed before any pair term.** Pair terms fitted at one ζ do not carry over to another, so the choice of ζ comes first:
   - 0.75, as now;
   - ECC from n_D (T5, waits for the n_D sources, UnitcellMD#3);
   - or a short-range value. The README cites 0.78–0.83 (Kostal 2023), not yet read.
4. **Time step:** the fit uses the production step, 1 fs (ADR 0017), as SC-7 Q3 proposes, with SC-1's band stated.
   Mixing steps between the fit and production would add a bias of about 0.2–0.3 % in ρ.
5. **References read in the original:**
   - Kameda 2007 (Li–O 2.04 Å in PC; abstract only so far);
   - Self 2024 (DRS);
   - the ECC-R papers;
   - Nyman 2008 (EC:EMC 3:7 densities);
   - the Landesfeind SI points.

   Each goes into the ledger before it is a target (publication.md rule 3).

## 3. Routes, in the order they would be tried

### B: one size scalar for PF₆⁻ (ECC-R style), cheap, as a diagnostic first

- **What changes:** one scalar, the PF₆⁻ σ factor. The size map used one factor on P and F together.
- **Question:** can one size fix V_φ at 1 M and 3 M together, with an Li–F and an Li–P distance a source supports?
- **Prognosis from the map:** no. About × 0.85 would be needed at 3 M, far beyond a plausible size. B then becomes a
  measured "one term is not enough", which justifies A's extra terms.
  - This reading must be repeated after items 1 and 2 of section 2. With a smaller excess and a curved target, the factor
    needed shrinks.
- **Cost:** about 1.6 GPU h per density point (the size map and SC-4: 3 ns each). Four or five points (1 and 3 M, two
  candidate factors, one check) are about 8 h.

### A: a few pair-specific terms (Madrid-2019 recipe), the main route

`forcefield.pair_overrides` (spec 0.1.2) carries per-pair σ and ε. No spec or engine change is needed.

| Pair term | Why | Data that constrain it (fit side) | Data status |
|---|---|---|---|
| **PF₆⁻ F – solvent heavy atoms**, or the F σ itself | the anion's size carries the largest share of V° (README §1.3); the map shows 0.34 of the excess per 5 % | ρ(c) and V_φ(c) at 1–3 M | Landesfeind fit, in the ledger; SI points and Nyman 2008 to read |
| **Li⁺ – O(carbonyl, EC)** | sets the first-shell distance and EC uptake; Li⁺ σ cannot (soft repulsion) | Li–O distance (neutron, Kameda 2007, in PC); EC per Li⁺ (DRS, Self 2024); QM binding difference EC − EMC and Li–O distance (ours, Olguin 2016) | Kameda abstract only; DRS is our reading; QM in hand |
| **Li⁺ – O(carbonyl, EMC)** | the EC/EMC preference is a difference of two terms; one term alone cannot set it | the same QM difference; the shell composition | as above |
| *Li⁺ – F (optional)* | contact ion pairs and Li–F share of the coordination (Skarmoutsos 2015, abstract) | Raman contact-pair fractions (sources open, UnitcellMD#2); QM Li⁺–PF₆⁻ binding (can be computed with `tools/qm`, not done) | **no data yet: not fitted until a source exists** |

- **How many:** three terms, each with one free number (σ_ij, with ε_ij fixed by the mixing rule, or the other way round;
  that choice is an author question). Li–F is a fourth term only once data exist.
- **Targets (fit side), about 10–14 numbers for 3 parameters:**
  - V_φ or ρ at 1, 2 and 3 M, 20 °C;
  - ρ at 1 M, 10 and 50 °C (the model's dρ/dT agrees with Landesfeind and must keep agreeing; the 50 °C point itself
    fails SC-4 by its offset);
  - Li–O distance and coordination number;
  - EC per Li⁺;
  - the gas-phase EC − EMC binding difference and Li–O distance.
- **QM targets are differences and distances, not absolute binding energies.** A fixed-charge model under-binds Li⁺ by
  12–18 kcal/mol because it lacks induction. Fitting the absolute value would over-bind in the liquid. The gas phase also
  overstates the condensed-phase preference (Olguin 2016). So the QM numbers bound the potential, and the shell composition
  in the liquid is judged against the DRS estimate.
- **Transferability, kept apart:** ρ(c) of LiPF₆ in pure EMC (Wang 2020) and in PC (Hou & Monroe 2020).
  - These are strong tests: V_φ is about 38 → 49 in EMC and about 56 → 59 in PC.
  - Fit or test is an author question (Q3). As a test, they show whether the fit has only absorbed EC:EMC.
  - PC needs PC's solvent density to pass first. M0 PC is −0.2 %, so it does.
  - The pure-EMC solutions need SC-7's EMC.
- **Kept out of every fit:**
  - κ, D, t₊ and η (strategy principle 2);
  - Jo's group's ternary data (Gruber 2026: ρ, η and κ, −20 to 60 °C, 0.25–3 M) as the held-out prediction test of the
    whole model. Its solvent EC:DMC:EMC + VC needs DMC (and VC) models; that is the author's call (Q8).
- **Fitting loop, linear first:**
  - The size map was linear and symmetric at ±5 %. So: central finite differences per parameter at each fit state point,
    a Jacobian, linear least squares, one verification run at the solution, and a second iteration only if the
    verification misses its bands.
  - State points: 1 and 3 M in EC:EMC, 20 °C; 1 M at 10 and 50 °C for the check only.
  - Structure comes from the same trajectories at no extra cost. QM targets are CPU single points (`tools/ffcheck`).
- **Cost (ours):** 3 parameters × 2 signs × 2 state points + 2 central runs + verification ≈ 16–18 density points ≈ 26–30
  GPU h, plus 8 h if the EMC and PC solutions are tested. That fits about two nights of the GPU queue, run as ≤ 2 h jobs
  under the current queue rule.

### C: explicit polarization (strategy M4), only after a measured failure of A

- **Trigger, to be fixed by the author before A runs** (Q7). For example: A passes its density and structure bands, but
  the **finite-size-corrected** κ_NE (V-1/V-2) is still outside the transport band.
- The corrected value matters: Yeh–Hummer alone lifts M1's κ_NE from 0.50 to 0.60–0.80 S/m, depending on the model's η
  (`summary_261126-corrections/` row 1). A trigger on the uncorrected value would fire too early.
- **Needs:**
  - spec and bridge work: Drude particles, Thole screening, Tang–Toennies damping for Li⁺, a dual thermostat (README §7C);
  - about 2–4 × the compute;
  - a published polarizable parameter set whose licence permits use (CL&Pol; APPLE&P availability unchecked).

## 4. What would show that the plan is wrong

- **A cannot meet ρ(c) at 1 and 3 M with distances a source supports:** the excess is not short-range size and packing.
  Electrostriction under a constant ζ then becomes the suspect, and so does C.
- **The density fit moves κ_NE down further** (Maiti 2023: lower density means faster ions, so denser means slower). This
  is reported as a result and motivates C. It is never a reason to fit κ (README §7A risk).
- **The EC/EMC shell preference stays far from the DRS estimate after the Li–O terms:** the carbonyl charges are wrong
  (strategy M1/M2), not the pair terms.

## 5. Bands (proposals for the author; none approved)

| Target | Proposed band | Why |
|---|---|---|
| ρ at 1–3 M, 10–50 °C | ±0.5 % | the fit's own uncertainty is about ±0.6 % (SC-8); the time-step band is 0.2–0.3 % |
| V_φ at 1 and 3 M | ±3 cm³/mol | from the ±0.5 % band at 3 M (ours: 0.5 % of ρ at 3 M ≈ 3 cm³/mol); much wider at 1 M, which therefore weighs less |
| Li–O(carbonyl) first peak | ±0.05 Å of the neutron value | Kameda's ±0.01 Å is for PC, not EC:EMC; the band carries the solvent difference |
| EC per Li⁺ (1 M) | inside the DRS estimate's error | DRS is our reading of Self 2024 and must be read again first |

## 6. Questions for the author

- **Q1, order:** B as a one-scalar diagnostic before A, or straight to A? Recommended: B first. It costs about 8 GPU h, and
  its expected failure justifies A's extra terms with a measurement.
- **Q2, which terms:** PF₆⁻ size (F σ, or F–solvent pairs), Li–O(EC) and Li–O(EMC), with Li–F only once a source exists?
  And one free number per term: σ with ε from mixing, or ε with σ fixed?
- **Q3, transferability:** LiPF₆ in pure EMC (Wang 2020) and in PC (Hou & Monroe 2020) as **tests** (recommended), or in the
  fit?
- **Q4, QM targets:** the gas-phase EC − EMC difference and the Li–O distance as bounds, not the absolute binding energy?
  Recommended, for the induction reason in section 3A.
- **Q5, ζ:** fixed before the pair fit. Which one: 0.75, ECC from n_D (T5), or a short-range value?
- **Q6, source label:** "fitted by us to the cited data X, Y, Z" as each new parameter's source (CLAUDE.md: every parameter
  cites a source)? The fit script and its inputs would be committed with the parameters.
- **Q7, trigger for C:** which measured failure of A starts the polarizable route, stated before A runs?
- **Q8, the held-out test:** Jo's group's ternary data (Gruber 2026) as the prediction test of the whole model, never fitted?
  This needs a DMC model that passes its solvent tests (SC-7's DMC calibration) and a decision on the 1.5 wt % VC.
- **Q9, bands:** section 5.

## 7. What the literature reading (V-5 and the README §8) must settle before any parameter is proposed

- The ECC-R reduction factors and what they were fitted to (Kohagen 2016; the 2020 practical guide): is a σ reduction near
  5 % for a large anion precedented?
- Doherty 2017 (OPLS-VSIL): which LJ terms were refitted after charge scaling, and against what. It is the closest
  ionic-liquid precedent for PF₆⁻.
- Fan 2025: what it fits and what it tests.
- Maiti 2023 full text and SI: the polarizable force field used and its ρ(c) numbers.
- Borodin & Smith 2009: APPLE&P's ρ(c) error and Li–O distance.
- Nyman 2008 and the Landesfeind SI: measured densities at 25 and 20 °C that resolve the curvature of V_φ(c).
- Kameda 2007 and Self 2024, in the original: the structural targets of section 3A.
