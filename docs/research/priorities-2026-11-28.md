# Priorities after Jo's feedback (2026-11-28)

- **Inputs:**
  - Jo's feedback on the summary of 26 November (`Feedback_UnitcellMD_Summary_2026-11-26.md`, workspace root, not in git);
  - SC-7 step 0 (EMC 30 % over-cohesive);
  - SC-1 and its configurational temperatures;
  - SC-3;
  - the papers added to `../Lit` on 2026-11-27.
- **Tasks:** V-1 to V-6 in [docs/tasks.toml](../tasks.toml). Agents claim them there, one agent per task.

## The one question that blocks the most: the model's viscosity

Four open threads end at the same unknown, η of the model:

1. **Finite-size correction (Jo §1).**
   - Without the viscosity of the model, D and κ_NE cannot be corrected for the 4.3 nm box.
   - The Yeh–Hummer correction raises κ_NE by +30 to +60 % for η = 7 to 3.5 mPa s.
   - So two statements of the summary are open:
     - "the gap is in the mobilities, not the correlations";
     - "every bias points the same way".
2. **T4 (slow ions).** "Solvent too viscous or Li⁺ bound too strongly" is decided by η.
3. **SC-7 step 0.**
   - EMC's ΔH_vap is 53.2 kJ/mol against about 40.7: the solvent is about 30 % too cohesive.
   - A too-cohesive liquid is too dense (+2.8 %, seen) and very likely too viscous (not yet measured).
   - That would explain the slow ions without touching the ions.
4. **References are in hand.**
   - Logan 2018: EC:EMC 3:7 with LiPF₆; 1.0 mol/kg is 3.05 cP at 20 °C (agent reading; ledger entry still to make).
   - Gruber 2026 SI, as a CSV in `../Lit`: η, ρ and κ from −20 to 60 °C and 0.25 to 3 M. Its solvent is EC:DMC:EMC with VC, so it gives a band. At 1 M and 20 °C it is 3.16 mPa s. These are the "measurements from our group" in Jo's §6.

**Two independent routes, run in parallel:**
- **V-1, engine route (Green–Kubo).** The bridge reports the pressure tensor on the GPU. Then η of pure EMC and of the 1 M box follows from Green–Kubo. Step 0 is queued as job ded7 and times the tensor.
- **V-2, no new code (box-size series).** D of the 1 M box at three box sizes, plotted against 1/L. This gives D at infinite size, and from the slope a second estimate of η. It also answers whether the collective κ depends on box size.

## Thermostat, barostat and the "+3.4 K": one integrator effect, to be confirmed once

- **What is measured:**
  - **Temperature (SC-1):** configurational minus kinetic temperature is +3.7 K at 1 fs and +1.7 K at 0.5 fs in the 1 M box. In EMC it is +5.3 K and −0.2 K, in water +6.0 K and +2.4 K (water at 0.25 fs: +0.3 K).
  - **Pressure (SC-3):** the atomic pressure is biased by −129 bar in water at 1 fs, as Δt² predicts.
  - **Density (Jo §2):** the SC-1 density shift follows exactly from the temperature offset and the model's own thermal expansion.
- **Reading:** the integrator, at 1 fs with flexible X–H bonds, accounts for most of it. Thermostat–barostat coupling is not needed to explain the numbers.
- **What is left open:** the 1 M box at 0.5 fs (+1.7 K) is twice what pure Δt² scaling predicts (about +0.9 K).
- **V-3 separates the integrator from the coupling:**
  - an NVE run, with no thermostat and no barostat;
  - and one exploratory run with X–H constraints.
- The summary then gets one bias row instead of two (Jo §2).

## Order

| Priority | Task | Why first | Needs |
|---|---|---|---|
| 1 | **V-1** viscosity by Green–Kubo, GPU pressure tensor | decides T4, the Yeh–Hummer corrections and the reading of SC-7 | design note for the bridge (author), then GPU |
| 1 | **V-2** box-size series of the 1 M box | the same question without new code; independent check of V-1 | study README with criterion, then GPU |
| 1 | **SC-7 answers Q1–Q7** | the EMC refit is the most likely model fix and waits only for the author | author |
| 2 | **V-3** thermodynamic consistency (NVE, constraints, SC-3) | one bias instead of two; tests the thermostat–barostat hypothesis | short GPU and CPU runs |
| 2 | **V-4** salt-free solvent NPT | the intercept, hence V_φ, is extrapolated (Jo §3a) | about 3 short GPU runs |
| 2 | **V-5** literature note on the new papers | what other models' η and D are, measured D and η for the ledger | no compute |
| 3 | **V-6** corrected summary (successor of 26 November) | Jo's corrections, after V-1 to V-4 report | no compute |
| later | ion model (ρ(c) slope), 3 M κ, t₊ | the solvent must be right first (ion-model notes §7); t₊ needs about 300 ns per 10 % | — |

## Rules that stay

- **No parameter is chosen from κ, D, t₊ or η.** η is a test quantity, like κ: the model's η is measured and compared, never fitted.
- **GPU work goes through the queue,** one job at a time. The engine branches build in their own worktrees.
- **A study's question and pass criterion** are in its README before its first run.
