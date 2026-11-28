# SC-7 — Refit the EMC Lennard-Jones parameters to density and ΔH_vap (design, approved 2026-11-28)

- **Status:** proposal, 2026-11-27 (unitcellmd-c8). The author said "go ahead" for SC-7.
  - **Approved by the author 2026-11-28:** "for SC-7 I take the recommendations".
    - That is Q1 (c) 40.5 ± 1.0 kJ/mol, Q2 option A, Q3 fit at 1 fs, Q5 SC-7 before the ion model, Q6 the wider map, and
      Q7 the DMC calibration first (done: r = 0.97, shared).
    - Q4, downloading Goldberg 2026 and Oh 2018, is the author's action and still open.
    - The same choices had been written up shortly before by the agent "decisions" under the delegation of that morning.
      Its §7 stays as the record of the reasons; the decisions are the author's.
  - **Fit runs** follow the order at the end of §7. They need the conditions of Q1 first: the derivation script and ledger
    entries committed, and Goldberg 2026 read (Q4). On the GPU they queue behind the V tasks, the author's priority of
    2026-11-28.
  - Step 0 (the current model's ΔH_vap, no new parameter) is done: `studies/2026-11-27_emc-dhvap-baseline`.
- **Task:** `docs/tasks.toml` SC-7. Acceptance there: every parameter has a source; targets fixed before fitting; κ, t₊ and D
  never used.

## 1. Why

- LigParGen EMC (OPLS-AA LJ, 1.14·CM1A charges) is **2.8 % too dense** at 25 °C (SC-1: 1.0346 g/cm³ at 1 fs against
  1.00688). It is 70 % of the solvent by mass.
- SC-4 shows the electrolyte **+2.8 % too dense near zero salt**. That is the solvent's offset. It cancels against the ions'
  too-flat slope near 1 M, so the 1 M agreement is partly luck.
- The 1 M scan's EMC ε probe moved D(Li⁺) and D(EMC) strongly (exponent about −4). The solvent therefore takes part in the
  slow ions (T4), but transport is never a target here.
- **Order:** SC-7 comes before the ion model. EMC's LJ types enter every EMC–ion pair through the combination rule, so the ion
  terms have to be fitted on the final solvent.

## 2. Targets (fixed here, before any fit; values to be confirmed in the originals)

| Target | Value | Source | State |
|---|---|---|---|
| ρ(EMC, 298.15 K) | 1006.88 ± 0.13 kg/m³ | Oh, Gu, Park, *Fluid Phase Equilib.* 2018, doi 10.1016/j.fluid.2018.05.033 (vibrating tube, 99.9 %) | ThermoML only; **read the paper first**. Consistent with 1.01 ± 0.05 (Dougassa 2013, read) and the supplier value 1.006. |
| ΔH_vap(EMC, 298.15 K) | **40–41 kJ/mol** (see Q1) | Clausius–Clapeyron on Goldberg, Herdegen, Braeuer, *J. Chem. Eng. Data* 71, 4756 (2026), raw data doi 10.25532/OPARA-1547 (CC BY): 39.9–40.2. Dougassa 2014 (ThermoML, ±10 %): 40.7 ± 0.6. On DMC the Goldberg route reads 1–1.8 kJ/mol below calorimetry (Kozlova 2008, Steele 1997). | Raw data read, paper not read (ACS blocks automated download). The derivation script must be committed first (publication rule 3). |

No calorimetric ΔH_vap of EMC exists (`docs/research/emc-literature/sc7-sources.md`). The ΔH_vap target is therefore
weaker than the density target, and its tolerance should say so.

## 3. Parameters (proposal: option A)

| Option | Fitted | Targets | Comment |
|---|---|---|---|
| **A (recommended)** | two factors on all EMC atom types: s_σ on every σ, s_ε on every ε | ρ, ΔH_vap | exactly determined. It keeps LigParGen's relative pattern and the charges. Each fitted value is "LigParGen × factor, fitted to [targets]", which is a source. |
| B | σ, ε of the carbonyl O, ester O and carbonyl C (6) | ρ, ΔH_vap (+ ρ(T)) | under-determined: there is no second precise ρ(T) source (SC-5 and the agent search found none), so B needs regularisation, i.e. choices without data |
| C | strategy M2: RESP charges for all solvents plus a few LJ types against five solvents | ~20 | the larger, consistent route (`forcefield-strategy.md`); needs the QC method decision. Not now. |

EC stays as it is (Caleman OPLS-AA, reproduced to −0.1 % / −0.54 kJ/mol; ADR 0014). Charges and bonded terms of EMC stay.

## 4. Procedure

1. **Step 0 (running):** ΔH_vap of the current model, gas phase against SC-1's liquids. It shows how far the cohesion is from
   the target, next to the known density error.
2. **Step 1, the map (4 liquid + 4 gas runs):** a 2 × 2 design around the current model, s_σ ∈ {1.00, 1.02} × s_ε ∈ {1.00,
   0.90}, without the existing corner (1, 1). That leaves 3 new liquids plus 3 gas phases; the fourth corner is
   step 0. These are probe values, not parameters.
   - A 2 % larger σ lowers ρ by roughly 6 % if ρ ∝ σ⁻³.
   - In the 1 M scan, ε × 0.85 lowered the density by 2.0 %.
   - So both factors move both targets, and the map gives the 2 × 2 Jacobian.
   - The protocol is SC-1's EMC liquid: 500 molecules, NPT, 25 °C, 1 fs (ADR 0017), 2 ns with 0.5 ns skipped. SC-1 measured the
     settling and the spread: 0.03 % in ρ between seeds.
3. **Fit:** solve the linear model of step 1 for (s_σ, s_ε) that meets both targets. If the solution lies outside the map, or
   the map is visibly non-linear, one more map point is added before solving. Nothing is tuned by hand.
4. **Step 2, confirmation:** the solution with three seeds (liquid and gas). **Accepted if** ρ is within 0.3 % of the target
   (ten times the seed SE of SC-1, and below the Landesfeind fit's own 0.6 %) and ΔH_vap within the tolerance of Q1.
5. **Held-out checks (reported, never fitted):**
   - ρ(T) of EMC at 10 and 40 °C against Nambu & Sasaki 2015, Fig. 2a (figure only, a weak check);
   - the EC:EMC 3:7 solvent: SC-4's 0.1 M point re-run with the new EMC, against Landesfeind (1.5 % criterion);
   - η(EMC) against 0.65 cP (Logan 2018 Table I, from Barthel & Gores), once T4 can run;
   - D and κ are reported as test data only.

**Cost:** an EMC liquid run (2 ns, 1 fs) takes about 32 min on the GPU (SC-1 log), and a gas run takes minutes on any CPU
(soricel). Steps 1–2 together come to about 4 GPU hours.

**Code:** `make_packages.py` with a factor change as in the scan (`change_eps_emc`, plus an analogous σ change), the step-0
analysis for ΔH_vap, and a 2 × 2 solve with a test. No engine, spec or builder change.

## 5. Questions for the author

- **Q1, ΔH_vap target:** either (a) 40.1 kJ/mol, the Goldberg Clausius–Clapeyron value as it stands; (b) about 41, corrected
  by the DMC calibration; or (c) **40.5 ± 1.0 kJ/mol**, which covers both and says how weak the target is. Recommendation:
  (c), with acceptance |ΔH_vap − 40.5| ≤ 1.0.
- **Q2, parameters:** option A (two global factors)? Recommended.
- **Q3, step:** fit at 1 fs, the production step (ADR 0017)? That bakes 1 fs's −0.3 % density bias into s_σ, consistently
  with production. The final 0.5 fs check of ADR 0017 item 4 shows its size. Recommended.
- **Q4, sources:** could you download Goldberg 2026 (CC BY, doi 10.1021/acs.jced.6c00429) and Oh 2018 into `../Lit`? ACS and
  ScienceDirect refuse automated downloads. Their uncertainties, purity and Antoine fit decide the tolerance in Q1.
- **Q5, order:** SC-7 before the ion-model fit (§1)? Recommended.
- **Decided 2026-11-28 by the author** ("I take the recommendations"; recorded first by agent decisions under the
  delegation; reasons and what would change each item in §7):
  - Q1 (c), 40.5 ± 1.0 kJ/mol, with conditions before the first fit;
  - Q2 option A, subject to Q7;
  - Q3 at 1 fs;
  - Q4 is the author's download;
  - Q5 yes.

## 6. Amendment after step 0 (2026-11-27 afternoon; for approval)

**Step 0 result** (`studies/2026-11-27_emc-dhvap-baseline`, Result): the current EMC has ΔH_vap = **53.17 ± 0.04 kJ/mol** at 1 fs,
**12–13 kJ/mol (30 %) above** the 40–41 working range. The method was checked against the CPU engine and the trajectory
(`docs/research/emc-literature/cohesion_split.py`). Per molecule the cohesion is LJ −37.7, Coulomb −14.6 kJ/mol, and
intramolecular distortion gives back +1.6.

What this changes:

1. **The map in §4 is too narrow.** To first order the target needs ε × 0.66 (ε × 0.7 or so once the lower density is counted).
   The density then falls, by roughly 2 % per 0.15 of ε (1 M scan), so σ probably has to go down, not up. Proposed instead,
   still probe values only:
   - step 1a: s_ε ∈ {0.85, 0.70} at s_σ = 1.00 (2 liquids, 2 gas phases), giving ΔH_vap(s_ε) and ρ(s_ε);
   - step 1b: one σ point, s_σ = 0.98 at the s_ε of step 1a's interpolation, giving ∂ρ/∂s_σ and ∂ΔH/∂s_σ there;
   - then the solve and the three-seed confirmation of §4. About 4 GPU hours, as before.
2. **A uniform 30 % cut of every OPLS ε is not a small correction.** It would make EMC a new model, "OPLS-AA LJ × (s_σ, s_ε)
   fitted to ρ and ΔH_vap", and its transferability is unknown. The held-out checks of §4.5 become more important, ρ(T) above
   all. The other routes:
   - **B** (only the carbonyl/ester O and C) concentrates the cut on fewer types. It is still under-determined (§3).
   - **C** (RESP charges and a few LJ types) is the larger route.
   - **Another published EMC model:** the agent search found no linear-carbonate model with stated density and ΔH_vap errors
     (`docs/research/emc-literature/sc7-sources.md`, unchecked), so there is none to take over.
3. **A cheap calibration of the conclusion (proposed, no new parameter):** DMC has a calorimetric ΔH_vap (NIST: 38.0 ± 0.2,
   primary papers not read). The same LigParGen OPLS-AA route for DMC shows whether the over-cohesion is a property of the
   carbonate types or of EMC alone. One liquid (GPU, ~30 min) and three gas runs (CPU) are needed.

**Questions added:**

- **Q6:** accept the wider map of item 1 (option A), knowing that the fit may land near ε × 0.7?
- **Q7:** first the DMC calibration of item 3? Recommended: it costs half an hour of GPU and decides whether option A's
  global factor is a fix for one molecule or a systematic correction of the carbonate types.
- **Decided 2026-11-28 by the author** ("I take the recommendations"; §7):
  - Q6 yes, the wider map;
  - Q7 yes, the DMC reading first, with what each outcome means. It was answered the same day: r = 0.97, the
    over-cohesion is shared by the carbonate types, and DMC becomes the held-out test.

## 7. Decisions of 2026-11-28 (the author's; reasons written by agent decisions)

The author first delegated SC-7's open questions on 2026-11-28 and said SC-7 "can wait". Agent decisions wrote the choices
below with their reasons. The same day the author took the recommendations, which are these choices, so they are the
author's decisions. They start nothing by themselves: fit runs follow the order at the end of this section.

- **Q1, decided: (c) ΔH_vap(EMC, 298.15 K) = 40.5 ± 1.0 kJ/mol. Acceptance |ΔH_vap − 40.5| ≤ 1.0 at 1 fs.**
  - **Reason:** the band covers (a) and (b). It also says how weak the target is: no calorimetric or transpiration value
    of EMC exists. Against the model's present 53.2, a ±1 band is still sharp (2.5 % of the target), and choosing (a)
    or (b) moves the fit by less than the band.
  - **Sources and their state** (`docs/research/emc-literature/sc7-sources.md`, an agent note, **unchecked**):
    - Goldberg, Herdegen, Braeuer, *J. Chem. Eng. Data* 71, 4756 (2026), raw data doi 10.25532/OPARA-1547:
      Clausius–Clapeyron 39.9–40.2. Our own fit of the deposited data; **the paper is not read**, so its Antoine fit,
      uncertainties and purity are unknown.
    - Dougassa 2014 (*J. Chem. Thermodyn.* 79, 49): 40.7 ± 0.6, our own fit of the ThermoML record. **Paper not read.**
    - Franke 2025 (*J. Electrochem. Soc.* 172, 070520) Table II: 40.7, read. It is calculated, and not independent of
      Dougassa.
    - The calibration of the Goldberg route on DMC (it reads 1–1.8 kJ/mol low) rests on Kozlova 2008 (38.0 ± 0.2) and
      Steele 1997 (37.7 ± 0.2), both from the NIST WebBook. **Neither paper is read.**
  - **Conditions before the first fit run** (publication rule 3):
    - the Clausius–Clapeyron script is committed (it sits in an agent scratchpad today);
    - ledger entries for every number above;
    - a reading of Goldberg 2026 (Q4).

    If that reading moves the centre or gives a wider uncertainty than ±1, the target is changed and dated here
    **before** step 1 runs, never after a fit result.
  - **What would change it:** a measured calorimetric or transpiration ΔH_vap of EMC; Goldberg's own Antoine fit or
    uncertainties; a second reading that disagrees with the agent note.
- **Q2, decided: option A** (s_σ and s_ε on all EMC LJ types; charges and bonded terms unchanged), **subject to Q7.**
  Q7 is answered (r = 0.97, shared), so option A stands. The same factors are applied to DMC as the held-out test.
  - **Reason:** two targets fix two factors exactly. B is under-determined: no second precise ρ(T) of EMC exists. C is
    strategy M2 and waits for the QM method decision.
  - The result is a new model, named "LigParGen OPLS-AA LJ × (s_σ, s_ε), fitted to ρ and ΔH_vap" (§6 item 2), and it is
    reported as such.
  - **What would change it:** the reading of Q7 (below), or held-out checks that fail (ρ(T), the solvent density at
    c → 0). Then B or C is designed instead.
- **Q3, decided: fit at 1 fs** (ADR 0017).
  - **Reason:** the model is used at 1 fs. A fit at 0.5 fs would miss its own target in production by the known band
    (about −0.3 % in ρ). The final model's 0.5 fs check (ADR 0017 item 4) states the band.
  - **What would change it:** a change of the production step or constraints by the author (e.g. after V-3). Then the
    fit is repeated at the new protocol, about 4 GPU hours.
- **Q4: the author's action, not decided here.**
  - Goldberg 2026 (CC BY, doi 10.1021/acs.jced.6c00429) and Oh 2018 (*Fluid Phase Equilib.*, doi
    10.1016/j.fluid.2018.05.033) into `../Lit`. ACS and ScienceDirect refuse automated downloads.
  - Useful too, optional: Dougassa 2014 (doi 10.1016/j.jct.2014.07.004) and Kozlova 2008 (doi 10.1016/j.jct.2008.02.012),
    for the DMC reference used by the calibration.
- **Q5, decided: SC-7 before the ion model.**
  - **Reason:** the combination rule puts EMC's LJ types into every EMC–ion pair, so ion terms fitted now would be
    fitted to the wrong solvent. `docs/research/priorities-2026-11-28.md` puts the solvent first too.
  - **What would change it:** an ion-model route that does not use the combination rule for ion–solvent pairs (pair
    overrides for every ion–solvent pair, ADR 0015). Even then the solvent offset (+2.8 % near c = 0) stays.
- **Q6, decided: the wider map of §6 item 1** (step 1a: s_ε ∈ {0.85, 0.70} at s_σ = 1.00; step 1b: one point at
  s_σ = 0.98 at the interpolated s_ε; then the solve and the three-seed confirmation of §4), knowing that the fit may land
  near ε × 0.7.
  - The values are probes, not parameters.
  - The held-out checks of §4 item 5 are reported for any solution, in this order:
    1. ρ(T);
    2. DMC with the same factors (ρ and ΔH_vap, after Q7's result);
    3. the 3:7 solvent at c → 0 (V-4 measures that point);
    4. η against Logan 2018, once V-1 can run.
  - **What would change it:** visible non-linearity, or a solution outside the map. Then one more map point is added
    before solving, as §4 item 3 says.
- **Q7, decided: the DMC calibration first.** Steps 1a and 1b wait for its reading, by the rule fixed in
  `studies/2026-11-27_dmc-dhvap-calibration/README.md`:
  - **r ≥ 0.6 (shared):** option A goes ahead. DMC with the same factors becomes a held-out test of whether they fix the
    carbonate types, not only EMC.
  - **0.3 < r < 0.6 (partly shared):** option A goes ahead. The report states that only part of the excess is shared
    by the carbonate types, and B is kept as the next option.
  - **r ≤ 0.3 (EMC's own):** no global LJ cut. EMC's charges and conformers are examined first, in a new design
    section.
  - **Reason:** it costs almost nothing (the liquid exists, the gas phase runs on a CPU), and it decides whether
    option A is the right lever.
  - **Answered by data, the same day** (`studies/2026-11-27_dmc-dhvap-calibration`, Result, commit 416aebc):
    - LigParGen DMC, which uses the same OPLS-AA LJ types, gives ΔH_vap = 50.23 ± 0.03 kJ/mol at 1 fs. The
      calorimetric value is 38.0 ± 0.2 (NIST table, primary papers not read, not in the ledger): an excess of
      +12.2 kJ/mol (+32 %). EMC's excess is +12.7 (+31 %).
    - r = 0.97 ≥ 0.6, so by the rule fixed before the runs **the over-cohesion is shared by the carbonate types.** The
      prediction (r ≈ 0.7–1) held.
    - So option A goes ahead (Q2), and the wider map stands (Q6). A global (s_σ, s_ε) is a correction of the carbonate
      types, not a fix for one molecule.
    - **DMC is the held-out test of the fitted factors:** they are applied unchanged to DMC, and its ρ and ΔH_vap are
      reported against experiment. They are never fitted to DMC.
    - The DMC reference must enter the ledger before it is used as a held-out test (Q4: Kozlova 2008 is useful for
      that).
    - DMC's excess rests on a calorimetric reference. EMC's own target, built on vapour pressures, is therefore not the
      cause of EMC's excess.
    - What this does not settle: whether the factors fitted on EMC also give DMC's density. That is what the held-out
      test is for.

**Order of the fit (approved; on the GPU behind the V tasks):**
1. Q7's reading: done 2026-11-28, shared (r = 0.97);
2. the conditions of Q1;
3. step 1a, then 1b;
4. the solve;
5. the three-seed confirmation;
6. the held-out checks.

Each GPU step goes through the queue.
