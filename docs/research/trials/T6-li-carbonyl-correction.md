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

**Amendment 4 (2026-11-23, 11:32Z, cluster optimizations restarted, no cluster result yet):**
optimizer coordinates.
- **What was found:** the first cluster, Li⁺(EMC)₄ (61 atoms), started at 23:48Z with optking's
  default coordinates, redundant internals.
  - Steps 1 and 2 went through.
  - From step 3 on, every step failed with "Back transformation failed. Cartesian step size too
    large". Optking then erased its history and recomputed the gradient at the same geometry.
  - After 207 energies, 11.7 h, the geometry had not moved since step 3. The run was stopped at
    11:31Z, with no cluster finished.
- **Change:** the five clusters are optimized with `opt_coordinates = both` (redundant internals
  plus Cartesians, `cluster_dft.py --opt-coordinates both`), from the same start files. The
  solvents alone use the same setting in that run.
  - **Unchanged:** functional, basis, grid, convergence criteria and the start geometries. Only
    the route changes. A different route can end in a different local minimum of these floppy
    clusters; this is not tested.
  - **Single-solvent complexes:** those runs converged with redundant internals and are not
    rerun.
- **Disclosed, already seen:** the Li⁺(EMC)₄ energies at steps 1–3 of the failed run (−1537.5899,
  −1537.6168, −1537.6103 hartree), and parts of its Cartesian geometries and gradients, printed
  while the failure was diagnosed. No converged geometry, Li–O distance or binding energy of any
  cluster had been read. The failed output is kept in the work directory.
- **Cost:** the stage 1 estimate of about one CPU day was low.
  - A Li⁺(EMC)₄ optimization step takes about 6–8 min at def2-SVP on 16 threads.
  - A def2-TZVPD energy of the EC complex (284 basis functions) took 80 s. Li⁺(EMC)₄ has about
    1 300, so roughly 2 h per energy, and each cluster needs six energies in the full basis.
- **Second change (12:12Z), cost only:** the ωB97X-D run now does only the optimizations
  (`--geometry-only`), and the def2-TZVPD energies are computed once, at ωB97M-V.
  - Under Amendment 3 the fit uses only the ωB97M-V energies. ωB97X-D cluster energies would
    have been computed and never used, at about two days of CPU.
  - Nothing that enters stage 2 changes.
  - The restart is at 12:12Z, and the optimization steps of the 11:32Z run (energies of steps 1–5
    seen, −1537.5899 to −1537.6173 hartree) are discarded.
- **Corrected 2026-11-24, 08:50Z, before any cluster geometry or Li–O distance was read:** this
  amendment as committed (b742cf7, 75fa8d4) gave the stop as 11:29Z and the second change as
  12:20Z, where run.log has 11:31Z and 12:12Z; it said no geometry had been read; it left out the
  step energies of the 11:32Z run; and it stated as fact that the same minimum is reached and
  that the old run would have ended with an error. Seen since: ωB97X-D/def2-SVP optimization
  energies of the first three clusters, and of the solvents alone for the first two.

**Run record (2026-11-24, 09:00Z), no change of the plan:**
- **Hold:** the author agreed to let the ωB97X-D geometries finish and to hold the ωB97M-V single
  points until the sensitivity scan (`studies/2026-11-24_parameter-sensitivity-1M`) is read.
- **Interruption:** the way the hold was applied ended the running container (SIGTERM, 08:59:57Z).
  Li⁺(EC)₂(EMC)₂ was lost at about step 69; n = 0 and 1 were finished and are kept. n = 2, 3 and 4
  run since 09:00:26Z in a detached container, n = 2 again from its original start file.
- **Amendment 5** (less counterpoise; the energy weight per exchanged solvent) was open here; it is
  below. No cluster energy or converged geometry had been read at this record.

**Amendment 5 (2026-11-24, 21:45Z, no ωB97M-V cluster energy computed; author: "both look okay"):**
less counterpoise, and the energy weight of the fit.
- **Counterpoise only for n = 0 and 4** (`cluster_dft.py --no-cp` for n = 1–3).
  - ΔE_n is computed without counterpoise for all n.
  - **Why:** counterpoise takes 5 of the 6 full-basis energies of a cluster. On the four
    single-solvent complexes it changes E_bind by 0.05–0.06 kcal/mol (ωB97M-V/def2-TZVPD), and
    EC − EMC by 0.003. Contacts between solvents in a cluster can add more; the complexes do not
    test that.
  - **Check:** the counterpoise shift of ΔE_4, per exchanged solvent. If it is larger than
    0.5 s_x (0.48 kcal/mol), n = 1–3 get counterpoise energies too and ΔE_n is computed with it, as
    in the original plan. `t6_fit.py` refuses to fit otherwise.
- **Energy weight:** s_E = 3.95 kcal/mol is replaced by n s_x for ΔE_n, with s_x per exchanged
  solvent.
  - **Why:** s_E is the error of *absolute* binding energies. ΔE_n is a difference between EC and
    EMC, in which the nearly uniform over-binding of the functional cancels. With s_d = 0.0156 Å,
    s_E gives the energies almost no weight, and they are what option B is for.
  - **s_x** is the RMS of the functional's two EC − EMC errors against MP2 (0.43 in E_bind, 1.29 in
    the CP interaction energy): **0.96 kcal/mol**, floor 0.3. It was chosen knowing these errors. It
    rests on one solvent pair.
  - **Factor n:** an error per exchange repeats with every exchange, so it grows with n.
  - MP2 itself differs from G4 by 0.7 kcal/mol in EC − DMC (−6.89 here, −6.2 in Olguin 2016), so
    s_x is not smaller than the reference's own uncertainty.
- **Unchanged:** s_d, option A (distances only), the weighted-RMS ≤ 1 statement, stage 3 and its
  decision rule. **The hold on the single points stays:** they run only after the sensitivity
  scan is read and the author decides.
- **Cost:** about one CPU day instead of two for the single points (estimate).
- **Disclosed, already seen when this was written:** by other sessions, the ωB97X-D/def2-SVP
  optimization energies listed in the correction to Amendment 4, from which a rough ΔE_n could be
  formed. The session that proposed and wrote this amendment had read none of those, and no
  cluster geometry or Li–O distance. It saw force-field values of M1 at the start geometries,
  while testing the script on synthetic energies.
- **Tested:** `T6/test_t6_fit.py` and `tools/qm/test_cluster_dft.py` (9 tests, Psi4 stubbed), and
  `t6_fit.py` end to end on synthetic energies. `--no-cp` has not run in Psi4 yet: memory was
  short next to the geometry run. Its first run must reproduce E_bind of the EC complex, −50.755
  kcal/mol.
- **Before the single points:** copy the new `cluster_dft.py` to the work directory, after the
  geometry run has ended (the queue script `run_clusters.sh` there knows neither `--no-cp` nor the
  hold). Two calls write to the same `--out`: n = 0 and 4 with counterpoise, n = 1–3 with
  `--no-cp`.

## Results

### Stage 1a — functional (2026-11-22, 23:48Z)

Applied by `T6/t6_functional.py` (committed before the M06-2X and ωB97M-V results were read).
Output in `T6/t6_functional_choice.json`; DFT rows in `tools/qm/results/t6_dimers_*.json`.

| Functional | Largest error (kcal/mol) | EC − EMC (MP2 −6.24) | Condition (≤ 1) | Li–O vs MP2 (Å) |
|---|---|---|---|---|
| ωB97X-D | **2.38** (EMC, E_int_CP) | −5.19 (off by 1.046) | **missed by 0.046** | −0.012 … −0.016 |
| ωB97M-V//ωB97X-D | 3.95 (EMC, E_int_CP) | −5.81 (off by 0.43) | met | ωB97X-D's |
| M06-2X | 4.43 (EMC, E_int_CP) | −5.70 (off by 0.54) | met | −0.035 … −0.037, all four flagged |

**How the result reads:**
- **Chosen: ωB97M-V//ωB97X-D.** It is the best-ranked functional among those that meet the
  condition.
- ωB97X-D ranks first on the largest error, but misses the EC − EMC condition by 0.046 kcal/mol.
- **The rule's reading:** the condition decides which functionals can be chosen, and the ranking
  picks among them. This is how the selection script implements Amendment 1 together with the
  plan's "if none reproduces …". That reading was fixed before the results; it is stated here
  because the best-ranked functional is not the one chosen.
- **Pattern:** all three bind more strongly than MP2 (every error is negative). ωB97M-V and
  M06-2X do so by 2–4.4 kcal/mol, nearly uniformly across the four solvents. That shift largely
  cancels in the EC − EMC difference, which is the quantity the exchange energies of stage 2
  measure.
- **Geometry check:** for EC, ωB97M-V with its own geometry (the stopped run, Amendment 3) gives
  E_bind −50.36 kcal/mol. On the ωB97X-D geometry it gives −50.76, so the composite costs
  0.4 kcal/mol here.

**Fit uncertainties (Amendment 2), from the chosen protocol:**
- s_E = 3.95 kcal/mol (above the 0.3 floor);
- s_d = 0.0156 Å, which is ωB97X-D's largest Li–O error, since the geometries are ωB97X-D's.

With s_E this large, option B's energy residuals carry little weight against the distances. That
follows from the rule and is reported, not changed.
**Superseded by Amendment 5** (2026-11-24): the energies get n s_x, s_x = 0.96 kcal/mol. s_d stays.

**Next:** the five clusters, run since 23:48Z. First ωB97X-D/def2-SVP optimizations, then
ωB97M-V/def2-TZVPD single points with counterpoise (`run_clusters.sh wb97m-v wb97x-d` in the
work directory).
