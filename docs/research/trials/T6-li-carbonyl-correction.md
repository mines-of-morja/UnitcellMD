# T6 — First-shell correction: one Li⁺ σ (ECC-R) or a pair-specific Li⁺–O(carbonyl) term

Strategy M3, step 3 (`docs/research/forcefield-strategy.md` §8), after T2 (ADR 0014).

## Why it is contested

- **The gap:**
  - with M1, Li⁺ has 0.97 ± 0.01 EC in its first shell at 1 M, against about 2.2 from
    dielectric spectroscopy (an upper bound);
  - in the gas phase, M1 gives EC 1.24 kcal/mol more binding than EMC, against 6.24 in QM;
  - both force fields put Li⁺ 1.94–2.04 Å from the carbonyl O of a single solvent, QM 1.75–1.76 Å.
- **For one Li⁺ σ (option A, ECC-R):**
  - one parameter;
  - the published form for scaled-charge ions (Kirby & Jungwirth 2019; citation to be checked);
  - no spec change.
  - The strategy takes it first.
- **For a pair term (option B):**
  - the difference between EC and EMC is an energy difference between two carbonyl O, and a
    single Li⁺ σ acts on both nearly alike;
  - a pair term can treat them apart.
  - It costs four parameters and a spec extension (per-pair LJ overrides, ADR 0008 §3), which
    needs the author's approval before any liquid run.
- **Why the single-solvent QM numbers are not the targets:** the 1.76 Å belongs to Li⁺ with one
  solvent molecule. In the liquid, Li⁺ carries about four carbonyl O, which compete. Clusters
  Li⁺(S)₄ are therefore the reference; the single-solvent complexes are kept as a check.

## Plan (fixed 2026-11-22, before any calculation of this trial)

### Stage 1 — QM reference (fit side, layer 0)

- **Clusters:** Li⁺(EC)ₙ(EMC)₄₋ₙ, n = 0…4, in the gas phase.
  - Start: the lowest of 10 force-field minima (M1, q_Li = 1) from random placements of the four
    carbonyl O around Li⁺.
  - EMC in the conformer the force field finds.
- **Level:** DFT with dispersion, as the strategy decided (QM method, delegated).
  - Geometry optimization with def2-SVP, energies at def2-TZVPD with counterpoise.
  - Before the clusters, the whole protocol runs on the four single-solvent complexes (EC, EMC, PC,
    DMC) for three functionals: ωB97X-D, ωB97M-V, M06-2X. All three run in the image without
    extra programs; B3LYP-D3(BJ) would need s-dftd3, which the image does not have (checked
    2026-11-22).
  - The functional with the smallest largest error against our MP2/aug-cc-pVTZ values (E_bind
    and Li–O, `tools/qm/results/li_binding_mp2_aug-cc-pvtz.json`) is used for the clusters.
  - If none reproduces the EC − EMC difference within 1 kcal/mol, the clusters are not run, and
    this goes to the author.
- **Targets:**
  - the mean Li–O(carbonyl) distance per cluster and per solvent;
  - the exchange energies ΔE_n = E(n) − E(0) − n [E(EC) − E(EMC)] for n = 1…4: the energy of
    replacing EMC by EC in the shell, with the solvents optimized alone.

### Stage 2 — both options fitted to stage 1 (force field, gas phase, q_Li = 0.75)

- **A:** σ_Li fitted to the cluster Li–O distances (least squares over all clusters). The
  exchange energies are its test.
- **B:** σ and ε of the pairs Li–O(EC carbonyl) and Li–O(EMC carbonyl) fitted to the distances
  and the exchange energies together. That is four parameters against about 14 targets. All
  other pairs keep the combination rule.
- **Charges:** the production charges (ζ = 0.75 on Li⁺, solvents unscaled). When T5 sets ζ from
  n_D, both fits are repeated at that ζ.
- **Reported:** fit residuals, the single-solvent complexes (check), Li–F distances (Li–PF₆⁻ in
  the gas phase).

### Stage 3 — liquid test (T2 box and protocol)

- **Runs:** 3 packing seeds per option (20261124–26).
- **Length:** 3 ns from packing, the last 1.5 ns analysed. This is the length T2 measured for
  this kind of run (trials rule 6).
- **Option B** runs only after the author has approved the spec extension. It is approved and
  implemented: ADR 0015, `docs/design/S0.1.2-pair-lj-overrides.md`. Its liquid runs use the
  engine and bridge of branch `s012-pair-overrides`. Option A can run as soon as stage 2 has
  its σ.
- **Metric:** EC carbonyl O within 0.28 nm of Li⁺ (as in T2). Reference: M1, 0.973 ± 0.010
  (T2); bound 2.2 ± 0.1.

**Decision rule:**

1. A candidate **passes** if its count exceeds M1's by more than 2 combined SE **and** does not
   exceed 2.2 by more than 2 combined SE (the SE of the runs combined with the bound's ±0.1).
2. If both pass, the one closer to 2.2 wins if the difference between them is resolved
   (> 2 combined SE). If it is not, A wins: one parameter and no spec change.
3. If one passes, it is the correction.
4. **If a candidate exceeds the bound,** the gas-phase clusters overstate the preference in the
   liquid, as Olguin et al. 2016 found with implicit solvent. That is reported. Nothing is refit
   to the liquid shell: that would be fitting to the answer (strategy §5).
5. If neither passes, step 4 of M3 follows: Drude (M4).
6. Not used for the decision, reported: density against the Landesfeind fit (one reading), PF₆⁻
   within 0.516 nm, the first peak of g(Li–O), D and κ_NE.

**Run-length diagnostic (T2 lesson):** the count in 250 ps windows. The tolerance is set from
the window noise: two standard deviations of the windows after 1.5 ns. It reports the time
after which every window stays within that band.

## Cost

- **Stage 1:** about 12 DFT optimizations of the single complexes (minutes each), then 5 cluster
  optimizations (41–61 atoms) and their counterpoise energies, about one CPU day (Psi4 in
  Docker, `tools/qm`).
- **Stage 2:** minutes.
- **Stage 3:** about 40 min per run on the MI50, so 2 h per option.

**Amendment 1 (2026-11-22, 09:26Z, before any calculation of this trial):** how the
functional is chosen.
- The DFT single-solvent values are compared with MP2 in two ways:
  - E_bind without counterpoise, against MP2's E_bind;
  - the counterpoise interaction energy at the complex geometry, against MP2's.
- **Selection:** the functional with the smallest largest absolute error over these 8 numbers
  (4 complexes) is chosen.
- **Condition:** its EC − EMC difference must also lie within 1 kcal/mol of MP2's (−6.24).
- Li–O distances (def2-SVP geometries) are reported. Any that is more than 0.03 Å from MP2 is
  flagged.
- Integration grid (99, 590) for all three functionals, so M06-2X is not grid-limited.

**Amendment 2 (2026-11-22, 09:33Z, stage 1 running, no DFT result read yet):** how stage 2
fits.
- **Weights:** each residual is divided by the uncertainty of its reference, the chosen
  functional's largest error against MP2 on the single complexes: s_d for Li–O distances and
  s_E for energies. Floors are 0.01 Å and 0.3 kcal/mol, so that a lucky agreement does not
  dominate.
- **Option A** minimizes Σ (Δd/s_d)² over all cluster Li–O(carbonyl) distances. Option B
  minimizes that sum plus Σ (ΔE_n/s_E)² over n = 1…4.
- **The force-field values** come from minimizing each cluster from its DFT geometry, and each
  free solvent from its DFT minimum. The same Reference-platform minimizer as the starts is used,
  with PF₆⁻ absent and q_Li = 0.75.
- **The fit is good** if the weighted RMS residual is ≤ 1, i.e. within the reference
  uncertainty. That is reported. It is not a gate: stage 3 decides.

**Amendment 3 (2026-11-22, 22:31Z, functional check part-run): ωB97M-V on ωB97X-D geometries.**
- **What was found:** Psi4 1.9.1 has no analytic gradients for the VV10 functionals (ωB97M-V,
  ωB97X-V). This was tested on water; ωB97X-D and M06-2X have them. The optimizer therefore fell
  back to finite differences: the EC complex alone took 11.8 h (1 176 energy evaluations,
  09:56–21:42Z). The clusters (41–61 atoms) would take weeks, so the protocol as planned cannot
  be run with ωB97M-V. The run was stopped after EC.
- **Change:** ωB97M-V enters as ωB97M-V/def2-TZVPD//ωB97X-D/def2-SVP.
  - Its energies are single points, with counterpoise as before, on the ωB97X-D geometries of the
    complexes and of the solvents alone (`cluster_dft.py --geometries`).
  - Its Li–O distances are therefore those of ωB97X-D.
  - This is the usual composite for functionals without gradients.
  - The selection rule of Amendment 1 is unchanged. It applies to ωB97X-D, M06-2X and
    ωB97M-V//ωB97X-D. If the composite is chosen, the clusters are optimized with ωB97X-D, and
    s_d is ωB97X-D's.
- **Disclosed, already seen when this was written:**
  - ωB97X-D: EC and EMC. E_bind −48.80 and −43.61 kcal/mol; CP interaction −51.25 and −46.51;
    Li–O 1.750 and 1.739 Å.
  - ωB97M-V, full protocol, EC only: E_bind −50.36; CP interaction −53.38; Li–O 1.731 Å. It is
    reported, not used for the selection.
  - No M06-2X result, and no ωB97X-D PC or DMC value, had been read.
