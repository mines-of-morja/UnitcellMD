# Force-field strategy: from Lehnert's model to experiment

- **Status:** proposal, 2026-11-20. No parameter is chosen here; each step that sets one needs the
  author's approval and a cited source (CLAUDE.md).
- **Companions:**
  - [calculation-plan.md](calculation-plan.md): the calculations, their costs and statuses;
  - [forcefield-survey.md](forcefield-survey.md): candidate parameter sets;
  - [report/report.md](report/report.md): the numbers quoted below.
- **Question:** how do we extend the model so that it reproduces experiment, with parameters we
  can defend, and what would be too much or the wrong direction?

## 1. Where we stand

Same protocol, same ions (JJ06 Li⁺, CL&P PF₆⁻), same ζ = 0.75 as Lehnert 2025. Only the solvent
parameters differ: LigParGen instead of Maestro OPLS.

| 1 M LiPF₆ in EC:EMC 3:7, 20 °C | this work (A2, A3) | Lehnert MD | experiment |
|---|---|---|---|
| density | 1.4 % below Lehnert's model | — | open (Logan 2018, Gruber 2026) |
| EC share of carbonyl O at Li⁺, r ≤ 5.16 Å | 20 % | ≈ 47 % | disputed; source open |
| κ (formal charges) | 0.42 ± 0.09 S/m | ≈ experiment (ζ fitted) | 0.84 S/m (Landesfeind 2019) |
| κ_NE (no correlations) | 0.48 ± 0.03 S/m | — | — |
| t₊ (COM) | 0.29 ± 0.11 | 0.373 | 0.343 (eNMR, Lehnert) |
| pure EMC / EC density | +2.9 % / −3.5 % | — | Lehnert Table S2 |

**Reading:**
- We have reached Lehnert's **method**, not his **results**. The remaining gap sits in the
  solvent model, because everything else is identical.
- **κ_NE is only 57 % of κ_exp.** Even if all ion correlations vanished, our ions would be too slow. So
  the κ deficit is a mobility problem (viscosity, Li⁺ dragging an EMC shell), not an
  association problem.
- ζ mostly controls association. Fitting ζ to κ now would therefore push it to whatever value
  hides the solvent error. That is the first thing **not** to do.

## 2. Principles

1. **Repair each layer with its own data.** Molecule → pure liquid → one ion in solvent →
   electrolyte. A parameter in one layer must not compensate an error in another (e.g. ζ
   compensating a too viscous EMC).
2. **Fit set and test set are separate and fixed in advance.** Transport (κ, t₊, D±, residence
   times) is test data. At most one scalar, ζ, may ever be calibrated against κ, and only if
   step S6 fails.
3. **Few parameters, many targets.** Every fit is over-determined; otherwise it explains
   nothing.
4. **Change only what a test shows broken,** and record the change as a transform with its
   source (ADR 0008 §4).
5. **No direct tuning to the answer:** no carbonyl charge adjusted until EC enters the shell, no
   ζ per concentration or temperature.

## 3. Targets per layer

| layer | fit to | test against |
|---|---|---|
| 0 molecule (QM) | electrostatic potential → charges; conformer energies | Li⁺–EC and Li⁺–EMC binding energies (single and mixed Li⁺(S)₄ clusters); dipole moments (experimental, source open) |
| 1 pure solvents | ρ(T), ΔH_vap | ε (A7), viscosity η (A6), self-diffusion |
| 2 one ion in solvent | — | Li–O distance and coordination (diffraction or AIMD, sources open); EC vs EMC preference (A4; spectroscopy, source open) |
| 3 electrolyte | (ζ only as a last resort, S6) | ρ(c,T) and η(c,T) (Logan 2018, Gruber 2026); κ(c,T) (Landesfeind 2019, Logan 2018); t₊ (with the known dispute) |

The ion–solvent layer is where Lehnert's and our models differ most visibly. It is also the
layer with the weakest experimental data, so QM cluster energies (layer 0) are the independent
check there.

## 4. Model levels, from cheap to expensive

Each level is a recipe change and runs through the same tests. We stop at the first level that
passes.

| level | what changes | why | cost | risk |
|---|---|---|---|---|
| **M0** | nothing (LigParGen solvents, ADR 0009) | baseline | done | — |
| **M1** | EC (and PC) from the published OPLS-AA types (Caleman 2012; survey set 2) | tests the carbonyl-charge hypothesis with a published set; EC density is published to 0.05 % | A1 + A4, about 3 h of GPU | linear carbonates stay LigParGen (EMC +2.9 %); primary citation of the types still open |
| **M2** | charges for all solvents from one QM method (RESP), plus a small refit of a few LJ types (carbonyl O, ester O, CH₃/CH₂) against ρ(T) and ΔH_vap of all five solvents at once | one consistent method instead of per-molecule fits; repairs EMC and EC together; about 6–10 parameters against about 20 targets | psi4 container (decision open); fit loop about 1–2 GPU days | needs an approved QC method; the fitting tool is new |
| **M3** | ζ from physics instead of κ: ECC, ζ = 1/√ε_el with ε_el ≈ n_D² of the solvent; optionally the Li⁺ σ adjusted to the QM Li–O distance (ECC-R) | makes κ(c,T) a **prediction**; carbonates have n_D ≈ 1.38–1.42, so ζ ≈ 0.70–0.73, close to Lehnert's fitted 0.75 (n_D values to be sourced) | almost free: one 1 M run per candidate | ECC's standard justification is for ions in polar solvents; it needs its sources checked |
| **M4** | explicit electronic polarization (Drude), through OpenMM's Drude support in the bridge (ADR 0008 §7), or a published polarizable carbonate set (APPLE&P, Borodin & Smith 2006, if its parameters are available) | concentration-dependent screening; a constant ζ already fails at 3 M in Lehnert's work | about 2–4× compute per ns; bridge work; dual thermostat | only worth it if M3 fails in a specific, measured way |

**Expected path:** M1 → (M2 if EMC stays outside 2 %) → M3 → C-stage production. M4 is the
research extension for high concentrations, not a prerequisite.

## 5. Too much, or the wrong direction (now)

- **ζ fitted to κ before the solvent passes layer 1.** It would hide the mobility error (§1).
- **ζ per concentration or temperature.** It fits the curve and removes the prediction;
  Lehnert avoided it too.
- **Hand-tuning single charges or LJ values** until the shell or κ looks right.
- **A global refit against transport data.** Expensive, under-determined and uninterpretable.
- **Machine-learned potentials for production.** 10²–10³× the cost; transport needs about
  100 ns per state point. At most a reference for layer 0 or 2.
- **A Maestro licence to match Lehnert exactly.** It would reproduce his model, not experiment.
  Useful only as an optional cross-check of the engine, not as the way forward.
- **Interphases, SEI, reactions.** Outside a bulk model.

## 6. Next steps

| step | content | compute | needs |
|---|---|---|---|
| S1 | Sources: n_D, ε, ΔH_vap of EC, EMC, DMC, PC (Caleman 2012 SI lists the primary references); experimental evidence on preferential Li⁺ solvation; ECC and ECC-R primary papers (Leontyev & Stuchebrukhov; Kirby & Jungwirth 2019); APPLE&P availability | none | literature (citations to be checked against the papers) |
| S2 | M1 for EC: A1 (density at 40 °C) and A4 in pure EC and EC:EMC 1:1 | about 3 h GPU, after A4 | approval of M1 as a test set (not yet as the working horse) |
| S3 | A5 (ΔH_vap) and A7 (ε) for EC and EMC on M0 and M1; tools exist | CPU | S1 sources |
| S4 | A6, viscosity of pure EMC and of 1 M on M0: tests the mobility hypothesis | about 9 h GPU | pressure tensor: spec 0.1.1 and `ucmd-analyze viscosity` exist (E2.9); engine branch `e29-pressure-tensor` |
| S5 | Decision point: M1 + LigParGen EMC good enough, or M2 | — | author |
| S6 | M3: 1 M EC:EMC with ζ_ECC, 3 × 30 ns; κ as a prediction | about 40 h GPU | S1, S5 |
| S7 | Only if S6 fails at high c: M4 | — | design doc and ADR |

## 7. What would be new, if it holds

- **κ(c,T) predicted, not fitted:** ζ from the refractive index, every solvent parameter from
  layer 0–1 data, transport only as a test. Lehnert fits ζ to κ.
- **A testable explanation for the literature dispute on the Li⁺ shell** (cyclic-only vs mixed
  shells): the carbonyl charge model alone moves EC from depleted to enriched (M0 vs M1 vs
  Lehnert). If A4 and S2 confirm this, part of the dispute is a property of the force fields.
  This is a hypothesis until S2.
- **An open, reproducible chain:** open engine, open parameters with citations, scripted
  studies. The benchmark model is commercial.

## 8. Decisions and refinements (author, 2026-11-20)

### M1 approved as a test set

- EC density and ΔH_vap with the OPLS-AA types run as rung EC of E2.9
  (`studies/2026-11-20_ec-opls-test`, GPU queue 3).
- The Li⁺ preference with M1 runs as `studies/2026-11-20_li-preference-m1` (GPU queue 4). M0 is
  the 1:1 run of A4, with the same protocol.
- **A4, preliminary (M0, one Li⁺, first 2 ns of the 1:1 run):** without salt crowding, EC holds
  21 % of the carbonyl O in the first shell (0.92 EC, 3.52 EMC), against 50 % of the molecules.
  In pure EC the same Li⁺ binds 4.9 EC carbonyl O. So EC can bind; it loses against EMC. The
  depletion is a property of the M0 parameters, not of crowding.

- **M1 result (2026-11-21, one Li⁺, last 4 ns):** EC holds 31 ± 7 % of the first-shell
  carbonyl O (M0 19 ± 4 %; SEM over 4 × 1 ns blocks, correlated, so larger in truth), 39 % within
  Lehnert's 0.516 nm (M0 29 %, Lehnert ≈ 47 %). EC residence 42 ps (M0 24 ps). The direction
  matches layer 0; the size does not reach the 50 % share. Details:
  `studies/2026-11-20_li-preference-m1/README.md`.
- **EC density (rung EC, 39 °C, 1000 EC):** OPLS-AA 1.3193 g/cm³, LigParGen 1.2800
  (`studies/2026-11-20_ec-opls-test/INDEX.md`; the experimental comparison belongs to that study).

### Layer 0, first result (2026-11-20): gas-phase Li⁺ binding against G4

- Tool and table: [tools/ffcheck/README.md](../../tools/ffcheck/README.md). The reference is
  Olguin, Borodin et al., Phys. Chem. Chem. Phys. 18, 164 (2016), Table 1 (G4, MP2, DFT).
- **QM:** Li⁺ binds EC 6.2 kcal/mol more strongly than DMC (G4; 5.5–7.2 across 11 methods).
- **M0:** no difference (+0.1 kcal/mol). **M1:** −2.0 kcal/mol, the right sign but a third of
  the size.
- Both under-bind Li⁺ by 12–18 kcal/mol, the induction a fixed-charge model lacks.
- **Consequence:** the carbonyl charges (M1) are part of the answer, not all of it. If the M1
  liquid run still depletes EC, step 3 of M3 becomes the next lever: a pair-specific Li⁺–O(carbonyl)
  term fitted to these QM differences. That needs per-pair overrides in the spec (ADR 0008).
  Drude (M4) remains the fallback.
- The gas-phase difference overstates the condensed-phase preference (Olguin's implicit-solvent
  and BOMD results). The test checks the potential, not the shell.

### M3 approved as a trial, with the author's caution about refractive indices

The author's point: n is a bulk, optical-frequency property. Treating it as a constant works
until it does not, and then the result deviates from experiment. The two ECC papers locate
where that happens:
- **What ECC assumes** (Leontyev & Stuchebrukhov, Phys. Chem. Chem. Phys. 13, 2613 (2011)):
  - the electronic response is a uniform continuum with ε_el = n² (high-frequency limit);
  - organic materials have ε_el ≈ 1.7–2.2, and ζ = 1/√ε_el;
  - the unscaled standard practice only works when ε₀/ε_el ≫ 1. It fails in low-dielectric
    media (ε₀/ε_el ≈ 1). Linear carbonates have a low static ε, so EMC-rich electrolytes are
    exactly where the choice matters (ε₀ of EMC to be sourced).
- **Where it must fail** (Kirby & Jungwirth, J. Phys. Chem. Lett. 10, 7531 (2019)):
  - wherever the high-frequency dielectric constant is non-uniform, in proportion to the
    omitted bound charge;
  - ε_el itself varies little between materials, because it depends on atomic density and
    orbital size.

**Consequence for us:**
- The bulk n_D is the robust part. Its dependence on salt concentration must still be checked
  against data.
- The fragile part is the continuum at the scale of the first Li⁺ shell. A Li⁺ 0.2 nm from a
  carbonyl O induces a local dipole that no uniform ε_el represents, and that is where the
  EC/EMC preference is decided.

**Approximations, in order:** each step either passes or names the next one.

1. **ζ_ECC from n_D of the solvent mixture** (bulk mean field).
2. **Sensitivity:** κ at ζ_ECC ± 0.03. If κ moves much more than the n_D uncertainty would
   explain, ζ is not a robust prediction, and we say so.
3. **First-shell correction from quantum chemistry on clusters:** Li⁺–EC and Li⁺–EMC binding
   curves, and mixed Li⁺(S)₄.
   - These clusters are small enough for accurate methods. So we do use first principles, but
     only where the continuum fails; the mean field covers everything else.
   - Implemented as ECC-R (a rescaled Li⁺ σ). If one σ cannot match both carbonyls, a
     pair-specific Li⁺–O term follows, which needs per-pair overrides in the spec.
4. **Drude (M4)** only if step 3 cannot reproduce both binding curves with one parameter set.
   That would show that the missing physics is many-body polarization.

**Pass criteria, fixed before the runs** (a proposal, to be confirmed by the author before S6):
- κ(1 M, 20 °C) within ±15 % of 0.84 S/m without any refit;
- the κ(c) maximum within ±0.2 M of Landesfeind's.
- If either fails, C1 (ζ fitted to κ) becomes the fallback, and the failure is reported as a
  result.

### Quantum chemistry: method (delegated to Claude; an ADR when B2 starts)

- **Program:** Psi4, open source, in a Docker container like the OpenMM image. Nothing is
  installed on the host.
- **Solvent charges (M2):** RESP2 (Schauperl et al., Commun. Chem. 3, 44 (2020); citation to be
  checked against the paper).
  - Charges are a mix of gas-phase and implicit-solvent RESP charges, controlled by one
    parameter δ.
  - Why: one physically interpretable parameter for the polarization level, set by layer-1
    data (ε, ΔH_vap); the same method for all solvents; minutes per conformer.
  - Plain RESP at HF/6-31G* is the cheaper standard, but its polarization level is fixed by
    accident of the basis set, not by data.
- **Ion–solvent references (layer 0, ECC-R):**
  - counterpoise-corrected DFT with dispersion for all clusters;
  - CCSD(T) spot checks on the Li⁺–solvent dimers (about 12 atoms; feasible on 16 cores).
- **Cost:** about one CPU day in total. No GPU.
