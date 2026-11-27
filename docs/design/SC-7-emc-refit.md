# SC-7 — Refit the EMC Lennard-Jones parameters to density and ΔH_vap (design, for approval)

- **Status:** proposal, 2026-11-27 (unitcellmd-c8). The author said "go ahead" for SC-7; this note needs approval before
  any fitting run. Step 0 (the current model's ΔH_vap, no new parameter) runs already: `studies/2026-11-27_emc-dhvap-baseline`.
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
