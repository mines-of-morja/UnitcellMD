# Corrections to the summary of 26 November (preparation for V-6)

- **Purpose:** every point of Jo's feedback, sections 1–5, against the text of `summary_261126`. For each point: what
  the summary says, what Jo says, what our own data say, and what the successor will say. Prepared by unitcellmd-40 on
  2026-11-28, at the request of unitcellmd-b4. V-6 itself (the successor) is not claimed here.
- **Inputs:**
  - Jo's feedback `Feedback_UnitcellMD_Summary_2026-11-26.md` (workspace root). It is not in git, because its
    section 6 holds the group's data. Section 6 is not reproduced here.
  - The old text is quoted from the built `summary_261126/out1/summary.html` (commit 74a65e0bd7a1).
- **Numbers:** from `check.py` → `check.json`, which reads the same sources as `summary_261126/build.py`, plus:
  - the box volumes from the thermo tables;
  - SC-1's configurational temperatures (`timestep/tconf/summary.json`).

  ```sh
  ucmd-analysis/.venv/bin/python docs/research/summary_261126-corrections/check.py
  ```

- **The viscosities are a range, not a model value.** η = 10, 7, 5 and 3.5 mPa s is Jo's range. The model's η is
  unknown until V-1 or V-2 reports.
- **State column:**
  - **now**: can be corrected from existing data;
  - **V-n**: waits for that task;
  - **keep**: stays, with the reason given.

## What Jo's assumptions turn into with our data

- **Box edge.** Jo assumed 4.28 nm. Measured:
  - the M1 boxes of T2 and of the scan baselines: 4.282–4.283 nm;
  - the pilot (M0, NVT): 4.292 nm;
  - the probe epsEMC x0.85: 4.311 nm.

  Jo's finite-size arithmetic therefore stands as printed.
- **The "+3.4 K" is the 1 fs value**, as Jo assumed. SC-1 gives the configurational minus kinetic temperature:
  - 1 M box: +3.67 ± 0.48 K at 1 fs and +1.74 ± 0.88 K at 0.5 fs. The Δt² prediction for 0.5 fs is +0.92 K.
  - The change from 1 fs to 0.5 fs is 1.93 ± 1.01 K, not the 2.55 K that Jo derived from Δt² scaling.
  - Each run's own jackknife error is about 1.4 K.

## Points

| # | Jo | Summary says (verbatim) | Jo's point | Our check | State | Planned answer in the successor |
|---|---|---|---|---|---|---|
| 1 | §1 | Bias table: "finite box (no Yeh–Hummer correction) \| needs the electrolyte's viscosity, not measured \| D too low; collective κ unaffected" | Give the size. For κ_NE the correction points up and is the largest bias | ΔD = 1.42 / 2.03 / 2.84 / 4.06 ·10⁻¹¹ m²/s at η = 10 / 7 / 5 / 3.5 mPa s (L = 4.282 nm). κ_NE of T2 M1, 0.50 ± 0.03 S/m, becomes 0.60 / 0.65 / 0.71 / 0.80 S/m, i.e. 72 / 77 / 85 / 96 % of 0.84 S/m. Scan baselines: 0.54 → 0.65 / 0.70 / 0.76 / 0.85 S/m. Reproduces Jo's table | now (size); V-1, V-2 (final value) | Row with the size over the η range and the direction "κ_NE up by 20–60 %". Then the value at the model's η from V-1, checked against V-2's D(1/L) |
| 2 | §1 | Summary: "The known biases point the same way. … Both make the simulated ions faster, so correcting them widens the κ gap." | True for the Onsager κ, false for κ_NE: the box correction raises κ_NE more than the time step lowers it | The time step at 0.5 fs lowers D by 8–13 % (SC-1). The box correction raises κ_NE by 21–62 % (row 1). The net effect on κ_NE is up for any η ≤ 10 mPa s. Jo's 0.35–0.37 S/m for the Onsager κ at Δt → 0 is not recomputed here | now | Split the statement. Onsager κ: the corrections widen the gap. κ_NE: they narrow it, by an amount that depends on η |
| 3 | §1 | "The gap is in the mobilities, not in the correlations. … the pilot's κ/κ<sub>NE</sub> is 0.90 ± 0.19." | The ratio is biased high in a finite box. Corrected it is about 0.5–0.7. Splitting the gap also needs measured D | Pilot, from `transport.repaired.json`: κ/κ_NE = 0.88 uncorrected. The printed 0.90 is quoted from `report/report.md` (at 9eda5bd); the 0.02 difference is not explained yet, and V-6 should take one source. Corrected: 0.72 ± 0.15 / 0.67 ± 0.14 / 0.61 ± 0.12 / 0.54 ± 0.11 at η = 10 / 7 / 5 / 3.5 mPa s. This assumes the collective κ does not depend on box size, which is Jo's premise; V-2 tests it | V-1, V-2; measured D from V-5 | Withdraw the claim until η is known. Then give the corrected ratio. Split mobility from correlation only with a measured D (pfg-NMR, refs. 29 and 35 of [1], V-5) |
| 4 | §1 | "One probe of the parameter scan, epsEMC x0.85, reaches κ<sub>NE</sub> = 0.96 S/m (114 %, inside the band)" | Corrected, it lies above the band: at least 1.07 S/m for η ≤ 10 mPa s | L = 4.311 nm. κ_NE becomes 1.07 S/m (127 %) at η = 10 mPa s and more for lower η. Confirmed | now | "Above the band once corrected for box size". Still a map, not a model |
| 5 | §1 | (Fig. 2 and table: only the pilot has an Onsager κ) | The robust number is M0's Onsager κ, 0.42 ± 0.09 S/m from one 20 ns run. M1 has no collective κ | Fact | V-2 (κ per box size, agent-finite-size) | Say so. Add M1's collective κ when V-2 reports |
| 6 | §1 | Self-diffusion note: "Not corrected for box size." | Same correction for every species | ΔD as in row 1, the same for all four species | V-1, V-2 | D table with a D∞ column at the model's η |
| 7 | §2 | Bias table rows 1 and 2: "1 fs step with flexible bonds (SC-1)" and "liquid warmer than displayed \| +3.4 ± 0.5 K" | These are one bias. The offset explains the density shift completely and most of the D shift | **1 M density:** ΔT = 1.93 ± 1.01 K, with the model's dρ/dT = −1.081·10⁻³ g cm⁻³ K⁻¹, predicts +0.17 ± 0.09 %; measured +0.23 ± 0.04 %. Consistent. **Pure EMC:** ΔT = 5.47 ± 1.69 K predicts +0.59 ± 0.18 %; measured +0.31 ± 0.03 %. Overpredicts by about 1.5σ. **D (1 M):** predicted −4.2 % (E_a = 16 kJ/mol) to −6.5 % (25 kJ/mol); measured −11 (Li⁺), −13 (PF₆⁻), −8 (EC), −9 % (EMC). The temperature explains about half of the D shift, not most | V-3 (agent-consistency) | "One effect" is plausible for the density and not shown for D. Keep two rows, or one row with two parts, until V-3 separates the integrator from the coupling. The 0.5 fs residual (+1.74 ± 0.88 K against +0.92 K) stays an open line |
| 8 | §2 | (0.5 fs runs treated as unbiased) | The 0.5 fs runs still carry about +0.85 K: +0.08 % in density, 2–3 % in D | The measured residual is +1.74 ± 0.88 K, so about twice Jo's estimate, within 1σ | V-3 | Give the 0.5 fs residual with its error in the bias table |
| 9 | §3a | "The straight line through the model's points meets c = 0 +3.2 % above the fit of [1]" | No salt-free run. V_φ depends steeply on ρ₀. Ideal mixing predicts +2.1 to +2.4 % | Not recomputed here | V-4 (agent-finite-size) | Measured ρ₀ of the M1 solvent; V_φ table recomputed with it |
| 10 | §3b | Fig. 3 and section 6: deviations against the linear fit of [1] at 0.1 and 3 M | The fit is a straight line. The SI's measured points are the better reference at the ends | Can be done without new runs: the SI is in `../Lit`, and the second reading is in `landesfeind-density/` | now (V-6) | Compare 0.1 and 3 M against the SI's measured points; give both deviations |
| 11 | §3c | "Lehnert's published boxes imply the same … so the slope belongs to the ions" and the second explanation of the 3 M κ excess | The implied density is the model's density only if the boxes were matched to an equilibrated volume | **The SI says they were.** Lehnert SI S1.2 (VoR, `../Lit`, read 2026-11-28): "In order to find the right number of ions for our target concentrations, we conduct multiple MD simulations at 20 °C with varying ion numbers. Table S1 shows the most consistent particle numbers with the desired concentrations." S1.1: 3 ns NPT at 1 atm (Nosé–Hoover, 1000 fs damping), then cooling to the target temperature. So the implied density is their model's own, up to the integer ion step: ρ_implied/ρ_true = c_target/c_true. If "most consistent" means the nearest count, that is at most 1/(2N): ±5.6 % at 0.1 M, ±1.1 % at 1 M, ±0.30 % at 3 M; one full pair, 0.60 % at 3 M, if it does not. The 3 M point is −2.0 %, between 3.3 and 6.6 such bounds below the fit. Slope weighted by these bounds: 0.072 ± 0.004 g cm⁻³ M⁻¹, against 0.0912. The unweighted 0.0757 printed in the summary leans on the coarse low-c boxes. **An NPT run of their 3 M composition with our force field would not test their model:** their solvent parameters come from Maestro (Schrödinger, not open; `docs/lehnert2025-si-notes.md`), and our model's own 3 M density is already known (SC-4, −2.0 %) | now; no GPU run planned (item (a) closed by the SI). A request for the box volumes stays optional and goes through the author (summary PDF to the contact first) | Drop "if each box sits exactly at its target concentration" as an assumption. Cite S1.2 and give the integer-step bound per point; use the weighted slope with its error. "The slope belongs to the ions" then rests on the 2–3 M points, where the bound is ≤ 0.5 % |
| 12 | §4 | "Transference number: no test yet … A 10 % error needs about 300 ns." | The reference itself is soft: R² = 0.82; EC:EMC has the most scatter. No pass band tighter than ±0.1 | Agrees with publication.md (the t₊ dispute) | keep | State a band of no less than ±0.1 for t₊. Spend no 300 ns on t₊ before the collective κ and the box-size series |
| 13 | §5 | "Reaching the measured V<sub>φ</sub> would need ζ ≈ 0.98 at 1 M but 1.12 at 3 M" next to "V<sub>φ</sub> … 70.6 (1 M)" | 0.75 + (70.6 − 55.7)/74 = 0.95, not 0.98 | build.py takes V_φ = 72.41 cm³/mol from the 1 M ζ = 0.75 run of the 3 M map (1 fs, ρ = 1.1949, c = 0.994 M), so ζ* = 0.977. With SC-4's printed 70.64 (0.5 fs) it is 0.953. Jo is right that the two numbers do not belong together. Jo's 73.1 assumes c = 1.000 M | now | Give ζ* with the V_φ it uses and the time step: about 0.95 at 0.5 fs (SC-4), 0.98 at 1 fs (map). The 3 M value comes from the map at 1 fs |
| 14 | §5 | Fig. 3 caption: "Both models cross the fit near 1–1.5 M" | M1 crosses at about 1.75 M, Lehnert's boxes at about 1.5 M | Linear between neighbours: M1 (SC-4) at 1.79 M; Lehnert's implied densities at 1.55 M | now | "M1 crosses the fit near 1.8 M, Lehnert's boxes near 1.5 M" |
| 15 | §5 | "Water (engine check): 1.0072 ± 0.0002 g/cm³ against 1.012 for the same model [4] (−0.47 %), unexplained." | About 100 bar. A pressure offset could act in the electrolyte too. The LJ tail convention alone could do it (−280 bar at 0.9 nm) | Already worked out on 25 November (`water-pressure/README.md`), but not carried into the summary. At 1.012 g/cm³ the molecular pressure is 122.6 ± 11.9 bar: the warm liquid accounts for 72 ± 2 bar, and 49 ± 12 bar remain. Our LJ tail at 0.9 nm is −285 bar. The README infers (Wu does not say) that Wu's 1.012 is the atomic pressure, which is −4 ± 12 bar at 1.012 on the GPU. Electrolyte: the warm-liquid part acts there too (row 7). Whether a pressure-definition part acts depends on the barostat's virial | now (text); V-3 (electrolyte part) | Replace "unexplained" with the budget and its open remainder. Name the tail and pressure conventions next to Wu's. State the electrolyte's share after V-3 |
| 16 | §7 | (order of checks) | (1) η; (2) T at 0.5 fs or X–H constraints; (3) salt-free; (4) Lehnert's volumes; (5) collective κ for M1 and measured D | Matches V-1/V-2, V-3, V-4, item (a), V-2 and V-5 (`priorities-2026-11-28.md`) | — | Thank Jo; list which task answers which point |

## Not a correction, but for the successor

- **Jo's section 6.** The group's data (Gruber 2026, SI CSV in `../Lit`) go in through V-5's ledger entries, as a
  comparison band for ρ(c), V_φ(c) and η. Its solvent is EC:DMC:EMC with VC, not EC:EMC 3:7.
- **The correction can close most of the κ_NE gap.** If the model's η were near the measured 3–3.5 mPa s, the
  corrected κ_NE of M1 would be 85–100 % of experiment. The ions look slow, and SC-7 finds EMC over-cohesive, so a
  more viscous model is more likely. That η is what V-1 and V-2 decide; the successor must not anticipate it.
